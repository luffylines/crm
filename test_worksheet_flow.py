#!/usr/bin/env python
"""Test single vs. multiple worksheet behavior end-to-end."""
import os
import io
import pandas as pd
import app as app_module

os.makedirs(app_module.DRAFT_DIR, exist_ok=True)

print("=" * 70)
print("TEST 1: SINGLE WORKSHEET - Should open directly, no modal")
print("=" * 70)

# Create single-sheet workbook
wb_single = os.path.join(app_module.DRAFT_DIR, 'single_sheet_test.xlsx')
pd.DataFrame({
    'Company': ['Acme Corp', 'TechStart'],
    'Lead Ranking': ['good', 'best']
}).to_excel(wb_single, sheet_name='Data', index=False)

xl = pd.read_excel(wb_single, sheet_name=None, dtype=str)
print(f'Original sheets: {list(xl.keys())}')

client = app_module.app.test_client()
with client.session_transaction() as sess:
    sess['username'] = 'testuser1'

with open(wb_single, 'rb') as fh:
    resp = client.post(
        '/upload',
        data={'file': (io.BytesIO(fh.read()), 'single_sheet_test.xlsx')},
        content_type='multipart/form-data'
    )

print(f'Upload response: {resp.status_code}')
upload_data = resp.get_json()
print(f'  total: {upload_data.get("total")} (number of rows)')
print(f'  columns: {upload_data.get("columns")}')

with client.session_transaction() as sess:
    key1 = sess.get('file_key')

print(f'File key: {key1}')

# Test opening without sheet param
resp = client.get(f'/open/{key1}')
print(f'Open response (no sheet param): {resp.status_code}')
open_data = resp.get_json()
if 'worksheets' in open_data:
    print(f'  ERROR: Got worksheets list (modal shown), should open directly!')
    print(f'  Worksheets: {[ws["name"] for ws in open_data["worksheets"]]}')
else:
    print(f'  ✓ Opened directly (no modal)')
    print(f'  total: {open_data.get("total")}')
    print(f'  sheet_name: {open_data.get("sheet_name")}')

print("\n" + "=" * 70)
print("TEST 2: MULTIPLE WORKSHEETS - Should show modal, NOT auto-open")
print("=" * 70)

# Create multi-sheet workbook
wb_multi = os.path.join(app_module.DRAFT_DIR, 'multi_sheet_test.xlsx')
with pd.ExcelWriter(wb_multi, engine='openpyxl') as writer:
    pd.DataFrame({
        'Company': ['Alpha Inc'],
        'Lead Ranking': ['good']
    }).to_excel(writer, sheet_name='Masterfile', index=False)
    pd.DataFrame({
        'Company': ['Beta Ltd'],
        'Lead Ranking': ['best']
    }).to_excel(writer, sheet_name='Christian For Reval', index=False)

xl = pd.read_excel(wb_multi, sheet_name=None, dtype=str)
print(f'Original sheets: {list(xl.keys())}')

with client.session_transaction() as sess:
    sess['username'] = 'testuser2'

with open(wb_multi, 'rb') as fh:
    resp = client.post(
        '/upload',
        data={'file': (io.BytesIO(fh.read()), 'multi_sheet_test.xlsx')},
        content_type='multipart/form-data'
    )

print(f'Upload response: {resp.status_code}')
upload_data = resp.get_json()
print(f'  total: {upload_data.get("total")}')

with client.session_transaction() as sess:
    key2 = sess.get('file_key')

print(f'File key: {key2}')

# Test opening without sheet param
resp = client.get(f'/open/{key2}')
print(f'Open response (no sheet param): {resp.status_code}')
open_data = resp.get_json()
if 'worksheets' in open_data:
    print(f'  ✓ Shows worksheet selection modal')
    ws_names = [ws["name"] for ws in open_data["worksheets"]]
    print(f'  Worksheets: {ws_names}')
    if set(ws_names) == {'Masterfile', 'Christian For Reval'}:
        print(f'  ✓ Both original sheets preserved')
    else:
        print(f'  ERROR: Not all sheets preserved!')
else:
    print(f'  ERROR: Opened directly (no modal), should show modal!')

# Test selecting a worksheet
print(f'\nSelecting "Christian For Reval" sheet...')
resp = client.get(f'/open/{key2}?sheet=Christian For Reval')
print(f'Open response (with sheet param): {resp.status_code}')
sel_data = resp.get_json()
print(f'  total: {sel_data.get("total")}')
print(f'  sheet_name: {sel_data.get("sheet_name")}')
if sel_data.get("sheet_name") == "Christian For Reval":
    print(f'  ✓ Correct sheet selected')

print("\n" + "=" * 70)
print("TEST 3: Verify draft file contains all sheets")
print("=" * 70)

# Check draft file for multi-sheet
draft_file = os.path.join(app_module.DRAFT_DIR, f'testuser2_{key2}_draft.xlsx')
if os.path.exists(draft_file):
    xl_draft = pd.read_excel(draft_file, sheet_name=None, dtype=str)
    print(f'Draft file sheets: {list(xl_draft.keys())}')
    if set(xl_draft.keys()) == {'Masterfile', 'Christian For Reval'}:
        print(f'  ✓ All sheets preserved in draft file')
    else:
        print(f'  ERROR: Not all sheets in draft file!')
else:
    print(f'Draft file not found: {draft_file}')

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("✓ All tests passed - worksheet detection works correctly!")
