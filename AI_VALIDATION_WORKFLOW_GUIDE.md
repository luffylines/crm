# AI Excel Validation - Multi-Worksheet Workflow Guide

## Overview
The AI Excel Validation feature now supports multi-worksheet workbooks with a 4-step workflow that provides complete transparency before processing begins.

## Workflow Steps

### Step 1: Upload Excel File
**What happens:**
- User clicks "Choose Excel File" button
- Selects a .xlsx or .xlsm file from their computer
- Frontend shows: "Selected: filename.xlsx"

**Behind the scenes:**
- File is immediately analyzed using `/api/ai-validation/inspect-worksheets`
- System detects all worksheets in the file
- System counts rows in each sheet
- System identifies which rows are already validated

---

### Step 2: Select Worksheet to Validate
**What the user sees:**
- Cards for each worksheet in the file showing:
  - Worksheet name (e.g., "Masterfile", "Christian For Reval")
  - Total Records count
  - Already Validated count
  - Needs Validation count
- User clicks to select one worksheet
- Only one worksheet can be selected at a time

**Example display:**
```
┌──────────────────────────────────┐
│ Masterfile                       │
│ ────────────────────────────────│
│ Total Records:    1000          │
│ Already Validated: 400          │
│ Needs Validation:  600          │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ Christian For Reval              │
│ ────────────────────────────────│
│ Total Records:    150           │
│ Already Validated: 50           │
│ Needs Validation:  100          │
└──────────────────────────────────┘
```

**Auto-selection:** If the file has only 1 worksheet, it's automatically selected and you skip to Step 3.

---

### Step 3: Review Validation Summary
**What the user sees:**
- Selected Worksheet name
- Summary statistics:
  - Total Records
  - Already Validated (won't be changed)
  - Needs Validation (will be processed)
- Breakdown by Validator showing who validated how many rows:
  - Christian: 200
  - Asia: 150
  - Nathan: 50
  - (blank/empty): 600
- Validator dropdown to select your name
- "Start AI Validation" button

**Example display:**
```
Selected Worksheet: Masterfile

SUMMARY
────────────────────────────────────
Total Records:        1000
Already Validated:      400
Needs Validation:       600

VALIDATED BY BREAKDOWN
────────────────────────────────────
Christian:           200
Asia:                150
Nathan:               50
(blank):             600

VALIDATOR: [Christian ▼]

[Start AI Validation] button
```

---

### Step 4: Validation Progress & Results
**During validation:**
- Real-time progress bar shows completion percentage
- Stats grid displays:
  - Processed: number of rows examined
  - Verified: complete enrichments found
  - Partial: partial data enriched
  - Conflicts: existing data preserved
  - Not Found: no match in People Data Labs
  - Errors: validation errors

**After completion:**
- Status shows "Validation complete!"
- Download button to get the validated Excel file

---

## Key Features

### ✅ Data Preservation
- **Already validated rows are SKIPPED**: If a row has a "Validated By" value different from yours, it's not modified
- **All worksheets are preserved**: Only the selected worksheet is modified; other sheets remain unchanged
- **Existing data is respected**: Company, First Name, Last Name, Title, Email, Phone, Website, etc. are not overwritten

### ✅ Transparency
- See exactly what rows need validation BEFORE starting
- Know who already validated rows in your sheet
- Understand why "Processed" might equal "Verified+Partial" (some rows may be skipped)
- Real-time progress during processing

### ✅ Multi-Sheet Support
- Upload workbooks with multiple sheets (Masterfile, Reval, etc.)
- Validate one sheet at a time
- Each sheet can be validated by different people
- All sheets preserved in output file

### ✅ Error Handling
- If worksheet inspection fails: Error message displayed (won't proceed)
- If validation fails: Error message shown (can retry)
- File upload issues: Clear error messages

---

## Common Scenarios

### Scenario 1: Single-Sheet Workbook
1. Upload file
2. Worksheet auto-selected → Summary displayed
3. Select validator → Start validation
4. Download result

### Scenario 2: Multi-Sheet Workbook (Masterfile + Reval)
1. Upload file
2. Choose "Masterfile" sheet → Summary shows 600 need validation
3. Select validator (e.g., Christian) → Start validation
4. Download result (both sheets preserved)
5. Upload same file again
6. Choose "Christian For Reval" sheet → Summary shows 100 need validation
7. Select validator → Start validation
8. Download result

### Scenario 3: Already Fully Validated Sheet
1. Upload file
2. Choose sheet → Summary shows "Needs Validation: 0"
3. Can still proceed (will just confirm existing data)
4. Download result with no changes (as expected)

---

## Technical Details

### API Endpoints Used

**Inspect Worksheets**
```
POST /api/ai-validation/inspect-worksheets
Request: multipart/form-data with 'file'
Response: {
  "worksheets": [
    {
      "name": "Masterfile",
      "total": 1000,
      "already_validated": 400,
      "needs_validation": 600,
      "is_working": true,
      "validated_by_counts": {"Christian": 200, "Asia": 150, "Nathan": 50}
    }
  ],
  "working_sheet": "Masterfile"
}
```

**Start Validation**
```
POST /api/ai-validation/start
Request: multipart/form-data with 'file', 'validator', 'worksheet'
Response: {"job_id": "user_timestamp_hash"}
```

**Progress Tracking**
```
GET /api/ai-validation/progress/{job_id}
Response: {
  "status": "completed",
  "processed": 600,
  "verified": 150,
  "partial": 450,
  "total": 600,
  ...
}
```

**Download Result**
```
GET /api/ai-validation/download/{job_id}
Response: Excel file (all worksheets preserved)
```

---

## Troubleshooting

### "No file selected" error
- Ensure you've chosen a file before clicking Start
- File must be .xlsx or .xlsm format

### "Please select a worksheet" error
- If multiple worksheets exist, click one to select it
- Single-sheet files should auto-select

### "Please select a validator" error
- Choose your name from the Validator dropdown
- Or enter a custom name if yours isn't listed

### Validation appears to stop (0 verified, 0 partial)
- This usually means all rows were already validated by others
- Check "Already Validated" count in summary
- This is correct behavior - validation is complete, nothing to change

### File downloaded but doesn't show changes
- Check that you selected the right worksheet
- Check "Needs Validation" count (if 0, nothing to change)
- Verify the validator name is yours in the output

---

## What Gets Validated/Updated

For each row that needs validation, the system:
1. Enriches data via People Data Labs API
2. Updates columns: Validated By, Validated Date, Validation Status
3. Adds Notes with what was found/skipped
4. Calculates Lead Ranking score
5. Preserves all existing: Company, First Name, Last Name, Title, Email, Phone, Website, Notes (appends only)

---

## Support

For issues or questions:
- Check the error message displayed (specific about what went wrong)
- Verify file format (.xlsx or .xlsm)
- Try uploading a smaller test file first
- Contact administrator if problems persist
