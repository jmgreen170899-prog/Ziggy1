"""Debug script for memory module."""

import os
import tempfile


# Set test environment before importing memory module
test_dir = tempfile.mkdtemp()
test_file = os.path.join(test_dir, "debug_test.jsonl")
os.environ["MEMORY_PATH"] = test_file
os.environ["MEMORY_MODE"] = "JSONL"

print(f"Test file path: {test_file}")
print(f"MEMORY_PATH env: {os.getenv('MEMORY_PATH')}")
print(f"MEMORY_MODE env: {os.getenv('MEMORY_MODE')}")

# Import after setting environment
from app.memory.events import JSONL_PATH, MODE, append_event


print(f"Module JSONL_PATH: {JSONL_PATH}")
print(f"Module MODE: {MODE}")

# Test basic append
event_data = {"ticker": "TEST", "p_up": 0.5, "decision": "BUY"}

try:
    event_id = append_event(event_data)
    print(f"Event ID: {event_id}")
    print(f"File exists: {os.path.exists(test_file)}")

    if os.path.exists(test_file):
        with open(test_file) as f:
            content = f.read()
            print(f"File content: {content}")
    else:
        print("File was not created")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()

# Cleanup
import shutil


shutil.rmtree(test_dir, ignore_errors=True)
