from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Spreadsheet, Report
import pandas as pd
import io
import json
import zipfile

class SpreadsheetProcessorTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse('upload_spreadsheet')
        self.report_list_url = reverse('report_list')
        self.home_url = reverse('home')
        self.download_pdf_url = reverse('download_reports_pdf')
        
        # Create a test Excel file
        data = {
            'Name': ['John Doe', 'Jane Smith'],
            'Age': [30, 25],
            'Department': ['IT', 'HR']
        }
        df = pd.DataFrame(data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        self.test_file = SimpleUploadedFile(
            'test.xlsx',
            excel_file.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_root_url_redirect(self):
        """Test that the root URL redirects to the upload page"""
        response = self.client.get(self.home_url, follow=False)
        self.assertEqual(response.status_code, 302)  # Check for redirect
        self.assertEqual(response.url, self.upload_url)

    def test_spreadsheet_model(self):
        """Test the Spreadsheet model creation and string representation"""
        spreadsheet = Spreadsheet.objects.create(
            file=self.test_file,
            processed=True
        )
        self.assertTrue(spreadsheet.processed)
        self.assertIn('Spreadsheet uploaded at', str(spreadsheet))

    def test_report_model(self):
        """Test the Report model creation and string representation"""
        spreadsheet = Spreadsheet.objects.create(file=self.test_file)
        report = Report.objects.create(
            spreadsheet=spreadsheet,
            row_number=1,
            content='Name: John Doe\nAge: 30'
        )
        self.assertEqual(report.row_number, 1)
        self.assertEqual(report.spreadsheet, spreadsheet)
        self.assertIn('Report for row 1', str(report))

    def test_upload_view_get(self):
        """Test the upload view GET request"""
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spreadsheet_processor/upload.html')

    def test_upload_view_post_success(self):
        """Test successful spreadsheet upload and processing"""
        response = self.client.post(
            self.upload_url,
            {'spreadsheet': self.test_file},
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spreadsheet_processor/report_list.html')
        
        # Check if spreadsheet was created
        self.assertEqual(Spreadsheet.objects.count(), 1)
        spreadsheet = Spreadsheet.objects.first()
        self.assertTrue(spreadsheet.processed)
        
        # Check if reports were created
        self.assertEqual(Report.objects.count(), 2)
        
        # Verify report content
        reports = Report.objects.all()
        self.assertEqual(reports[0].row_number, 1)
        self.assertEqual(reports[1].row_number, 2)
        
        # Verify report content contains expected data
        self.assertIn('Name: John Doe', reports[0].content)
        self.assertIn('Age: 30', reports[0].content)

    def test_upload_view_post_invalid_file(self):
        """Test upload with invalid file"""
        invalid_file = SimpleUploadedFile(
            'test.txt',
            b'not an excel file',
            content_type='text/plain'
        )
        response = self.client.post(
            self.upload_url,
            {'spreadsheet': invalid_file},
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spreadsheet_processor/upload.html')
        self.assertEqual(Spreadsheet.objects.count(), 0)
        self.assertEqual(Report.objects.count(), 0)

    def test_report_list_view(self):
        """Test the report list view"""
        # Create test data
        spreadsheet = Spreadsheet.objects.create(file=self.test_file)
        Report.objects.create(
            spreadsheet=spreadsheet,
            row_number=1,
            content='Name: John Doe\nAge: 30'
        )
        
        response = self.client.get(self.report_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spreadsheet_processor/report_list.html')
        self.assertEqual(len(response.context['reports']), 1)

    def test_report_list_view_empty(self):
        """Test the report list view when no reports exist"""
        response = self.client.get(self.report_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spreadsheet_processor/report_list.html')
        self.assertEqual(len(response.context['reports']), 0)

    def test_download_reports_pdf(self):
        """Test downloading reports as PDF"""
        # Create test data
        spreadsheet = Spreadsheet.objects.create(file=self.test_file)
        Report.objects.create(
            spreadsheet=spreadsheet,
            row_number=1,
            content='Name: John Doe\nAge: 30'
        )
        
        # Test GET request (should fail)
        response = self.client.get(self.download_pdf_url)
        self.assertEqual(response.status_code, 405)
        
        # Test POST request
        response = self.client.post(self.download_pdf_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        
        # Verify ZIP file contents
        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            self.assertEqual(len(zip_file.namelist()), 1)
            self.assertIn('report_row_1.pdf', zip_file.namelist())

    def test_end_to_end_flow(self):
        """Test the complete end-to-end flow"""
        # Step 1: Visit upload page
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Upload spreadsheet
        response = self.client.post(
            self.upload_url,
            {'spreadsheet': self.test_file},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Verify reports were created
        self.assertEqual(Report.objects.count(), 2)
        
        # Step 4: View reports
        response = self.client.get(self.report_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['reports']), 2)
        
        # Step 5: Verify report content
        reports = Report.objects.all()
        self.assertIn('Name: John Doe', reports[0].content)
        self.assertIn('Age: 30', reports[0].content)
        self.assertIn('Department: IT', reports[0].content)
