import pickle
import os

# Check one of the pickle files
pkl_file = './drafts/chan_Intern Revalidation -Validated by Christian - Aug 13, 2026.pkl'

if os.path.exists(pkl_file):
    with open(pkl_file, 'rb') as f:
        store = pickle.load(f)
    
    print("Pickle file contents keys:", list(store.keys()))
    print()
    
    if 'sheet_map' in store:
        sheet_map = store['sheet_map']
        print("sheet_map found!")
        print(f"  Sheets in sheet_map: {list(sheet_map.keys())}")
        for sheet_name, df in sheet_map.items():
            print(f"    {sheet_name}: {len(df)} rows, columns: {list(df.columns)}")
    else:
        print("No sheet_map in pickle file")
    
    print()
    print("working_sheet_name:", store.get('working_sheet_name'))
else:
    print(f"Pickle file not found: {pkl_file}")
