import pandas as pd
import sqlite3
import json
import os
from datetime import datetime
from jinja2 import Template
import hashlib

class ReportManager:
    def __init__(self):
        self.conn = sqlite3.connect('report_system.db')
        self.cursor = self.conn.cursor()
        self.reports_dir = 'reports'
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)

    def get_column_set_hash(self, columns):
        """Generate a hash of the column set for template identification."""
        return hashlib.md5(json.dumps(sorted(columns)).encode()).hexdigest()

    def get_template_for_columns(self, columns):
        """Retrieve or create a template for the given column set."""
        column_set_hash = self.get_column_set_hash(columns)
        
        # Check if we have a template for these columns
        self.cursor.execute('''
            SELECT id, template_content 
            FROM templates 
            WHERE column_set = ?
        ''', (json.dumps(sorted(columns)),))
        
        result = self.cursor.fetchone()
        
        if result:
            template_id, template_content = result
            # Update last_used timestamp
            self.cursor.execute('''
                UPDATE templates 
                SET last_used = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (template_id,))
            self.conn.commit()
            return template_id, Template(template_content)
        
        # If no template exists, generate a new one
        template_content = self.generate_template(columns)
        self.cursor.execute('''
            INSERT INTO templates (column_set, template_content)
            VALUES (?, ?)
        ''', (json.dumps(sorted(columns)), template_content))
        self.conn.commit()
        
        template_id = self.cursor.lastrowid
        return template_id, Template(template_content)

    def generate_template(self, columns):
        """Generate a new Jinja template for the given columns."""
        # This is where we would normally call Claude to generate the template
        # For now, we'll use a basic template that handles any columns
        template = """
FOOD MANUFACTURING PLANT INCIDENT REPORT
======================================

Report Generated: {{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}
Report ID: {{ batch_number }}

INCIDENT DETAILS
---------------
{% for column in columns %}
{% if column not in ['description', 'corrective_action', 'notes'] %}
{{ column|replace('_', ' ')|title }}: {{ row[column] }}
{% endif %}
{% endfor %}

DESCRIPTION
----------
{{ description }}

CORRECTIVE ACTION
---------------
{{ corrective_action }}

ADDITIONAL NOTES
--------------
{{ notes }}

======================================
This is an official document. Please handle accordingly.
"""
        return template

    def process_unprocessed_issues(self, excel_file):
        """Process unprocessed issues and generate reports."""
        # Read the Excel file
        df = pd.read_excel(excel_file)
        
        # Get template for current column set
        template_id, template = self.get_template_for_columns(df.columns.tolist())
        
        # Process unprocessed issues
        unprocessed_mask = df['processed'] == False
        unprocessed_issues = df[unprocessed_mask]
        
        if len(unprocessed_issues) == 0:
            print("No unprocessed issues found.")
            return
        
        print(f"Found {len(unprocessed_issues)} unprocessed issues.")
        
        # Generate reports for each unprocessed issue
        for index, row in unprocessed_issues.iterrows():
            # Prepare data for template
            report_data = row.to_dict()
            report_data['columns'] = df.columns.tolist()
            
            # Generate report using template
            report = template.render(**report_data)
            
            # Create filename using batch number and date
            filename = f"report_{row['batch_number']}_{row['date'].replace('-', '_')}.txt"
            filepath = os.path.join(self.reports_dir, filename)
            
            # Save report to file
            with open(filepath, 'w') as f:
                f.write(report)
            
            # Store report data in database
            self.cursor.execute('''
                INSERT INTO reports (template_id, report_data, file_path)
                VALUES (?, ?, ?)
            ''', (template_id, json.dumps(report_data), filepath))
            
            print(f"Generated report: {filename}")
            
            # Mark issue as processed
            df.at[index, 'processed'] = True
        
        # Save updated DataFrame back to Excel
        df.to_excel(excel_file, index=False)
        self.conn.commit()
        print(f"\nUpdated spreadsheet saved: {excel_file}")

    def __del__(self):
        """Close database connection when the object is destroyed."""
        self.conn.close()

if __name__ == "__main__":
    report_manager = ReportManager()
    report_manager.process_unprocessed_issues('food_manufacturing_issues.xlsx') 