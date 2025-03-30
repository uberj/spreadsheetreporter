from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_spreadsheet, name='upload_spreadsheet'),
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('reports/download-pdf/', views.download_reports_pdf, name='download_reports_pdf'),
] 