# ClaudeCode vs Claude API: Implementation Comparison

This document compares the original Claude API implementation with the new ClaudeCode local implementation in agno.

## Overview

| Aspect | Claude API | ClaudeCode Local |
|--------|------------|------------------|
| **Execution** | HTTP API calls to Anthropic | Local Claude Code CLI |
| **API Key** | Required (`ANTHROPIC_API_KEY`) | Not required |
| **Internet** | Required | Not required |
| **Model Selection** | Full model IDs (e.g., `claude-3-5-sonnet-20241022`) | Simple names (e.g., `"sonnet"`) |
| **Usage Data** | Accurate from API | Accurate from Claude Code SDK |
| **Tools** | agno tools + API tools | agno tools + Claude Code built-in tools |

## Implementation Differences

### 1. Model Instantiation

**Claude API:**
```python
from agno.models.anthropic import Claude

agent = Agent(
    model=Claude(
        id="claude-3-5-sonnet-20241022",  # Required: specific model ID
        api_key="your-api-key"           # Required: API key
    ),
    instructions="You are a helpful assistant."
)
```

**ClaudeCode Local:**
```python
from agno.models.claudecode import ClaudeCode

agent = Agent(
    model=ClaudeCode(
        model="sonnet",                   # Optional: simple model name
        # No API key needed
    ),
    instructions="You are a helpful assistant."
)
```

### 2. Tool Integration

**Claude API:**
```python
from agno.tools import FileTools, PythonAssistant

agent = Agent(
    model=Claude(id="claude-3-5-sonnet-20241022"),
    tools=[FileTools(), PythonAssistant()],  # Use agno tools
    instructions="You can work with files and Python."
)
```

**ClaudeCode Local:**
```python
agent = Agent(
    model=ClaudeCode(
        allowed_tools=["Read", "Write", "Bash"],  # Use Claude Code's built-in tools
        permission_mode="acceptEdits",            # Auto-accept file edits
        cwd="/path/to/project"                   # Working directory
    ),
    tools=[PythonAssistant()],                   # Can still use agno tools too
    instructions="You can work with files and Python."
)
```

### 3. Advanced Features

**Claude API:**
```python
agent = Agent(
    model=Claude(
        id="claude-3-5-sonnet-20241022",
        api_key="your-api-key",
        # Limited to API capabilities
    ),
    instructions="Standard API features."
)
```

**ClaudeCode Local:**
```python
agent = Agent(
    model=ClaudeCode(
        model="sonnet",
        
        # System prompts
        system_prompt="You are an expert developer.",
        append_system_prompt="Always follow best practices.",
        
        # Built-in tools
        allowed_tools=["Read", "Write", "Bash", "Edit"],
        permission_mode="acceptEdits",
        cwd="/Users/username/project",
        
        # Multi-turn conversations
        max_turns=10,
        continue_conversation=True,
        max_thinking_tokens=20000,
        
        # MCP server integration
        mcp_servers={
            "github": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"]
            }
        },
        mcp_tools=["mcp__github__list_repos"]
    ),
    instructions="You have extensive capabilities."
)
```

## Response Structure Comparison

### Usage Data

**Claude API Response:**
```json
{
  "usage": {
    "input_tokens": 150,
    "output_tokens": 75,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0
  }
}
```

**ClaudeCode Response:**
```json
{
  "usage": {
    "input_tokens": 4,
    "cache_creation_input_tokens": 4947,
    "cache_read_input_tokens": 40694,
    "output_tokens": 6,
    "server_tool_use": {"web_search_requests": 0},
    "service_tier": "standard",
    "total_cost_usd": 0.15430725
  }
}
```

### Key Differences:
- **ClaudeCode** provides more detailed metrics (cache tokens, cost, service tier)
- **ClaudeCode** includes server tool usage statistics
- **ClaudeCode** provides actual cost in USD
- **Both** provide accurate token counts (no estimates)

## Feature Matrix

| Feature | Claude API | ClaudeCode |
|---------|------------|------------|
| **Basic Chat** | ✅ | ✅ |
| **Streaming** | ✅ | ✅ |
| **Tool Calls** | ✅ agno tools | ✅ agno + built-in tools |
| **File Operations** | ✅ via agno tools | ✅ via built-in Read/Write/Edit |
| **Shell Commands** | ✅ via agno tools | ✅ via built-in Bash |
| **MCP Integration** | ❌ | ✅ Full MCP server support |
| **Multi-turn Context** | ✅ | ✅ Enhanced with continue_conversation |
| **Permission Control** | ❌ | ✅ granular permission modes |
| **Working Directory** | ❌ | ✅ Configurable cwd |
| **System Prompts** | ✅ Basic | ✅ Enhanced with append_system_prompt |
| **Thinking Tokens** | ✅ | ✅ Configurable max_thinking_tokens |
| **Cost Tracking** | ❌ Manual calculation | ✅ Automatic USD cost |
| **Cache Analytics** | ✅ Basic | ✅ Detailed cache metrics |

## When to Use Which

### Use Claude API When:
- You need specific model versions not available locally
- You're in a constrained environment without Claude Code
- You prefer cloud-based execution
- You need guaranteed model availability

### Use ClaudeCode When:
- You want to avoid API costs
- You need offline operation
- You want built-in file/shell tools
- You need MCP server integration
- You want detailed usage analytics
- You prefer local execution for privacy

## Migration Guide

### From Claude API to ClaudeCode:

1. **Change import:**
   ```python
   # Before
   from agno.models.anthropic import Claude
   
   # After
   from agno.models.claudecode import ClaudeCode
   ```

2. **Update model instantiation:**
   ```python
   # Before
   model=Claude(id="claude-3-5-sonnet-20241022", api_key="key")
   
   # After
   model=ClaudeCode(model="sonnet")
   ```

3. **Consider replacing agno tools with built-ins:**
   ```python
   # Before
   tools=[FileTools(), ShellTools()]
   
   # After (optional)
   model=ClaudeCode(allowed_tools=["Read", "Write", "Bash"])
   ```

4. **Remove API key environment variable:**
   ```bash
   # No longer needed
   # export ANTHROPIC_API_KEY="your-key"
   ```

## Installation Differences

**Claude API:**
```bash
cd agno/libs/agno
uv add anthropic  # or pip install anthropic
export ANTHROPIC_API_KEY="your-key"
```

**ClaudeCode:**
```bash
cd agno/libs/agno
uv pip install -e ".[claudecode]"  # or uv add claude-code-sdk
# Ensure Claude Code CLI is installed and authenticated
```

## Cost Comparison

| Aspect | Claude API | ClaudeCode |
|--------|------------|------------|
| **Per Token** | Anthropic API rates | Claude Code subscription |
| **Tracking** | Manual calculation | Automatic USD reporting |
| **Billing** | Pay-per-use | Subscription model |
| **Limits** | API rate limits | Local resource limits |

## Conclusion

ClaudeCode provides a more feature-rich, cost-effective, and privacy-friendly alternative to the Claude API for local development. It offers enhanced capabilities like MCP integration, built-in tools, and detailed analytics while maintaining full compatibility with agno's Agent interface.

The choice between them depends on your specific needs:
- **Cloud-first, specific models**: Claude API
- **Local-first, enhanced features**: ClaudeCode