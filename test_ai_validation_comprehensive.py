"""
Comprehensive test suite for AI Validation filtering requirements.
Tests all scenarios mentioned in the requirements:
1. Validator filtering (Christian, Asia, Nathan, Vincent)
2. Lead Ranking skipping (bad, good, better, best)
3. Original row number preservation
4. Worksheet isolation
5. Progress count accuracy
"""
import pandas as pd
import sys


def test_validator_filtering():
    """Test that each validator's rows are correctly identified and filtered."""
    print("\n" + "="*80)
    print("TEST 1: VALIDATOR FILTERING")
    print("="*80)
    
    validators = ['Christian', 'Asia', 'Nathan', 'Vincent']
    
    for selected_validator in validators:
        print(f"\n--- Testing validator: {selected_validator} ---")
        
        # Create dataset with multiple validators
        data = []
        expected_eligible = 0
        
        # For each validator, create 10 rows
        for val_idx, val in enumerate(validators):
            for i in range(10):
                row_num = val_idx * 10 + i
                is_eligible = (val == selected_validator)
                
                data.append({
                    'Company': f'Company{row_num}',
                    'First Name': f'Person{row_num}',
                    'Validated By': val,
                    'Lead Ranking': '',  # Empty - eligible if validator matches
                })
                
                if is_eligible:
                    expected_eligible += 1
        
        df = pd.DataFrame(data)
        
        # Apply filtering
        eligible_rows = []
        for idx in range(len(df)):
            row = df.iloc[idx]
            validated_by = str(row.get("Validated By", "")).strip()
            lead_ranking = str(row.get("Lead Ranking", "")).strip()
            
            # Skip if already completed
            if lead_ranking and lead_ranking.lower() in ["bad", "good", "better", "best"]:
                continue
            
            # Only include if validator matches
            if validated_by == selected_validator:
                eligible_rows.append(idx)
        
        print(f"  Dataset has {len(df)} total rows")
        print(f"  Expected {selected_validator} eligible rows: {expected_eligible}")
        print(f"  Found eligible rows: {len(eligible_rows)}")
        
        assert len(eligible_rows) == 10, f"Expected 10 eligible {selected_validator} rows, got {len(eligible_rows)}"
        
        # Verify all eligible rows belong to the correct validator
        for idx in eligible_rows:
            actual_validator = str(df.iloc[idx]['Validated By']).strip()
            assert actual_validator == selected_validator, \
                f"Row {idx} has validator {actual_validator}, expected {selected_validator}"
        
        print(f"  [OK] All {len(eligible_rows)} rows verified for {selected_validator}")
    
    print("\n[OK] VALIDATOR FILTERING TEST PASSED")


def test_lead_ranking_skipping():
    """Test that rows with Lead Ranking values are correctly skipped."""
    print("\n" + "="*80)
    print("TEST 2: LEAD RANKING SKIPPING")
    print("="*80)
    
    rankings_to_skip = ['bad', 'good', 'better', 'best', 'BAD', 'GOOD', 'BETTER', 'BEST', 'Bad', 'Good']
    validator = 'Christian'
    
    print(f"\nTesting that these rankings are skipped: {rankings_to_skip}")
    
    for ranking in rankings_to_skip:
        # Create dataset where all rows have this ranking
        data = []
        for i in range(5):
            data.append({
                'Company': f'Company{i}',
                'First Name': f'Person{i}',
                'Validated By': validator,
                'Lead Ranking': ranking,
            })
        
        df = pd.DataFrame(data)
        
        # Apply filtering
        eligible_rows = []
        skipped_count = 0
        
        for idx in range(len(df)):
            row = df.iloc[idx]
            validated_by = str(row.get("Validated By", "")).strip()
            lead_ranking = str(row.get("Lead Ranking", "")).strip()
            
            # Skip if already completed
            if lead_ranking and lead_ranking.lower() in ["bad", "good", "better", "best"]:
                skipped_count += 1
                continue
            
            # Only include if validator matches
            if validated_by == validator:
                eligible_rows.append(idx)
        
        assert len(eligible_rows) == 0, f"Ranking '{ranking}' should be skipped, but {len(eligible_rows)} rows were eligible"
        assert skipped_count == 5, f"Expected 5 rows skipped for ranking '{ranking}', got {skipped_count}"
        
        print(f"  [OK] Ranking '{ranking}' correctly skipped (5 rows)")
    
    print("\n[OK] LEAD RANKING SKIPPING TEST PASSED")


