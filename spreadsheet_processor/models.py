from django.db import models
from django.utils import timezone

class Spreadsheet(models.Model):
    file = models.FileField(upload_to='spreadsheets/')
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Spreadsheet uploaded at {self.uploaded_at}"
