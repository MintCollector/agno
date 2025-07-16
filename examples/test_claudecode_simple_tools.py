#!/usr/bin/env python3
"""Simple test of ClaudeCode with built-in Claude Code tools"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agno', 'libs', 'agno'))

from agno.agent import Agent
from agno.models.claudecode import ClaudeCode

def test_claudecode_builtin_tools():
    """Test ClaudeCode with Claude Code's built-in tools"""
    print("Creating ClaudeCode agent with built-in tools...")
    
    # Create agent with Claude Code's built-in tools
    agent = Agent(
        model=ClaudeCode(
            allowed_tools=["Read", "Write"],  # Use Claude Code's built-in tools
            permission_mode="acceptEdits",  # Auto-accept file edits
            cwd=os.getcwd(),  # Set working directory
            system_prompt="You are a helpful assistant that can read and write files using your built-in tools."
        ),
        # No agno tools needed - Claude Code has its own
        instructions="Use your built-in file tools to complete tasks.",
        markdown=True,
    )
    
    print("\nAsking agent to create a test file...")
    response = agent.run("""
    Please create a file called 'test_from_claudecode.txt' with the content:
    'This file was created by Claude Code using its built-in tools!'
    """)
    
    print(f"\nAgent response:\n{response.content}")
    
    # Check if file was created
    if os.path.exists("test_from_claudecode.txt"):
        print("\n✅ File was created successfully!")
        with open("test_from_claudecode.txt", "r") as f:
            content = f.read()
            print(f"File content: {content}")
        # Clean up
        os.remove("test_from_claudecode.txt")
        return True
    else:
        print("\n❌ File was not created.")
        return False

if __name__ == "__main__":
    print("Testing ClaudeCode with built-in tools...")
    print("=" * 50)
    
    success = test_claudecode_builtin_tools()
    
    print("\n" + "=" * 50)
    print(f"\nTest result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    exit(0 if success else 1)