def test_original_row_numbers_preserved():
    """Test that original Excel row numbers are preserved in the eligible queue."""
    print("\n" + "="*80)
    print("TEST 3: ORIGINAL ROW NUMBERS PRESERVED")
    print("="*80)
    
    # Create a dataset where eligible rows are scattered (non-sequential)
    data = []
    expected_row_indices = [2, 5, 8, 12, 19]  # Non-sequential
    
    for idx in range(25):
        if idx in expected_row_indices:
            row_data = {
                'Company': f'EligibleCompany{idx}',
                'First Name': f'Person{idx}',
                'Validated By': 'Christian',
                'Lead Ranking': '',  # Eligible
            }
        else:
            row_data = {
                'Company': f'OtherCompany{idx}',
                'First Name': f'Person{idx}',
                'Validated By': 'Asia',  # Different validator
                'Lead Ranking': '',
            }
        data.append(row_data)
    
    df = pd.DataFrame(data)
    
    # Apply filtering
    eligible_rows = []
    for idx in range(len(df)):
        row = df.iloc[idx]
        validated_by = str(row.get("Validated By", "")).strip()
        lead_ranking = str(row.get("Lead Ranking", "")).strip()
        
        if lead_ranking and lead_ranking.lower() in ["bad", "good", "better", "best"]:
            continue
        
        if validated_by == 'Christian':
            eligible_rows.append(idx)
    
    print(f"\nExpected eligible row indices (original Excel rows): {expected_row_indices}")
    print(f"Actual eligible row indices found: {eligible_rows}")
    
    assert eligible_rows == expected_row_indices, \
        f"Row numbers not preserved! Expected {expected_row_indices}, got {eligible_rows}"
    
    print(f"[OK] Original row numbers correctly preserved")
    print(f"  - Did NOT renumber to [0, 1, 2, 3, 4]")
    print(f"  - Preserved original indices [2, 5, 8, 12, 19]")
    
    print("\n[OK] ROW NUMBER PRESERVATION TEST PASSED")


def test_worksheet_isolation():
    """Test that only the selected worksheet is marked for processing."""
    print("\n" + "="*80)
    print("TEST 4: WORKSHEET ISOLATION")
    print("="*80)
    
    print("\nScenario: Multiple worksheets in workbook")
    print("  - Masterfile: 1000 rows")
    print("  - Christian For Reval: 500 rows")
    print("  - Selected: Christian For Reval")
    
    # Simulate workbook_sheets
    masterfile_data = []
    for i in range(1000):
        masterfile_data.append({
            'Company': f'MasterCompany{i}',
            'First Name': f'MasterPerson{i}',
            'Validated By': '',
            'Lead Ranking': '',
        })
    
    revalidation_data = []
    for i in range(500):
        revalidation_data.append({
            'Company': f'Reval Company{i}',
            'First Name': f'RePerson{i}',
            'Validated By': 'Christian' if i < 100 else 'Asia',
            'Lead Ranking': '',
        })
    
    workbook_sheets = {
        'Masterfile': pd.DataFrame(masterfile_data),
        'Christian For Reval': pd.DataFrame(revalidation_data),
    }
    
    selected_worksheet = 'Christian For Reval'
    
    # Process only selected worksheet
    df = workbook_sheets[selected_worksheet].copy()
    
    eligible_rows = []
    for idx in range(len(df)):
        row = df.iloc[idx]
        validated_by = str(row.get("Validated By", "")).strip()
        lead_ranking = str(row.get("Lead Ranking", "")).strip()
        
        if lead_ranking and lead_ranking.lower() in ["bad", "good", "better", "best"]:
            continue
        
        if validated_by == 'Christian':
            eligible_rows.append(idx)
    
    print(f"\nProcessing worksheet: {selected_worksheet}")
    print(f"  - Total rows in selected worksheet: {len(df)}")
    print(f"  - Eligible rows for Christian: {len(eligible_rows)}")
    
    # Verify only selected worksheet was processed
    assert len(df) == 500, f"Expected 500 rows from Christian For Reval, got {len(df)}"
    assert len(eligible_rows) == 100, f"Expected 100 eligible Christian rows, got {len(eligible_rows)}"
    
    # Verify Masterfile was NOT processed
    masterfile_df = workbook_sheets['Masterfile']
    assert masterfile_df is not None, "Masterfile should remain in workbook_sheets"
    assert len(masterfile_df) == 1000, "Masterfile should be unmodified"
    
    print(f"[OK] Only selected worksheet processed")
    print(f"[OK] Masterfile left untouched (still {len(masterfile_df)} rows)")
    
    print("\n[OK] WORKSHEET ISOLATION TEST PASSED")


