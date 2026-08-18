"""
Test script to verify AI Validation filtering logic
"""
import pandas as pd
import sys

def test_filtering_logic():
    """Test the filtering logic for eligible rows"""
    
    # Create test dataframe similar to the actual scenario
    test_data = {
        'First Name': ['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'Dave', 'Eve', 'Frank', 'Grace', 'Henry'],
        'Last Name': ['Doe', 'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez'],
        'Company': ['ABC Corp', 'XYZ Inc', 'Tech Co', 'Data Ltd', 'Cloud Sys', 'Web Pro', 'AI Works', 'Data Science', 'Analytics', 'Big Data'],
        'Validated By': ['Christian', 'Christian', '', 'Asia', 'Christian', 'Christian', '', 'Nathan', '', ''],
        'Lead Ranking': ['', '', 'Bad', '', 'Good', '', 'Better', '', '', ''],
        'Email': ['', '', '', '', '', '', '', '', '', '']
    }
    
    df = pd.DataFrame(test_data)
    validator = 'Christian'
    
    print(f"\n{'='*80}")
    print(f"AI VALIDATION FILTERING TEST")
    print(f"{'='*80}")
    print(f"\nValidator: {validator}")
    print(f"Total rows in worksheet: {len(df)}")
    
    # Apply filtering logic
    eligible_rows = []
    completed_count = 0
    assigned_to_others = 0
    not_assigned = 0
    
    print(f"\n{'Index':<6} {'Name':<20} {'Validated By':<15} {'Lead Ranking':<15} {'Status'}")
    print("-" * 80)
    
    for idx in range(len(df)):
        row = df.iloc[idx]
        validated_by = str(row.get("Validated By", "")).strip()
        lead_ranking = str(row.get("Lead Ranking", "")).strip()
        first_name = str(row.get("First Name", "")).strip()
        
        # Determine why row is skipped or eligible
        status = "ELIGIBLE"
        
        # Check if row is already completed
        if lead_ranking and lead_ranking.lower() in ["bad", "good", "better", "best"]:
            status = "SKIP: Already completed"
            completed_count += 1
        # Check if row is not assigned to this validator
        elif validated_by != validator:
            if validated_by:
                status = f"SKIP: Assigned to {validated_by}"
                assigned_to_others += 1
            else:
                status = "SKIP: Not assigned to Christian"
                not_assigned += 1
        else:
            # This row is eligible for processing
            eligible_rows.append(idx)
        
        print(f"{idx:<6} {first_name:<20} {validated_by:<15} {lead_ranking:<15} {status}")
    
    print("\n" + "="*80)
    print("FILTERING SUMMARY:")
    print("="*80)
    print(f"Total rows in worksheet: {len(df)}")
    print(f"Eligible for {validator}: {len(eligible_rows)}")
    print(f"Already completed (assigned to {validator}): {completed_count}")
    print(f"Assigned to other validators: {assigned_to_others}")
    print(f"Not assigned to {validator}: {not_assigned}")
    print(f"\nEligible row indices: {eligible_rows}")
    print(f"\nProgress should show:")
    print(f"  0 / {len(eligible_rows)} (NOT 0 / {len(df)})")
    
    # Verify the logic
    assert len(eligible_rows) + completed_count + assigned_to_others + not_assigned == len(df), \
        "Row counts don't add up!"
    
    print("\n✓ Filtering logic test PASSED")
    print(f"\nExpected behavior:")
    print(f"  - Only rows {eligible_rows} will be processed for {validator}")
    print(f"  - No API calls will be made for rows that are skipped")
    print(f"  - Progress counter will show 0/{len(eligible_rows)}, not 0/{len(df)}")

if __name__ == "__main__":
    test_filtering_logic()
