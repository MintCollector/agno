#!/usr/bin/env python3

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agno', 'libs', 'agno'))

from agno.agent import Agent
from agno.models.claudecode import ClaudeCode

def test_claudecode_json():
    print("Testing ClaudeCode JSON response structure...")
    
    # Create agent with ClaudeCode
    agent = Agent(
        model=ClaudeCode(),
        instructions="You are a helpful assistant.",
    )
    
    print("Asking simple question...")
    response = agent.run("What is 7 + 8?")
    
    print(f"Response content: {response.content}")
    
    # Convert to JSON
    response_json = response.to_json()
    response_dict = json.loads(response_json)
    
    print("\n=== JSON Structure ===")
    print(json.dumps(response_dict, indent=2))
    
    # Look specifically for usage data
    print("\n=== Usage Data Analysis ===")
    if 'usage' in response_dict:
        print(f"Found usage in JSON: {response_dict['usage']}")
    else:
        print("No 'usage' field in JSON")
        
    if 'response_usage' in response_dict:
        print(f"Found response_usage in JSON: {response_dict['response_usage']}")
    else:
        print("No 'response_usage' field in JSON")
        
    if 'extra_data' in response_dict:
        print(f"Found extra_data in JSON: {response_dict['extra_data']}")
    else:
        print("No 'extra_data' field in JSON")
        
    if 'metrics' in response_dict and response_dict['metrics']:
        print(f"Found metrics in JSON: {response_dict['metrics']}")
    else:
        print("No 'metrics' field in JSON")
    
    print("✅ JSON analysis completed!")

if __name__ == "__main__":
    test_claudecode_json()