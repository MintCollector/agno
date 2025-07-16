#!/usr/bin/env python3
"""Test using ClaudeCode (local Claude) instead of API calls"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agno', 'libs', 'agno'))

from agno.agent import Agent
from agno.models.claudecode import ClaudeCode

def test_claudecode_arithmetic():
    """Test that a ClaudeCode agent can add 2+2"""
    print("Creating ClaudeCode agent (using local Claude)...")
    
    agent = Agent(
        model=ClaudeCode(),
        instructions="You are a helpful assistant that can perform basic arithmetic. Answer only with the number result.",
        markdown=False,
    )
    
    print("Asking agent to calculate 2+2...")
    response = agent.run("What is 2+2?")
    
    print(f"Agent response: {response.content}")
    
    # Check if the response contains the correct answer
    if "4" in response.content.strip():
        print("✅ Test passed! ClaudeCode correctly calculated 2+2 = 4")
        return True
    else:
        print(f"❌ Test failed! Expected '4' but got: {response.content}")
        return False

if __name__ == "__main__":
    print("Starting ClaudeCode agent test...")
    print("This uses your local Claude Code CLI instead of API calls!")
    success = test_claudecode_arithmetic()
    exit(0 if success else 1)