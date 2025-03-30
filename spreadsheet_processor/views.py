from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView
from .models import Spreadsheet
import pandas as pd
from django.http import HttpResponse, JsonResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import zipfile
from django.views.decorators.http import require_http_methods
from datetime import datetime
import os
import logging
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_pdf_report(row_data, row_number):
    """Generate a beautiful PDF report for a single row"""
    try:
        # Create a buffer for the PDF
        pdf_buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Center alignment
        ))
        
        styles.add(ParagraphStyle(
            name='CustomSubTitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#34495e'),
            alignment=1  # Center alignment
        ))
        
        styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        # Build PDF content
        story = []
        
        # Add title
        story.append(Paragraph(f"Data Report", styles['CustomTitle']))
        story.append(Paragraph(f"Row {row_number}", styles['CustomSubTitle']))
        story.append(Spacer(1, 30))
        
        # Create table data
        table_data = [['Field', 'Value']]
        for field, value in row_data.items():
            table_data.append([field, str(value)])
        
        # Create table
        table = Table(table_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Add footer
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['CustomBodyText']))
        
        # Build PDF
        doc.build(story)
        
        # Get the PDF data
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
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
                    
                    # Generate PDF
                    pdf_data = generate_pdf_report(row_data, index + 1)
                    
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

def health_check(request):
    """
    Simple health check endpoint that returns 200 OK.
    """
    return JsonResponse({"status": "healthy"})
