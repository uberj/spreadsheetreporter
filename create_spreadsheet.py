import pandas as pd
import random
from datetime import datetime, timedelta
import faker

# Initialize faker for generating realistic data
fake = faker.Faker()

# Define food manufacturing specific data
departments = [
    'Production Line', 'Quality Control', 'Packaging', 'Warehouse', 
    'Sanitation', 'Maintenance', 'Food Safety', 'Inventory Management'
]

issue_types = [
    'Equipment Malfunction', 'Quality Deviation', 'Temperature Control',
    'Cross-Contamination Risk', 'Packaging Defect', 'Staff Safety',
    'Inventory Shortage', 'Sanitation Issue', 'Food Safety Violation',
    'Production Delay'
]

severity_levels = ['Low', 'Medium', 'High', 'Critical']

status_options = ['Open', 'In Progress', 'Under Investigation', 'Resolved', 'Closed']

# Generate sample data
num_rows = 20
data = {
    'date': [fake.date() for _ in range(num_rows)],
    'time': [fake.time() for _ in range(num_rows)],
    'reported_by': [fake.name() for _ in range(num_rows)],
    'department': [random.choice(departments) for _ in range(num_rows)],
    'issue_type': [random.choice(issue_types) for _ in range(num_rows)],
    'severity': [random.choice(severity_levels) for _ in range(num_rows)],
    'status': [random.choice(status_options) for _ in range(num_rows)],
    'description': [fake.text(max_nb_chars=200) for _ in range(num_rows)],
    'affected_product': [random.choice(['Chicken', 'Beef', 'Fish', 'Vegetables', 'Dairy', 'Bakery']) for _ in range(num_rows)],
    'batch_number': [f"BATCH-{random.randint(1000, 9999)}" for _ in range(num_rows)],
    'assigned_to': [fake.name() for _ in range(num_rows)],
    'resolution_date': [(datetime.strptime(fake.date(), '%Y-%m-%d') + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d') for _ in range(num_rows)],
    'corrective_action': [fake.text(max_nb_chars=150) for _ in range(num_rows)],
    'notes': [fake.text(max_nb_chars=100) for _ in range(num_rows)],
    'processed': [False for _ in range(num_rows)]
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel file
excel_file = 'food_manufacturing_issues.xlsx'
df.to_excel(excel_file, index=False, sheet_name='Food Manufacturing Issues')

# Format the Excel file
with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a') as writer:
    workbook = writer.book
    worksheet = workbook['Food Manufacturing Issues']
    
    # Adjust column widths
    for column in worksheet.columns:
        max_length = 0
        column = [cell for cell in column]
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

print(f"Food manufacturing issues spreadsheet has been created: {excel_file}") 