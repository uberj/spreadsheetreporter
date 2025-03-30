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
import io
import zipfile
from django.views.decorators.http import require_http_methods

def upload_spreadsheet(request):
    if request.method == 'POST' and request.FILES.get('spreadsheet'):
        spreadsheet_file = request.FILES['spreadsheet']
        spreadsheet = Spreadsheet.objects.create(file=spreadsheet_file)
        
        try:
            # Read the Excel file
            df = pd.read_excel(spreadsheet.file)
            
            # Process each row
            for index, row in df.iterrows():
                # Convert row to dictionary
                row_data = row.to_dict()
                
                # Generate report content using template
                report_content = render_to_string(
                    'spreadsheet_processor/report_template.html',
                    {'data': row_data}
                )
                
                Report.objects.create(
                    spreadsheet=spreadsheet,
                    row_number=index + 1,
                    content=report_content
                )
            
            spreadsheet.processed = True
            spreadsheet.save()
            messages.success(request, 'Spreadsheet processed successfully!')
            return redirect('report_list')
            
        except Exception as e:
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
def download_reports_pdf(request):
    # Create a BytesIO object to store the ZIP file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Get all reports
        reports = Report.objects.all().order_by('row_number')
        
        for report in reports:
            # Create PDF
            pdf_buffer = io.BytesIO()
            p = canvas.Canvas(pdf_buffer, pagesize=letter)
            
            # Add title
            p.setFont("Helvetica-Bold", 16)
            p.drawString(50, 750, f"Report for Row {report.row_number}")
            
            # Add content
            p.setFont("Helvetica", 12)
            y = 700
            for line in report.content.split('\n'):
                if y < 50:  # Start new page if we're near the bottom
                    p.showPage()
                    y = 750
                p.drawString(50, y, line)
                y -= 20
            
            p.save()
            pdf_buffer.seek(0)
            
            # Add PDF to ZIP file
            zip_file.writestr(f'report_row_{report.row_number}.pdf', pdf_buffer.getvalue())
    
    # Prepare the response
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="reports.zip"'
    return response
