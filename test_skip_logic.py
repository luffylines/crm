#!/usr/bin/env python3
"""
Test skip logic for company enrichment - Verify existing data is preserved.
"""

import sys
sys.path.insert(0, '/xampp/htdocs/crm')

from app import is_field_empty, check_missing_enrichment_fields

def test_is_field_empty():
    """Test the is_field_empty function."""
    print("\n" + "="*60)
    print("Testing is_field_empty()")
    print("="*60)
    
    test_cases = [
        (None, True, "None"),
        ("", True, "Empty string"),
        ("   ", True, "Whitespace only"),
        ("nan", True, "Lowercase 'nan'"),
        ("NaN", True, "Mixed case 'NaN'"),
        ("NAN", True, "Uppercase 'NAN'"),
        ("NA", False, "NA (should NOT be empty)"),
        ("Not Available", False, "Text starting with N"),
        ("0", False, "Zero as string"),
        ("Company Name", False, "Normal text"),
        ("51-200", False, "Range"),
    ]
    
    passed = 0
    failed = 0
    
    for value, expected, description in test_cases:
        result = is_field_empty(value)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status}: is_field_empty({repr(value):20}) = {result:5} | Expected: {expected:5} | {description}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_check_missing_enrichment_fields():
    """Test the check_missing_enrichment_fields function."""
    print("\n" + "="*60)
    print("Testing check_missing_enrichment_fields()")
    print("="*60)
    
    test_cases = [
        # (row_dict, expected_result, description)
        (
            {
                "About Company": "Existing description",
                "No. of Employees": "51-200",
                "Company Industry": "Technology"
            },
            {"about": False, "industry": False, "employees": False, "needs_enrichment": False},
            "All fields populated"
        ),
        (
            {
                "About Company": "",
                "No. of Employees": "11-50",
                "Company Industry": ""
            },
            {"about": True, "industry": True, "employees": False, "needs_enrichment": True},
            "About and Industry empty, Employees filled"
        ),
        (
            {
                "About Company": "",
                "No. of Employees": "",
                "Company Industry": ""
            },
            {"about": True, "industry": True, "employees": True, "needs_enrichment": True},
            "All fields empty"
        ),
        (
            {
                "About Company": "   ",
                "No. of Employees": "nan",
                "Company Industry": None
            },
            {"about": True, "industry": True, "employees": True, "needs_enrichment": True},
            "All fields with whitespace/nan/None"
        ),
        (
            {
                "About Company": "A Company",
                "No. of Employees": "100",
                "Company Industry": "Finance"
            },
            {"about": False, "industry": False, "employees": False, "needs_enrichment": False},
            "All fields populated with real data"
        ),
        (
            {
                "About Company": "NA",
                "No. of Employees": "",
                "Company Industry": "Tech"
            },
            {"about": False, "industry": False, "employees": True, "needs_enrichment": True},
            "NA not treated as empty, others populated"
        ),
    ]
    
    passed = 0
    failed = 0
    
    for row, expected, description in test_cases:
        result = check_missing_enrichment_fields(row)
        result_matches = (
            result["about"] == expected["about"] and
            result["industry"] == expected["industry"] and
            result["employees"] == expected["employees"] and
            result["needs_enrichment"] == expected["needs_enrichment"]
        )
        status = "✓ PASS" if result_matches else "✗ FAIL"
        if result_matches:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status}: {description}")
        print(f"  Result:   {result}")
        print(f"  Expected: {expected}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all tests."""
    print("\n" + "█"*60)
    print("  SKIP LOGIC TEST SUITE")
    print("█"*60)
    
    test1_pass = test_is_field_empty()
    test2_pass = test_check_missing_enrichment_fields()
    
    print("\n" + "█"*60)
    if test1_pass and test2_pass:
        print("  ✓ ALL TESTS PASSED")
        print("█"*60 + "\n")
        return 0
    else:
        print("  ✗ SOME TESTS FAILED")
        print("█"*60 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
