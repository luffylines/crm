#!/usr/bin/env python
import os
import io
import pandas as pd
import app as app_module

# Clean slate
os.makedirs(app_module.DRAFT_DIR, exist_ok=True)

# Create a test workbook with 2 sheets
wb_path = os.path.join(app_module.DRAFT_DIR, 'test_multi.xlsx')
with pd.ExcelWriter(wb_path, engine='openpyxl') as writer:
    pd.DataFrame({'Company': ['Alpha'], 'Lead Ranking': ['good']}).to_excel(
        writer, sheet_name='Masterfile', index=False
    )
    pd.DataFrame({'Company': ['Bravo'], 'Lead Ranking': ['best']}).to_excel(
        writer, sheet_name='Christian For Reval', index=False
    )

# Check sheets in the file
xl = pd.read_excel(wb_path, sheet_name=None, dtype=str)
print('Original file sheets:', list(xl.keys()))

# Now simulate upload
client = app_module.app.test_client()
with client.session_transaction() as sess:
    sess['username'] = 'testuser'

with open(wb_path, 'rb') as fh:
    resp = client.post(
        '/upload',
        data={'file': (io.BytesIO(fh.read()), 'test_multi.xlsx')},
        content_type='multipart/form-data'
    )
    
print('Upload response:', resp.status_code, resp.get_json())

# Get file key
file_key = None
with client.session_transaction() as sess:
    file_key = sess.get('file_key')
    print(f'File key from session: {file_key}')

# Check the draft directory
draft_files = [f for f in os.listdir(app_module.DRAFT_DIR) if f.startswith('testuser_') and f.endswith('_draft.xlsx')]
print('Draft files created (testuser):', draft_files)

# Read the draft file directly - construct the expected name based on file_key
if file_key:
    expected_draft = f'testuser_{file_key}_draft.xlsx'
    draft_file = os.path.join(app_module.DRAFT_DIR, expected_draft)
    if os.path.exists(draft_file):
        print(f'Reading draft file: {os.path.basename(draft_file)}')
        xl_saved = pd.read_excel(draft_file, sheet_name=None, dtype=str)
        print('Saved file sheets:', list(xl_saved.keys()))
        print('Number of sheets saved:', len(xl_saved))
    else:
        print(f'Draft file not found: {expected_draft}')

# Now test opening without sheet parameter
print('\nOpening file...')
resp = client.get(f'/open/{file_key}')
print('Open response (no sheet):', resp.status_code, resp.get_json())

