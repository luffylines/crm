import os
import pandas as pd

# Check the existing draft files
draft_dir = './drafts'
files = [f for f in os.listdir(draft_dir) if 'chan_Intern Revalidation' in f and f.endswith('_draft.xlsx')]
print(f"Found {len(files)} Intern Revalidation files:")
for f in sorted(files):
    full_path = os.path.join(draft_dir, f)
    try:
        sheets = pd.read_excel(full_path, sheet_name=None, dtype=str)
        sheet_names = list(sheets.keys())
        print(f"  {f}")
        print(f"    Sheets: {sheet_names} (count: {len(sheet_names)})")
    except Exception as e:
        print(f"  {f} - ERROR: {e}")
