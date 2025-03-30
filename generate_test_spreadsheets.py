import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_simple_spreadsheet(filename, rows=100):
    """Generate a simple spreadsheet with basic data types."""
    data = {
        'ID': range(1, rows + 1),
        'Name': [f'Item {i}' for i in range(1, rows + 1)],
        'Price': np.random.uniform(10, 1000, rows).round(2),
        'Quantity': np.random.randint(1, 100, rows),
        'Category': np.random.choice(['A', 'B', 'C', 'D'], rows),
        'In Stock': np.random.choice([True, False], rows)
    }
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Generated {filename}")

def generate_dates_spreadsheet(filename, rows=100):
    """Generate a spreadsheet with date-based data."""
    start_date = datetime.now()
    dates = [start_date + timedelta(days=i) for i in range(rows)]
    
    data = {
        'Date': dates,
        'Sales': np.random.randint(1000, 5000, rows),
        'Customers': np.random.randint(50, 200, rows),
        'Revenue': np.random.uniform(5000, 20000, rows).round(2)
    }
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Generated {filename}")

def generate_formulas_spreadsheet(filename, rows=10):
    """Generate a spreadsheet with formulas and calculations."""
    data = {
        'Item': [f'Product {i}' for i in range(1, rows + 1)],
        'Unit Price': np.random.uniform(10, 100, rows).round(2),
        'Quantity': np.random.randint(1, 50, rows),
        'Discount %': np.random.randint(0, 30, rows)
    }
    df = pd.DataFrame(data)
    
    # Add calculated columns
    df['Subtotal'] = df['Unit Price'] * df['Quantity']
    df['Discount Amount'] = df['Subtotal'] * (df['Discount %'] / 100)
    df['Total'] = df['Subtotal'] - df['Discount Amount']
    
    df.to_excel(filename, index=False)
    print(f"Generated {filename}")

def generate_missing_data_spreadsheet(filename, rows=100):
    """Generate a spreadsheet with missing data patterns."""
    data = {
        'ID': range(1, rows + 1),
        'Name': [f'Item {i}' for i in range(1, rows + 1)],
        'Price': np.random.uniform(10, 1000, rows).round(2),
        'Quantity': np.random.randint(1, 100, rows),
        'Category': np.random.choice(['A', 'B', 'C', 'D', None], rows),
        'Notes': [None if np.random.random() < 0.3 else f'Note {i}' for i in range(1, rows + 1)]
    }
    df = pd.DataFrame(data)
    
    # Add some random missing values
    for col in df.columns:
        if col != 'ID':  # Keep ID column complete
            mask = np.random.random(rows) < 0.1
            df.loc[mask, col] = None
    
    df.to_excel(filename, index=False)
    print(f"Generated {filename}")

def main():
    # Create a directory for test files if it doesn't exist
    test_dir = 'test_spreadsheets'
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    # Generate various test spreadsheets
    generate_simple_spreadsheet(os.path.join(test_dir, 'simple_data.xlsx'))
    generate_dates_spreadsheet(os.path.join(test_dir, 'date_based_data.xlsx'))
    generate_formulas_spreadsheet(os.path.join(test_dir, 'formulas.xlsx'))
    generate_missing_data_spreadsheet(os.path.join(test_dir, 'missing_data.xlsx'))
    
    print("\nAll test spreadsheets have been generated in the 'test_spreadsheets' directory.")

if __name__ == '__main__':
    main() 