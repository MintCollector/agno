#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agno', 'libs', 'agno'))

from agno.agent import Agent
from agno.models.claudecode import ClaudeCode

def test_claudecode_usage():
    print("Testing ClaudeCode usage data...")
    
    # Create agent with ClaudeCode
    agent = Agent(
        model=ClaudeCode(),
        instructions="You are a helpful assistant. Provide detailed responses.",
        markdown=True,
        show_tool_calls=True
    )
    
    # Test with a longer prompt to get more usage data
    prompt = """
    Please write a short story about a robot who learns to paint. 
    The story should be about 200 words and include themes of creativity and self-discovery.
    """
    
    print("Asking for a creative writing task...")
    response = agent.run(prompt)
    
    print(f"Response: {response.content[:100]}...")
    
    # Check if we have usage data
    if hasattr(response, 'usage') and response.usage:
        print(f"✅ Usage data found: {response.usage}")
    else:
        print("❌ No usage data found")
        
    # Check if response model has usage
    if hasattr(response, 'response') and hasattr(response.response, 'usage'):
        print(f"✅ Response model usage: {response.response.usage}")
    else:
        print("❌ No response model usage found")
        
    print("✅ Usage test completed!")

if __name__ == "__main__":
    test_claudecode_usage()