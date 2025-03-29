import pandas as pd
from datetime import datetime
import os

def generate_report(row):
    """Generate an official report for an unprocessed issue."""
    report = f"""
FOOD MANUFACTURING PLANT INCIDENT REPORT
======================================

Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Report ID: {row['batch_number']}

INCIDENT DETAILS
---------------
Date: {row['date']}
Time: {row['time']}
Department: {row['department']}
Issue Type: {row['issue_type']}
Severity Level: {row['severity']}
Status: {row['status']}

AFFECTED PRODUCT
---------------
Product: {row['affected_product']}
Batch Number: {row['batch_number']}

REPORTING INFORMATION
-------------------
Reported By: {row['reported_by']}
Assigned To: {row['assigned_to']}
Resolution Date: {row['resolution_date']}

DESCRIPTION
----------
{row['description']}

CORRECTIVE ACTION
---------------
{row['corrective_action']}

ADDITIONAL NOTES
--------------
{row['notes']}

======================================
This is an official document. Please handle accordingly.
"""
    return report

def process_unprocessed_issues():
    """Process unprocessed issues and generate reports."""
    # Read the Excel file
    excel_file = 'food_manufacturing_issues.xlsx'
    df = pd.read_excel(excel_file)
    
    # Create reports directory if it doesn't exist
    reports_dir = 'reports'
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    
    # Process unprocessed issues
    unprocessed_mask = df['processed'] == False
    unprocessed_issues = df[unprocessed_mask]
    
    if len(unprocessed_issues) == 0:
        print("No unprocessed issues found.")
        return
    
    print(f"Found {len(unprocessed_issues)} unprocessed issues.")
    
    # Generate reports for each unprocessed issue
    for index, row in unprocessed_issues.iterrows():
        # Generate report
        report = generate_report(row)
        
        # Create filename using batch number and date
        filename = f"report_{row['batch_number']}_{row['date'].replace('-', '_')}.txt"
        filepath = os.path.join(reports_dir, filename)
        
        # Save report to file
        with open(filepath, 'w') as f:
            f.write(report)
        
        print(f"Generated report: {filename}")
        
        # Mark issue as processed
        df.at[index, 'processed'] = True
    
    # Save updated DataFrame back to Excel
    df.to_excel(excel_file, index=False)
    print(f"\nUpdated spreadsheet saved: {excel_file}")

if __name__ == "__main__":
    process_unprocessed_issues() 