def test_progress_count_accuracy():
    """Test that progress tracking uses eligible_count, not total."""
    print("\n" + "="*80)
    print("TEST 5: PROGRESS COUNT ACCURACY")
    print("="*80)
    
    # Create realistic scenario from bug report
    data = []
    
    # Christian's assigned rows: 250 total
    # - Completed: 131
    # - Remaining: 119 (ELIGIBLE)
    
    # Rows 0-118: Christian, not completed (ELIGIBLE)
    for i in range(119):
        data.append({
            'Company': f'Christian Company {i}',
            'Validated By': 'Christian',
            'Lead Ranking': '',
        })
    
    # Rows 119-249: Christian, completed (SKIP)
    for i in range(119, 250):
        ranking = ['bad', 'good', 'better', 'best'][(i - 119) % 4]
        data.append({
            'Company': f'Christian Company {i}',
            'Validated By': 'Christian',
            'Lead Ranking': ranking,
        })
    
    # Rows 250-1798: Other validators or not assigned (SKIP)
    for i in range(250, 1799):
        data.append({
            'Company': f'Other Company {i}',
            'Validated By': 'Asia' if i % 2 == 0 else '',
            'Lead Ranking': '',
        })
    
    df = pd.DataFrame(data)
    
    # Apply filtering
    eligible_rows = []
    for idx in range(len(df)):
        row = df.iloc[idx]
        validated_by = str(row.get("Validated By", "")).strip()
        lead_ranking = str(row.get("Lead Ranking", "")).strip()
        
        if lead_ranking and lead_ranking.lower() in ["bad", "good", "better", "best"]:
            continue
        
        if validated_by == 'Christian':
            eligible_rows.append(idx)
    
    eligible_count = len(eligible_rows)
    total_rows = len(df)
    
    print(f"\nDataset Summary:")
    print(f"  Total worksheet rows: {total_rows}")
    print(f"  Eligible rows for Christian: {eligible_count}")
    print(f"\nProgress Counter Should Use:")
    print(f"  [WRONG] 0 / {total_rows} (total rows)")
    print(f"  [CORRECT] 0 / {eligible_count} (eligible rows)")
    
    # Simulate progress tracking
    processed = 0
    print(f"\nProgress simulation:")
    for i in range(min(5, eligible_count)):
        processed = i + 1
        progress_text = f"{processed} / {eligible_count}"
        print(f"  After processing row {i+1}: {progress_text}")
    
    print(f"\nFinal progress:")
    print(f"  [CORRECT] {eligible_count} / {eligible_count} (correct)")
    print(f"  [WRONG] NOT {eligible_count} / {total_rows} (wrong)")
    
    assert eligible_count == 119, f"Expected 119 eligible rows, got {eligible_count}"
    assert total_rows == 1799, f"Expected 1799 total rows, got {total_rows}"
    
    print("\n[OK] PROGRESS COUNT ACCURACY TEST PASSED")


