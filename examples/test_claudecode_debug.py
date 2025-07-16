#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agno', 'libs', 'agno'))

from agno.agent import Agent
from agno.models.claudecode import ClaudeCode

def test_claudecode_debug():
    print("Debugging ClaudeCode response structure...")
    
    # Create agent with ClaudeCode
    agent = Agent(
        model=ClaudeCode(),
        instructions="You are a helpful assistant.",
    )
    
    print("Asking simple question...")
    response = agent.run("What is 5 + 3?")
    
    print(f"Response type: {type(response)}")
    print(f"Response attributes: {dir(response)}")
    
    # Check what's in the response
    if hasattr(response, 'usage'):
        print(f"response.usage: {response.usage}")
    if hasattr(response, 'response_usage'):
        print(f"response.response_usage: {response.response_usage}")
    if hasattr(response, 'provider_data'):
        print(f"response.provider_data: {response.provider_data}")
    if hasattr(response, 'response'):
        print(f"response.response type: {type(response.response)}")
        if hasattr(response.response, 'usage'):
            print(f"response.response.usage: {response.response.usage}")
        if hasattr(response.response, 'response_usage'):
            print(f"response.response.response_usage: {response.response.response_usage}")
    
    print("✅ Debug completed!")

if __name__ == "__main__":
    test_claudecode_debug()