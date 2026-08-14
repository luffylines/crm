#!/usr/bin/env python
"""
Test the complete workflow to demonstrate how it should work.
This simulates exactly what you want:
1. Upload a file with 2 sheets (Masterfile + Christian For Reval)
2. Click the file
3. See selection modal
4. Choose which sheet to edit
"""
import os
import io
import pandas as pd
import app as app_module

os.makedirs(app_module.DRAFT_DIR, exist_ok=True)

print("=" * 80)
print("SIMULATING YOUR WORKFLOW: Upload Intern Revalidation with 2 sheets")
print("=" * 80)

# Create the workbook exactly like yours: 2 sheets
wb_path = os.path.join(app_module.DRAFT_DIR, 'your_intern_revalidation.xlsx')
with pd.ExcelWriter(wb_path, engine='openpyxl') as writer:
    # Sheet 1: Masterfile
    masterfile_data = pd.DataFrame({
        'Company': ['Company A', 'Company B'],
        'Lead Ranking': ['good', 'best']
    })
    masterfile_data.to_excel(writer, sheet_name='Masterfile', index=False)
    
    # Sheet 2: Christian For Reval
    reval_data = pd.DataFrame({
        'Company': ['Company C', 'Company D'],
        'Lead Ranking': ['', '']
    })
    reval_data.to_excel(writer, sheet_name='Christian For Reval', index=False)

print(f"\n✓ Created test workbook with sheets: Masterfile, Christian For Reval")

# Simulate upload
client = app_module.app.test_client()
with client.session_transaction() as sess:
    sess['username'] = 'chan'  # Your username

print("\n--- STEP 1: Upload ---")
with open(wb_path, 'rb') as fh:
    resp = client.post(
        '/upload',
        data={'file': (io.BytesIO(fh.read()), 'Intern Revalidation - Validated by Christian - Aug 13, 2026.xlsx')},
        content_type='multipart/form-data'
    )

print(f"Upload status: {resp.status_code}")
upload_json = resp.get_json()
print(f"  Rows detected: {upload_json['total']}")

with client.session_transaction() as sess:
    file_key = sess.get('file_key')

print(f"  File key: {file_key}")

# Simulate clicking the file (without sheet parameter)
print("\n--- STEP 2: User clicks file in Files list ---")
resp = client.get(f'/open/{file_key}')
print(f"Open status: {resp.status_code}")
open_json = resp.get_json()

# Check if we got the selection modal
if 'worksheets' in open_json:
    print("✓ SELECTION MODAL SHOWN (correct!)")
    print(f"  Worksheets available:")
    for ws in open_json['worksheets']:
        print(f"    - {ws['name']} ({ws['rows']} rows, {ws.get('validated_count', 0)} validated)")
    
    # Simulate user choosing "Christian For Reval"
    print("\n--- STEP 3: User selects 'Christian For Reval' ---")
    resp = client.get(f'/open/{file_key}?sheet=Christian For Reval')
    sel_json = resp.get_json()
    print(f"Open status: {resp.status_code}")
    print(f"  Sheet selected: {sel_json.get('sheet_name')}")
    print(f"  Rows in this sheet: {sel_json['total']}")
    print("✓ VALIDATION SCREEN OPENS (correct!)")
    
    # Verify the draft file has both sheets
    print("\n--- VERIFICATION: Check saved Excel file ---")
    draft_file = os.path.join(app_module.DRAFT_DIR, f'chan_{file_key}_draft.xlsx')
    xl_saved = pd.read_excel(draft_file, sheet_name=None, dtype=str)
    saved_sheets = list(xl_saved.keys())
    print(f"  Sheets in saved file: {saved_sheets}")
    if set(saved_sheets) == {'Masterfile', 'Christian For Reval'}:
        print("✓ BOTH SHEETS PRESERVED (correct!)")
    else:
        print("✗ ERROR: Not all sheets preserved!")
else:
    print("✗ ERROR: No worksheet selection modal!")
    print(f"  Response: {open_json}")

print("\n" + "=" * 80)
print("SUMMARY: This is how the NEW code should work!")
print("=" * 80)
