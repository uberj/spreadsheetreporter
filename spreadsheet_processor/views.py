from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView
from .models import Spreadsheet, Report
import pandas as pd
from django.http import HttpResponse
import json
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import zipfile
from django.views.decorators.http import require_http_methods
from jinja2 import Environment, FileSystemLoader
import markdown
from datetime import datetime
import os
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

def get_jinja_env():
    """Create and return a Jinja2 environment"""
    try:
        template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'spreadsheet_processor')
        logger.info(f"Template directory: {template_dir}")
        if not os.path.exists(template_dir):
            logger.error(f"Template directory does not exist: {template_dir}")
            os.makedirs(template_dir, exist_ok=True)
            logger.info(f"Created template directory: {template_dir}")
        
        env = Environment(
            loader=FileSystemLoader(template_dir)
        )
        return env
    except Exception as e:
        logger.error(f"Error creating Jinja2 environment: {str(e)}")
        raise

def generate_markdown_report(row_data, row_number, report_id):
    """Generate a markdown report using Jinja2"""
    try:
        env = get_jinja_env()
        template = env.get_template('markdown_report_template.md')
        
        context = {
            'data': row_data,
            'row_number': row_number,
            'report_id': report_id,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return template.render(**context)
    except Exception as e:
        logger.error(f"Error generating markdown report: {str(e)}")
        # Fallback to a simple format if template fails
        lines = [f"# Report for Row {row_number}\n\n## Data Summary\n"]
        for field, value in row_data.items():
            lines.append(f"- **{field}**: {value}")
        return "\n".join(lines)

def markdown_to_pdf(markdown_content, pdf_buffer):
    """Convert markdown content to PDF using HTML conversion"""
    try:
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
    except Exception as e:
        logger.error(f"Error converting markdown to PDF: {str(e)}")
        raise

def upload_spreadsheet(request):
    if request.method == 'POST' and request.FILES.get('spreadsheet'):
        spreadsheet_file = request.FILES['spreadsheet']
        spreadsheet = Spreadsheet.objects.create(file=spreadsheet_file)
        
        try:
            # Read the Excel file
            df = pd.read_excel(spreadsheet.file)
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Convert row to dictionary
                    row_data = row.to_dict()  # pandas Series to_dict() returns a dictionary
                    
                    # Generate markdown report
                    report_id = f"report_{spreadsheet.id}_{index + 1}"
                    markdown_content = generate_markdown_report(row_data, index + 1, report_id)
                    
                    Report.objects.create(
                        spreadsheet=spreadsheet,
                        row_number=index + 1,
                        content=markdown_content
                    )
                except Exception as e:
                    logger.error(f"Error processing row {index + 1}: {str(e)}")
                    continue
            
            if Report.objects.filter(spreadsheet=spreadsheet).exists():
                spreadsheet.processed = True
                spreadsheet.save()
                messages.success(request, 'Spreadsheet processed successfully!')
                return redirect('report_list')
            else:
                messages.error(request, 'No rows were processed successfully.')
                spreadsheet.delete()
                return render(request, 'spreadsheet_processor/upload.html')
            
        except Exception as e:
            logger.error(f"Error processing spreadsheet: {str(e)}")
            messages.error(request, f'Error processing spreadsheet: {str(e)}')
            spreadsheet.delete()
            return render(request, 'spreadsheet_processor/upload.html')
    
    return render(request, 'spreadsheet_processor/upload.html')

class ReportListView(ListView):
    model = Report
    template_name = 'spreadsheet_processor/report_list.html'
    context_object_name = 'reports'
    ordering = ['-created_at']

@require_http_methods(["POST"])
def download_report(request, report_id):
    """Download a report as PDF"""
    try:
        report = Report.objects.get(id=report_id)
        
        # Create a buffer to store the PDF
        pdf_buffer = io.BytesIO()
        
        # Convert markdown to PDF
        markdown_to_pdf(report.content, pdf_buffer)
        
        # Get the value of the buffer and write the response
        pdf = pdf_buffer.getvalue()
        
        # Create the HTTP response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="report_{report.id}.pdf"'
        return response
        
    except Report.DoesNotExist:
        messages.error(request, "Report not found")
        return redirect('report_list')
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        messages.error(request, f"Error downloading report: {str(e)}")
        return redirect('report_list')
