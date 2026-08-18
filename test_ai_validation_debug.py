"""
Test script to debug AI Validation workflow
Tests uploading an Excel file and calling the start validation endpoint
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, ai_validation_jobs
import tempfile
import pandas as pd

def test_ai_validation_workflow():
    """Test the AI validation workflow using Flask test client"""
    
    print("=" * 60)
    print("AI VALIDATION WORKFLOW DEBUG TEST")
    print("=" * 60)
    
    with app.app_context():
        client = app.test_client()
        
        # Step 1: Login
        print("\n[TEST] Step 1: Logging in as 'chan'...")
        response = client.post('/login', json={
            "username": "chan",
            "password": "chan123"
        })
        print(f"[TEST] Login response: {response.status_code}")
        print(f"[TEST] Response: {response.get_json()}")
        
        if response.status_code != 200:
            print("[TEST] Login failed, aborting")
            return
        
        # Step 2: Test validators endpoint
        print("\n[TEST] Step 2: Testing validators endpoint...")
        response = client.get('/api/ai-validation/validators')
        print(f"[TEST] Validators response: {response.status_code}")
        print(f"[TEST] Response: {response.get_json()}")
        
        # Step 3: Upload and test file
        print("\n[TEST] Step 3: Testing file upload...")
        
        test_file_path = r"c:\xampp\htdocs\crm\drafts\chan_Christian - Practice Validation for Interns_draft.xlsx"
        
        if not os.path.exists(test_file_path):
            print(f"[TEST] ERROR: Test file not found at {test_file_path}")
            return
        
        print(f"[TEST] Using test file: {test_file_path}")
        
        with open(test_file_path, 'rb') as f:
            data = {
                'file': (f, 'test.xlsx'),
                'validator': 'TestValidator'
            }
            
            print("[TEST] Sending POST to /api/ai-validation/start...")
            response = client.post(
                '/api/ai-validation/start',
                data=data,
                content_type='multipart/form-data'
            )
        
        print(f"[TEST] Response status: {response.status_code}")
        response_data = response.get_json()
        print(f"[TEST] Response: {response_data}")
        
        if response.status_code == 200 and 'job_id' in response_data:
            job_id = response_data['job_id']
            print(f"[TEST] SUCCESS: Job ID: {job_id}")
            
            # Step 4: Check job status
            print("\n[TEST] Step 4: Checking job status...")
            import time
            for i in range(5):
                time.sleep(1)
                job_response = client.get(f'/api/ai-validation/progress/{job_id}')
                job_data = job_response.get_json()
                print(f"[TEST] Poll {i+1}: status={job_data.get('status')}, processed={job_data.get('processed')}/{job_data.get('total')}")
                
                if job_data.get('status') == 'completed':
                    print(f"[TEST] Job completed!")
                    print(f"[TEST] Final stats: Verified={job_data.get('verified')}, Partial={job_data.get('partial')}, Not Found={job_data.get('not_found')}, Errors={job_data.get('errors')}")
                    break
        else:
            print(f"[TEST] FAILED: {response_data}")
        
        print("\n[TEST] Test complete!")

if __name__ == "__main__":
    test_ai_validation_workflow()
