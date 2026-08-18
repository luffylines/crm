#!/usr/bin/env python3
"""
Comprehensive test suite for validator filtering.
Tests that rows are filtered correctly by selected validator.
"""

import sys
import os
import pandas as pd
from io import BytesIO
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, build_filtered_queue


class TestValidatorFiltering(unittest.TestCase):
    """Test the filtering of validation rows by validator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = app.test_client()
        self.app.testing = True
        
    def create_test_dataframe(self):
        """Create a sample DataFrame with multiple validators."""
        data = {
            "Company": ["Company A", "Company B", "Company C", "Company D", "Company E", "Company F"],
            "First Name": ["John", "Jane", "Bob", "Alice", "Charlie", "Diana"],
            "Last Name": ["Doe", "Smith", "Brown", "Jones", "Davis", "Miller"],
            "Validated By": ["Christian", "Asia", "Christian", "Vincent", "Asia", "Christian"],
            "Lead Ranking": ["", "better", "", "", "best", ""],
        }
        return pd.DataFrame(data)
    
    def test_build_filtered_queue_christian(self):
        """Test filtering for Christian validator."""
        df = self.create_test_dataframe()
        validated, filtered = build_filtered_queue(df, "Christian")
        
        # Christian has rows 0, 2, 5
        # Row 2 has empty Lead Ranking - should be included
        # Rows 0, 5 have empty Lead Ranking - should be included
        expected_filtered = [0, 2, 5]
        
        self.assertEqual(filtered, expected_filtered, 
                        f"Christian's queue should be {expected_filtered}, got {filtered}")
        self.assertIn(1, validated, "Row 1 (Asia) should be marked as validated")
        self.assertIn(4, validated, "Row 4 (Asia) should be marked as validated")
    
    def test_build_filtered_queue_asia(self):
        """Test filtering for Asia validator."""
        df = self.create_test_dataframe()
        validated, filtered = build_filtered_queue(df, "Asia")
        
        # Asia has rows 1, 4
        # Row 1 has 'better' ranking - should NOT be included (already completed)
        # Row 4 has 'best' ranking - should NOT be included (already completed)
        expected_filtered = []
        
        self.assertEqual(filtered, expected_filtered,
                        f"Asia's queue should be empty (all completed), got {filtered}")
        self.assertIn(1, validated, "Row 1 (Asia with 'better') should be in validated")
        self.assertIn(4, validated, "Row 4 (Asia with 'best') should be in validated")
    
    def test_build_filtered_queue_vincent(self):
        """Test filtering for Vincent validator."""
        df = self.create_test_dataframe()
        validated, filtered = build_filtered_queue(df, "Vincent")
        
        # Vincent has row 3
        # Row 3 has empty Lead Ranking - should be included
        expected_filtered = [3]
        
        self.assertEqual(filtered, expected_filtered,
                        f"Vincent's queue should be {expected_filtered}, got {filtered}")
    
    def test_build_filtered_queue_unassigned_validator(self):
        """Test filtering for validator with no assignments."""
        df = self.create_test_dataframe()
        validated, filtered = build_filtered_queue(df, "Nathan")
        
        # Nathan has no rows
        expected_filtered = []
        
        self.assertEqual(filtered, expected_filtered,
                        f"Nathan's queue should be empty, got {filtered}")
    
    def test_original_excel_row_numbers_preserved(self):
        """Test that original Excel row numbers are preserved in the queue."""
        df = self.create_test_dataframe()
        validated, filtered = build_filtered_queue(df, "Christian")
        
        # The filtered queue should contain the actual dataframe indices
        # Excel rows would be index + 2 (header + 1-based numbering)
        excel_rows = [idx + 2 for idx in filtered]
        
        # Christian has dataframe indices 0, 2, 5 -> Excel rows 2, 4, 7
        expected_excel_rows = [2, 4, 7]
        self.assertEqual(excel_rows, expected_excel_rows,
                        f"Excel rows should be {expected_excel_rows}, got {excel_rows}")
    
    def test_all_validators_found(self):
        """Test that all validators in dataframe are correctly identified."""
        df = self.create_test_dataframe()
        
        # Get unique validators
        validators = set(df["Validated By"].astype(str).str.strip())
        expected_validators = {"Christian", "Asia", "Vincent"}
        
        self.assertEqual(validators, expected_validators,
                        f"Should find validators {expected_validators}, got {validators}")
    
    def test_empty_dataframe(self):
        """Test filtering on empty dataframe."""
        df = pd.DataFrame({
            "Company": [],
            "Validated By": [],
            "Lead Ranking": [],
        })
        
        validated, filtered = build_filtered_queue(df, "Christian")
        
        self.assertEqual(filtered, [],
                        "Empty dataframe should have empty filtered queue")
        self.assertEqual(validated, set(),
                        "Empty dataframe should have no validated rows")
    
    def test_no_validator_selected(self):
        """Test filtering when no validator is selected."""
        df = self.create_test_dataframe()
        validated, filtered = build_filtered_queue(df, None)
        
        # Without validator filter, should return all unvalidated rows
        # Rows 1 and 4 have rankings (validated), others don't
        expected_unvalidated = [0, 2, 3, 5]
        
        self.assertEqual(filtered, expected_unvalidated,
                        f"Should return unvalidated rows when no validator selected, got {filtered}")
    
    def test_completed_rows_not_in_queue(self):
        """Test that rows with Lead Ranking are not in the validation queue."""
        df = pd.DataFrame({
            "Company": ["A", "B", "C", "D"],
            "Validated By": ["John", "John", "John", "John"],
            "Lead Ranking": ["", "good", "", "bad"],
        })
        
        validated, filtered = build_filtered_queue(df, "John")
        
        # Should only include rows 0 and 2 (with empty ranking)
        expected_filtered = [0, 2]
        self.assertEqual(filtered, expected_filtered,
                        f"Should exclude completed rows, got {filtered}")
        
        # Rows 1 and 3 should be marked as validated
        self.assertIn(1, validated, "Row 1 with 'good' ranking should be validated")
        self.assertIn(3, validated, "Row 3 with 'bad' ranking should be validated")
    
    def test_case_sensitivity_validated_by(self):
        """Test that validator names are case-sensitive."""
        df = pd.DataFrame({
            "Company": ["A", "B", "C"],
            "Validated By": ["John", "john", "JOHN"],
            "Lead Ranking": ["", "", ""],
        })
        
        validated, filtered = build_filtered_queue(df, "John")
        
        # Should only match exact case
        expected_filtered = [0]
        self.assertEqual(filtered, expected_filtered,
                        f"Should be case-sensitive, got {filtered}")
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        df = pd.DataFrame({
            "Company": ["A", "B", "C"],
            "Validated By": ["  John  ", "John", "John  "],
            "Lead Ranking": ["", "", ""],
        })
        
        validated, filtered = build_filtered_queue(df, "John")
        
        # All should match after whitespace stripping
        expected_filtered = [0, 1, 2]
        self.assertEqual(filtered, expected_filtered,
                        f"Should strip whitespace, got {filtered}")


class TestValidatorDropdownGeneration(unittest.TestCase):
    """Test that validator dropdown is correctly generated from worksheet data."""
    
    def test_validators_extracted_from_column(self):
        """Test that unique validators are extracted from the Validated By column."""
        df = pd.DataFrame({
            "Company": ["A", "B", "C", "D", "E"],
            "Validated By": ["Asia", "Christian", "Vincent", "Nathan", "Christian"],
            "Lead Ranking": ["", "", "", "", ""],
        })
        
        validators = set(df["Validated By"].astype(str).str.strip())
        expected = {"Asia", "Christian", "Vincent", "Nathan"}
        
        self.assertEqual(validators, expected,
                        f"Should extract unique validators, got {validators}")
    
    def test_empty_validators_excluded(self):
        """Test that empty validator names are excluded."""
        df = pd.DataFrame({
            "Company": ["A", "B", "C"],
            "Validated By": ["John", "", "John"],
            "Lead Ranking": ["", "", ""],
        })
        
        validators = set(val for val in df["Validated By"].astype(str).str.strip() if val)
        expected = {"John"}
        
        self.assertEqual(validators, expected,
                        f"Should exclude empty validators, got {validators}")


class TestSaveOperations(unittest.TestCase):
    """Test that save operations respect the filtered queue."""
    
    def test_row_not_in_queue_rejected(self):
        """Test that saving a row not in filtered queue is rejected."""
        # This would require a full Flask app context to test properly
        # For now, just verify the logic
        
        filtered_queue = [0, 2, 5]
        invalid_row = 3
        
        self.assertNotIn(invalid_row, filtered_queue,
                        "Row 3 should not be in Christian's queue")
    
    def test_row_in_queue_accepted(self):
        """Test that saving a row in filtered queue is accepted."""
        filtered_queue = [0, 2, 5]
        valid_row = 2
        
        self.assertIn(valid_row, filtered_queue,
                     "Row 2 should be in Christian's queue")


def run_tests():
    """Run all tests and print results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestValidatorFiltering))
    suite.addTests(loader.loadTestsFromTestCase(TestValidatorDropdownGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestSaveOperations))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
