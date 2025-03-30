from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView
from .models import Spreadsheet, Report
import pandas as pd
from django.http import HttpResponse
import json

def upload_spreadsheet(request):
    if request.method == 'POST' and request.FILES.get('spreadsheet'):
        spreadsheet_file = request.FILES['spreadsheet']
        spreadsheet = Spreadsheet.objects.create(file=spreadsheet_file)
        
        try:
            # Read the Excel file
            df = pd.read_excel(spreadsheet.file)
            
            # Process each row
            for index, row in df.iterrows():
                # Convert row to dictionary and create a formatted report
                row_data = row.to_dict()
                report_content = json.dumps(row_data, indent=2)
                
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
            return redirect('upload_spreadsheet')
    
    return render(request, 'spreadsheet_processor/upload.html')

class ReportListView(ListView):
    model = Report
    template_name = 'spreadsheet_processor/report_list.html'
    context_object_name = 'reports'
    ordering = ['-created_at']
