from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView
from .models import Spreadsheet
import pandas as pd
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import zipfile
from django.views.decorators.http import require_http_methods
import markdown
from datetime import datetime
import os
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def generate_markdown_report(row_data, row_number):
    """Generate a markdown report for a single row"""
    try:
        lines = [f"# Report for Row {row_number}\n\n## Data Summary\n"]
        for field, value in row_data.items():
            lines.append(f"- **{field}**: {value}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error generating markdown report: {str(e)}")
        raise

def generate_pdf_from_markdown(markdown_content):
    """Generate a PDF from markdown content and return the PDF data"""
    try:
        # Create a buffer for the PDF
        pdf_buffer = io.BytesIO()
        
        # Convert markdown to HTML with proper extensions
        html_content = markdown.markdown(
            markdown_content,
            extensions=['extra', 'nl2br', 'sane_lists']
        )
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.black
        ))
        
        styles.add(ParagraphStyle(
            name='CustomSubHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.black
        ))
        
        styles.add(ParagraphStyle(
            name='CustomList',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.black
        ))
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Build PDF content
        story = []
        
        # Process each HTML element
        for element in soup.find_all(['h1', 'h2', 'p', 'li', 'strong']):
            if element.name == 'h1':
                text = element.get_text().strip()
                if text:
                    story.append(Paragraph(text, styles['CustomHeader']))
                    story.append(Spacer(1, 20))
            elif element.name == 'h2':
                text = element.get_text().strip()
                if text:
                    story.append(Paragraph(text, styles['CustomSubHeader']))
                    story.append(Spacer(1, 15))
            elif element.name == 'li':
                text = element.get_text().strip()
                if text:
                    story.append(Paragraph(f"• {text}", styles['CustomList']))
                    story.append(Spacer(1, 12))
            elif element.name == 'p':
                text = element.get_text().strip()
                if text:
                    story.append(Paragraph(text, styles['CustomList']))
                    story.append(Spacer(1, 12))
            elif element.name == 'strong':
                text = element.get_text().strip()
                if text:
                    story.append(Paragraph(f"<b>{text}</b>", styles['CustomList']))
                    story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        
        # Get the PDF data
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Error generating PDF from markdown: {str(e)}")
        raise

def upload_spreadsheet(request):
    if request.method == 'POST' and request.FILES.get('spreadsheet'):
        spreadsheet_file = request.FILES['spreadsheet']
        
        # Check file extension
        if not spreadsheet_file.name.endswith('.xlsx'):
            messages.error(request, 'Please upload a valid Excel file (.xlsx)')
            return render(request, 'spreadsheet_processor/upload.html')
            
        try:
            # Read Excel file with openpyxl engine
            df = pd.read_excel(spreadsheet_file, engine='openpyxl')
            if len(df) == 0:
                messages.error(request, 'The spreadsheet is empty.')
                return render(request, 'spreadsheet_processor/upload.html')
            
            # Save the spreadsheet
            spreadsheet = Spreadsheet.objects.create(
                file=spreadsheet_file,
                processed=True
            )
            messages.success(request, 'Spreadsheet uploaded successfully!')
            return redirect('spreadsheet_list')
            
        except Exception as e:
            logger.error(f"Error processing spreadsheet: {str(e)}")
            messages.error(request, f'Error processing spreadsheet: Please ensure the file is a valid Excel spreadsheet.')
            return render(request, 'spreadsheet_processor/upload.html')
    
    return render(request, 'spreadsheet_processor/upload.html')

class SpreadsheetListView(ListView):
    model = Spreadsheet
    template_name = 'spreadsheet_processor/spreadsheet_list.html'
    context_object_name = 'spreadsheets'
    ordering = ['-uploaded_at']

@require_http_methods(["GET", "POST"])
def download_spreadsheet_reports(request, spreadsheet_id):
    """Download all reports for a spreadsheet as a ZIP file"""
    try:
        # Get the spreadsheet
        spreadsheet = Spreadsheet.objects.get(id=spreadsheet_id)
        
        # Read the Excel file with openpyxl engine
        df = pd.read_excel(spreadsheet.file, engine='openpyxl')
        
        # Create a buffer for the ZIP file
        zip_buffer = io.BytesIO()
        
        # Create ZIP file
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Convert row to dictionary
                    row_data = row.to_dict()
                    
                    # Generate markdown
                    markdown_content = generate_markdown_report(row_data, index + 1)
                    
                    # Generate PDF
                    pdf_data = generate_pdf_from_markdown(markdown_content)
                    
                    # Add PDF to ZIP file
                    zip_file.writestr(f'row_{index + 1}.pdf', pdf_data)
                except Exception as e:
                    logger.error(f"Error creating PDF for row {index + 1}: {str(e)}")
                    continue
        
        # Prepare the response
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="spreadsheet_{spreadsheet_id}_reports.zip"'
        return response
        
    except Spreadsheet.DoesNotExist:
        messages.error(request, "Spreadsheet not found")
        return redirect('spreadsheet_list')
    except Exception as e:
        logger.error(f"Error creating ZIP file: {str(e)}")
        messages.error(request, "Error downloading reports")
        return redirect('spreadsheet_list')
