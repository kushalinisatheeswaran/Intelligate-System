import requests
import json

url = "http://127.0.0.1:5050/api/verify"

# Test 1: Verify barcode type
payload1 = {
    "type": "barcode",
    "value": "113688",
    "direction": "entry",
    "device_id": "test_cam"
}

# Test 2: Verify student_id type (synonym)
payload2 = {
    "type": "student_id",
    "value": "113658",
    "direction": "entry",
    "device_id": "test_cam"
}

headers = {"Content-Type": "application/json"}

try:
    print("Testing type: barcode")
    r1 = requests.post(url, json=payload1, headers=headers)
    print("Response:", r1.status_code, r1.json())
    
    print("\nTesting type: student_id")
    r2 = requests.post(url, json=payload2, headers=headers)
    print("Response:", r2.status_code, r2.json())
except Exception as e:
    print("Verification failed:", e)
