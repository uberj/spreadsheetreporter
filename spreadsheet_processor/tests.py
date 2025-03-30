from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Spreadsheet
import pandas as pd
import io
import zipfile
import markdown

class SpreadsheetProcessorTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse('upload_spreadsheet')
        self.spreadsheet_list_url = reverse('spreadsheet_list')
        
        # Create a test Excel file
        data = {
            'Name': ['John Doe', 'Jane Smith'],
            'Age': [30, 25],
            'Department': ['IT', 'HR']
        }
        df = pd.DataFrame(data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False, engine='openpyxl')
        excel_file.seek(0)
        self.test_file = SimpleUploadedFile(
            'test.xlsx',
            excel_file.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_spreadsheet_model(self):
        """Test the Spreadsheet model creation and string representation"""
        spreadsheet = Spreadsheet.objects.create(
            file=self.test_file,
            processed=True
        )
        self.assertTrue(spreadsheet.processed)
        self.assertIn('Spreadsheet uploaded at', str(spreadsheet))

    def test_upload_view_get(self):
        """Test the upload view GET request"""
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spreadsheet_processor/upload.html')

    def test_upload_view_post_success(self):
        """Test successful spreadsheet upload"""
        response = self.client.post(
            self.upload_url,
            {'spreadsheet': self.test_file},
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spreadsheet_processor/spreadsheet_list.html')
        
        # Check if spreadsheet was created
        self.assertEqual(Spreadsheet.objects.count(), 1)
        spreadsheet = Spreadsheet.objects.first()
        self.assertTrue(spreadsheet.processed)

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

    def test_spreadsheet_list_view(self):
        """Test the spreadsheet list view"""
        # Create test data
        spreadsheet = Spreadsheet.objects.create(file=self.test_file, processed=True)
        
        response = self.client.get(self.spreadsheet_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spreadsheet_processor/spreadsheet_list.html')
        self.assertEqual(len(response.context['spreadsheets']), 1)

    def test_spreadsheet_list_view_empty(self):
        """Test the spreadsheet list view when no spreadsheets exist"""
        response = self.client.get(self.spreadsheet_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spreadsheet_processor/spreadsheet_list.html')
        self.assertEqual(len(response.context['spreadsheets']), 0)

    def test_download_spreadsheet_reports(self):
        """Test downloading reports for a spreadsheet"""
        # Create test data
        spreadsheet = Spreadsheet.objects.create(file=self.test_file, processed=True)
        
        # Test GET request (should work now)
        download_url = reverse('download_spreadsheet_reports', args=[spreadsheet.id])
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        
        # Test POST request
        response = self.client.post(download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertEqual(
            response['Content-Disposition'],
            f'attachment; filename="spreadsheet_{spreadsheet.id}_reports.zip"'
        )
        
        # Verify ZIP file contents
        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            # Should contain 2 PDFs (one for each row, excluding header)
            self.assertEqual(len(zip_file.namelist()), 2)
            self.assertTrue('row_1.pdf' in zip_file.namelist())
            self.assertTrue('row_2.pdf' in zip_file.namelist())

    def test_download_spreadsheet_reports_not_found(self):
        """Test downloading reports for a non-existent spreadsheet"""
        download_url = reverse('download_spreadsheet_reports', args=[999])
        response = self.client.post(download_url, follow=True)
        self.assertRedirects(response, self.spreadsheet_list_url)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Spreadsheet not found')
