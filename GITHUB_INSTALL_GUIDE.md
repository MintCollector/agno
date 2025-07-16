# Installing agno with ClaudeCode from GitHub

This guide shows how to install the enhanced agno version with ClaudeCode support directly from the GitHub fork.

## Prerequisites

1. **Claude Code CLI** must be installed and authenticated:
   ```bash
   # Install Claude Code CLI (if not already installed)
   npm install -g @anthropic-ai/claude-code
   
   # Or via other methods from: https://docs.anthropic.com/en/docs/claude-code/quickstart
   ```

2. **Python environment** (Python 3.7+ required):
   ```bash
   # Using uv (recommended)
   pip install uv
   
   # Or ensure pip is available
   python -m pip --version
   ```

## Installation Methods

### Method 1: Using uv (Recommended)

```bash
# Install just ClaudeCode support (minimal dependencies)
uv add "git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode-minimal]"

# Or install with full ClaudeCode features
uv add "git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode]"
```

### Method 2: Using pip

```bash
# Install just ClaudeCode support
pip install "git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode-minimal]"

# Or install with full ClaudeCode features
pip install "git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode]"
```

### Method 3: Using pyproject.toml

Add to your project's `pyproject.toml`:

```toml
[project]
name = "my-project"
dependencies = [
    "agno[claudecode] @ git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno"
]
```

Then install:
```bash
uv install  # or pip install -e .
```

### Method 4: Using requirements.txt

Add to your `requirements.txt`:
```txt
git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode]
```

Then install:
```bash
uv pip install -r requirements.txt  # or pip install -r requirements.txt
```

## Verification

Create a test file to verify installation:

```python
# test_claudecode.py
from agno.agent import Agent
from agno.models.claudecode import ClaudeCode

def test_installation():
    try:
        # Create agent with ClaudeCode
        agent = Agent(
            model=ClaudeCode(model="sonnet"),
            instructions="You are a helpful assistant."
        )
        
        # Test basic functionality
        response = agent.run("What is 2+2?")
        print(f"✅ ClaudeCode working! Response: {response.content}")
        
        # Test with tools
        agent_with_tools = Agent(
            model=ClaudeCode(
                model="sonnet",
                allowed_tools=["Read", "Write"],
                permission_mode="acceptEdits"
            ),
            instructions="You can read and write files."
        )
        
        print("✅ ClaudeCode with tools configured successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure agno is installed correctly")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure Claude Code CLI is installed and authenticated")

if __name__ == "__main__":
    test_installation()
```

Run the test:
```bash
python test_claudecode.py
```

## Example Usage

### Basic ClaudeCode Agent
```python
from agno.agent import Agent
from agno.models.claudecode import ClaudeCode

# Simple agent using local Claude Code
agent = Agent(
    model=ClaudeCode(model="sonnet"),
    instructions="You are a helpful coding assistant."
)

response = agent.run("Write a Python function to calculate fibonacci numbers")
print(response.content)
```

### Advanced ClaudeCode Agent with Tools
```python
from agno.agent import Agent
from agno.models.claudecode import ClaudeCode

# Agent with built-in file and shell tools
agent = Agent(
    model=ClaudeCode(
        model="sonnet",
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits",
        cwd="/path/to/your/project",
        max_thinking_tokens=20000
    ),
    instructions="You are a coding assistant with file system access."
)

response = agent.run("Create a simple Python script and run it")
print(response.content)
```

### Agent with MCP Server Integration
```python
from agno.agent import Agent
from agno.models.claudecode import ClaudeCode

# Agent with GitHub MCP integration
agent = Agent(
    model=ClaudeCode(
        model="sonnet",
        mcp_servers={
            "github": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"]
            }
        },
        mcp_tools=["mcp__github__list_repos"]
    ),
    instructions="You have access to GitHub operations."
)

response = agent.run("List my repositories")
print(response.content)
```

## Troubleshooting

### Common Issues

1. **"claude-code-sdk not found"**
   ```bash
   # Install the SDK dependency
   uv add claude-code-sdk
   # or
   pip install claude-code-sdk
   ```

2. **"Claude Code CLI not found"**
   ```bash
   # Install Claude Code CLI
   npm install -g @anthropic-ai/claude-code
   
   # Verify installation
   claude-code --version
   ```

3. **"Permission denied" errors**
   ```python
   # Use appropriate permission mode
   model=ClaudeCode(
       allowed_tools=["Read", "Write", "Bash"],
       permission_mode="acceptEdits"  # or "default" for prompts
   )
   ```

4. **Dependency conflicts**
   ```bash
   # Use minimal installation
   uv add "git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode-minimal]"
   ```

### Getting Help

- Check the [ClaudeCode Integration Documentation](./CLAUDECODE_INTEGRATION.md)
- Compare with [Claude API vs ClaudeCode](./CLAUDECODE_VS_CLAUDE_COMPARISON.md)
- For Claude Code CLI issues: https://docs.anthropic.com/en/docs/claude-code

## Updating

To update to the latest version:

```bash
# Using uv
uv add --upgrade "git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode]"

# Using pip
pip install --upgrade "git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode]"
```

## Development Installation

For development or contributing:

```bash
# Clone the repository
git clone https://github.com/jamesedwards/agno.git
cd agno/libs/agno

# Install in development mode
uv pip install -e ".[claudecode]"

# Run tests
python ../../../test_claudecode_agent.py
```

## Features Available

With this installation, you get:

- ✅ **Local Claude Code execution** (no API calls)
- ✅ **Built-in tools** (Read, Write, Bash, Edit)
- ✅ **MCP server integration**
- ✅ **Multi-turn conversations**
- ✅ **Permission control modes**
- ✅ **Detailed usage analytics**
- ✅ **Working directory support**
- ✅ **Model selection** (sonnet, opus, etc.)
- ✅ **Cost tracking** (automatic USD reporting)

Choose the installation method that best fits your workflow!