from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_spreadsheet, name='upload_spreadsheet'),
    path('spreadsheets/', views.SpreadsheetListView.as_view(), name='spreadsheet_list'),
    path('spreadsheets/<int:spreadsheet_id>/download/', views.download_spreadsheet_reports, name='download_spreadsheet_reports'),
    path('health/', views.health_check, name='health_check'),
] 