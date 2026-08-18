"""
Inspect the test Excel file to understand its structure
"""

import openpyxl
import pandas as pd

test_file = r"c:\xampp\htdocs\crm\drafts\chan_Christian - Practice Validation for Interns_draft.xlsx"

print("=" * 60)
print("EXCEL FILE INSPECTION")
print("=" * 60)

# Use openpyxl to get sheet names
wb = openpyxl.load_workbook(test_file)
print(f"\nSheet names in workbook: {wb.sheetnames}")

# Use pandas to get more details
xls = pd.ExcelFile(test_file)
print(f"\nSheet names (pandas): {xls.sheet_names}")

for sheet in xls.sheet_names:
    df = pd.read_excel(test_file, sheet_name=sheet)
    print(f"\nSheet: {sheet}")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Column names: {list(df.columns)}")
    
    # Check for Validated By column
    if "Validated By" in df.columns:
        print(f"  Validated By values: {df['Validated By'].value_counts().to_dict()}")