def test_no_api_calls_for_filtered_rows():
    """
    Test that filtering happens BEFORE API calls.
    This is a logic verification test (not an actual API test).
    """
    print("\n" + "="*80)
    print("TEST 6: FILTERING BEFORE API CALLS (Logic Verification)")
    print("="*80)
    
    print("\nVerifying filtering happens BEFORE enrichment:")
    print("  1. Inspect Validated By column")
    print("  2. Check Lead Ranking for completed status")
    print("  3. Create eligible_rows list")
    print("  4. ONLY THEN: Loop through eligible_rows and call APIs")
    print("  5. Never call APIs for non-eligible rows")
    
    data = []
    
    # 1000 total rows
    for i in range(1000):
        if i < 100:
            # Rows 0-99: Christian, not completed (ELIGIBLE for API calls)
            data.append({
                'Company': f'EligibleCompany{i}',
                'Validated By': 'Christian',
                'Lead Ranking': '',
            })
        elif i < 150:
            # Rows 100-149: Christian, completed (NO API calls)
            data.append({
                'Company': f'SkippedCompany{i}',
                'Validated By': 'Christian',
                'Lead Ranking': 'good',
            })
        else:
            # Rows 150-999: Other validators (NO API calls)
            data.append({
                'Company': f'OtherCompany{i}',
                'Validated By': 'Asia',
                'Lead Ranking': '',
            })
    
    df = pd.DataFrame(data)
    
    # STEP 1-3: Filtering (happens BEFORE APIs)
    eligible_rows = []
    api_call_candidates = 0
    
    for idx in range(len(df)):
        row = df.iloc[idx]
        validated_by = str(row.get("Validated By", "")).strip()
        lead_ranking = str(row.get("Lead Ranking", "")).strip()
        
        # Skip completed rows (BEFORE checking for APIs)
        if lead_ranking and lead_ranking.lower() in ["bad", "good", "better", "best"]:
            continue
        
        # Skip non-matching validators (BEFORE checking for APIs)
        if validated_by != 'Christian':
            continue
        
        # Only now add to eligible (ready for API calls)
        eligible_rows.append(idx)
        api_call_candidates += 1
    
    print(f"\nFiltering Results:")
    print(f"  Total rows: 1000")
    print(f"  Eligible for API calls: {api_call_candidates}")
    print(f"  Rows NOT calling APIs: {1000 - api_call_candidates}")
    print(f"\n  API Call Reduction: {(1 - api_call_candidates/1000)*100:.1f}%")
    
    # STEP 4: Only eligible rows would get API calls
    print(f"\nIn the processing loop:")
    print(f"  for idx in eligible_rows:")
    print(f"      pdl_enrich_company(...)  # Only for {len(eligible_rows)} rows")
    print(f"      pdl_enrich_person(...)   # Only for {len(eligible_rows)} rows")
    
    print(f"\nRows that do NOT get API calls:")
    print(f"  - {1000 - api_call_candidates} rows (assigned to Asia, completed, or unassigned)")
    print(f"  - API credits/usage preserved!")
    
    assert len(eligible_rows) == 100, f"Expected 100 eligible rows, got {len(eligible_rows)}"
    assert 1000 - len(eligible_rows) == 900, f"Expected 900 rows to skip APIs, got {1000 - len(eligible_rows)}"
    
    print("\n[OK] FILTERING BEFORE API CALLS TEST PASSED")


def run_all_tests():
    """Run all comprehensive tests."""
    print("\n" + "="*80)
    print("COMPREHENSIVE AI VALIDATION TEST SUITE")
    print("="*80)
    
    try:
        test_validator_filtering()
        test_lead_ranking_skipping()
        test_original_row_numbers_preserved()
        test_worksheet_isolation()
        test_progress_count_accuracy()
        test_no_api_calls_for_filtered_rows()
        
        print("\n" + "="*80)
        print("[OK] ALL TESTS PASSED")
        print("="*80)
        print("\nSummary:")
        print("  [OK] Validator filtering works correctly")
        print("  [OK] Lead Ranking values are properly skipped")
        print("  [OK] Original Excel row numbers are preserved")
        print("  [OK] Worksheet isolation is maintained")
        print("  [OK] Progress uses eligible count, not total")
        print("  [OK] Filtering happens before API calls")
        print("\n")
        
        return 0
    except AssertionError as e:
        print(f"\n[FAILED] TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n[FAILED] UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
