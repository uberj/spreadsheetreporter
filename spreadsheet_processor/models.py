from django.db import models
from django.utils import timezone

class Spreadsheet(models.Model):
    file = models.FileField(upload_to='spreadsheets/')
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Spreadsheet uploaded at {self.uploaded_at}"

class Report(models.Model):
    spreadsheet = models.ForeignKey(Spreadsheet, on_delete=models.CASCADE, related_name='reports')
    row_number = models.IntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Report for row {self.row_number} from {self.spreadsheet}"
