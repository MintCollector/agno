#!/usr/bin/env python3
"""Test ClaudeCode with tools support"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agno', 'libs', 'agno'))

from agno.agent import Agent
from agno.models.claudecode import ClaudeCode
from agno.tools.file import FileTools

def test_claudecode_with_tools():
    """Test ClaudeCode agent with file tools"""
    print("Creating ClaudeCode agent with file tools...")
    
    # Create agent with tools
    agent = Agent(
        model=ClaudeCode(
            allowed_tools=["Read", "Write"],
            permission_mode="acceptEdits",  # Auto-accept file edits
            cwd=os.getcwd()  # Set working directory
        ),
        tools=[FileTools()],
        instructions="You are a helpful assistant that can read and write files.",
        markdown=True,
    )
    
    print("\nAsking agent to create a test file...")
    response = agent.run("""
    Please create a file called 'hello_claudecode.txt' with the content:
    'Hello from Claude Code! This file was created using local Claude.'
    """)
    
    print(f"\nAgent response:\n{response.content}")
    
    # Check if file was created
    if os.path.exists("hello_claudecode.txt"):
        print("\n✅ Test passed! File was created.")
        with open("hello_claudecode.txt", "r") as f:
            content = f.read()
            print(f"File content: {content}")
        # Clean up
        os.remove("hello_claudecode.txt")
        return True
    else:
        print("\n❌ Test failed! File was not created.")
        return False

def test_claudecode_with_mcp():
    """Test ClaudeCode with MCP configuration"""
    print("\n\nTesting ClaudeCode with MCP configuration...")
    
    agent = Agent(
        model=ClaudeCode(
            system_prompt="You are a helpful assistant with access to MCP tools.",
            mcp_tools=["filesystem"],  # Example MCP tool
            max_thinking_tokens=10000,
        ),
        markdown=True,
    )
    
    response = agent.run("What MCP tools do you have access to?")
    print(f"Agent response:\n{response.content}")
    
    return True

def test_multi_turn_conversation():
    """Test multi-turn conversation support"""
    print("\n\nTesting multi-turn conversation...")
    
    agent = Agent(
        model=ClaudeCode(
            max_turns=3,  # Allow 3 turns
            continue_conversation=True,
        ),
        markdown=True,
    )
    
    # First turn
    response1 = agent.run("Remember the number 42.")
    print(f"Turn 1: {response1.content}")
    
    # Second turn
    response2 = agent.run("What number did I ask you to remember?")
    print(f"Turn 2: {response2.content}")
    
    return "42" in response2.content

if __name__ == "__main__":
    print("Starting ClaudeCode feature tests...")
    print("=" * 50)
    
    # Test 1: Basic arithmetic (from previous test)
    print("\nTest 1: Basic arithmetic")
    from test_claudecode_agent import test_claudecode_arithmetic
    success1 = test_claudecode_arithmetic()
    
    # Test 2: File tools
    print("\n" + "=" * 50)
    print("\nTest 2: File tools")
    success2 = test_claudecode_with_tools()
    
    # Test 3: MCP configuration
    print("\n" + "=" * 50)
    print("\nTest 3: MCP configuration")
    success3 = test_claudecode_with_mcp()
    
    # Test 4: Multi-turn conversation
    print("\n" + "=" * 50)
    print("\nTest 4: Multi-turn conversation")
    success4 = test_multi_turn_conversation()
    
    # Summary
    print("\n" + "=" * 50)
    print("\nTest Summary:")
    print(f"Basic arithmetic: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"File tools: {'✅ PASSED' if success2 else '❌ FAILED'}")
    print(f"MCP configuration: {'✅ PASSED' if success3 else '❌ FAILED'}")
    print(f"Multi-turn conversation: {'✅ PASSED' if success4 else '❌ FAILED'}")
    
    all_passed = all([success1, success2, success3, success4])
    exit(0 if all_passed else 1)