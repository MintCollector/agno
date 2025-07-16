#!/usr/bin/env python3

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agno', 'libs', 'agno'))

from agno.models.claudecode import ClaudeCode
from agno.models.message import Message

def test_claudecode_raw():
    print("Testing ClaudeCode raw model response...")
    
    # Create ClaudeCode model directly
    model = ClaudeCode()
    
    # Create a simple message
    messages = [
        Message(role="user", content="What is 9 + 6?")
    ]
    
    print("Calling model directly...")
    raw_response = model.invoke(messages)
    
    print(f"Raw response type: {type(raw_response)}")
    print(f"Raw response: {json.dumps(raw_response, indent=2)}")
    
    # Parse it through the model's parser
    print("\n=== Parsing through model ===")
    parsed_response = model.parse_provider_response(raw_response)
    
    print(f"Parsed response type: {type(parsed_response)}")
    print(f"Parsed content: {parsed_response.content}")
    print(f"Parsed response_usage: {parsed_response.response_usage}")
    print(f"Parsed provider_data keys: {list(parsed_response.provider_data.keys()) if parsed_response.provider_data else None}")
    
    if parsed_response.provider_data and 'usage' in parsed_response.provider_data:
        print(f"Provider data usage: {parsed_response.provider_data['usage']}")
    
    print("✅ Raw model test completed!")

if __name__ == "__main__":
    test_claudecode_raw()