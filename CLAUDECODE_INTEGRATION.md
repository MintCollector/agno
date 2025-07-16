# ClaudeCode Integration for Agno

This document describes the integration of Claude Code (local Claude) support into the agno framework, allowing users to use their local Claude Code instance instead of making API calls to Anthropic.

## Overview

The ClaudeCode model provides a way to use agno with your local Claude Code installation, eliminating the need for API keys and internet connectivity for LLM operations. It uses the official `claude-code-sdk` Python package to communicate with Claude Code running on your machine.

## What Was Done

### 1. Added claude-code-sdk Dependency

Modified `/agno/libs/agno/pyproject.toml`:
- Added `claudecode = ["claude-code-sdk"]` to optional dependencies
- Added `"agno[claudecode]"` to the models group

### 2. Created ClaudeCode Model Implementation

Created `/agno/libs/agno/agno/models/claudecode.py` with:
- Full implementation following agno's Model interface
- Support for Claude Code SDK features
- Tool support for Claude Code's built-in tools
- MCP server configuration support
- Multi-turn conversation capabilities

### 3. Updated Model Exports

Modified `/agno/libs/agno/agno/models/__init__.py`:
- Added ClaudeCode to the exports

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│ agno Agent  │ --> │ ClaudeCode   │ --> │ claude-code-sdk │ --> │ Claude Code  │
│             │     │ Model        │     │ Python package  │     │ CLI (local)  │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────┘
```

### Key Differences from API Version

| Feature | Anthropic API | ClaudeCode |
|---------|--------------|------------|
| API Key | Required | Not needed |
| Network | HTTP calls | Local IPC |
| Tools | agno tools | Claude Code built-in tools |
| Streaming | Full support | Basic support |
| Images/Audio | Supported | Not supported |
| Caching | Supported | Not supported |
| Cost | Per token | Free (local) |

## Installation

1. Install Claude Code CLI:
```bash
npm install -g @anthropic-ai/claude-code
```

2. Install agno with claudecode support:
```bash
pip install agno[claudecode]
# or if installing from local development:
pip install -e "libs/agno[claudecode]"
```

## Usage Examples

### Basic Usage

```python
from agno.agent import Agent
from agno.models.claudecode import ClaudeCode

# Create a simple agent
agent = Agent(
    model=ClaudeCode(),
    instructions="You are a helpful assistant.",
)

response = agent.run("What is 2+2?")
print(response.content)
```

### With Built-in Tools

```python
agent = Agent(
    model=ClaudeCode(
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits",  # Auto-accept file edits
        cwd="/path/to/project"
    ),
    instructions="You can read, write files and run commands.",
)

response = agent.run("Create a hello.py file that prints 'Hello World'")
```

### With MCP Servers

```python
agent = Agent(
    model=ClaudeCode(
        mcp_servers={
            "myserver": {
                "type": "stdio",
                "command": "node",
                "args": ["path/to/mcp-server.js"]
            }
        },
        mcp_tools=["tool-from-mcp-server"]
    )
)
```

### Multi-turn Conversations

```python
agent = Agent(
    model=ClaudeCode(
        max_turns=5,
        continue_conversation=True
    )
)

# Have a multi-turn conversation
response1 = agent.run("Remember the number 42")
response2 = agent.run("What number did I ask you to remember?")
```

## Configuration Options

The ClaudeCode model supports these parameters:

- `system_prompt`: Initial system prompt
- `append_system_prompt`: Additional system prompt to append
- `allowed_tools`: List of allowed Claude Code tools (Read, Write, Bash, etc.)
- `disallowed_tools`: List of tools to disable
- `permission_mode`: How to handle tool permissions
  - `"default"`: Ask for permission
  - `"acceptEdits"`: Auto-accept file edits
  - `"bypassPermissions"`: Bypass all permissions
- `cwd`: Working directory for file operations
- `max_turns`: Maximum conversation turns
- `max_thinking_tokens`: Maximum tokens for thinking
- `continue_conversation`: Enable multi-turn conversations
- `model`: Model selection (if available in Claude Code)
- `mcp_tools`: List of MCP tools to enable
- `mcp_servers`: MCP server configurations

## Features Supported

✅ **Supported:**
- Text generation
- Built-in Claude Code tools (Read, Write, Bash, etc.)
- MCP (Model Context Protocol) servers
- System prompts
- Multi-turn conversations
- Working directory configuration
- Tool permission control
- Basic streaming (message-by-message)

❌ **Not Supported:**
- Image input/output
- Audio input/output
- Response format validation (structured output)
- Prompt caching
- Token-level streaming
- Direct temperature/max_tokens control

## Implementation Details

### Message Handling

The ClaudeCode model converts agno's message format to prompts that the claude-code-sdk expects:
- System messages become system prompts
- User messages are passed as prompts
- Assistant messages are handled for conversation context

### Tool Integration

Unlike the API version which uses agno's tool system, ClaudeCode uses Claude Code's built-in tools:
- File operations (Read, Write)
- Command execution (Bash)
- Web browsing capabilities
- And more depending on your Claude Code configuration

### Error Handling

The implementation handles these claude-code-sdk errors:
- `CLINotFoundError`: Claude Code not installed
- `CLIConnectionError`: Can't connect to Claude Code
- `ProcessError`: Claude Code process failed
- `CLIJSONDecodeError`: Response parsing issues

## Testing

Several test files were created:

1. `test_claudecode_agent.py` - Basic functionality test
2. `test_claudecode_simple_tools.py` - Tests built-in tools
3. `test_claudecode_tools.py` - Comprehensive feature tests

Run tests:
```bash
# Basic test
uv run test_claudecode_agent.py

# Tool test  
uv run test_claudecode_simple_tools.py
```

## Comparison with Anthropic API Model

The ClaudeCode model follows the same patterns as the Anthropic claude.py but adapts to local execution:

| Aspect | Anthropic claude.py | claudecode.py |
|--------|-------------------|---------------|
| Client | AnthropicClient (HTTP) | claude-code-sdk (IPC) |
| Auth | API key from env | None needed |
| Tools | agno tool system | Claude Code built-in |
| Streaming | Token-level | Message-level |
| Features | Full API features | SDK features only |

## Future Enhancements

Potential improvements:
1. Better streaming support when SDK adds it
2. Image/audio support if Claude Code adds it
3. Response format validation
4. Token counting accuracy
5. Conversation management improvements

## Troubleshooting

### "Claude Code CLI not found"
- Install Claude Code: `npm install -g @anthropic-ai/claude-code`
- Ensure `claude` is in your PATH

### "Failed to connect to Claude Code"
- Make sure Claude Code desktop app is running
- Check if `claude` CLI works in terminal

### Tool permissions issues
- Use `permission_mode="acceptEdits"` for auto-accepting
- Or handle permissions in Claude Code UI

## Summary

This integration allows agno users to:
1. Use Claude locally without API keys
2. Leverage Claude Code's built-in tools
3. Maintain code compatibility with agno's ecosystem
4. Switch between API and local Claude easily

The implementation provides a clean abstraction that makes local Claude Code work seamlessly within the agno framework while respecting the differences between API and local execution models.