# Quick Start: Install agno with ClaudeCode from GitHub

## TL;DR - One Command Install

```bash
# Install with uv (recommended)
uv add "git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode]"

# Or with pip
pip install "git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode]"
```

## Quick Test

```python
from agno.agent import Agent
from agno.models.claudecode import ClaudeCode

agent = Agent(
    model=ClaudeCode(model="sonnet"),
    instructions="You are a helpful assistant."
)

response = agent.run("What is 2+2?")
print(response.content)  # Should print: "4"
```

## GitHub URL Breakdown

```
git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode]
│   │                                        │                │            │
│   │                                        │                │            └── Extra features
│   │                                        │                └── Package name
│   │                                        └── Subdirectory (agno is in libs/agno)
│   └── Your fork URL
└── Git protocol
```

## What You Get

- **Local Claude Code** instead of API calls
- **Built-in tools** (Read, Write, Bash, Edit)
- **MCP server support** for integrations
- **Detailed usage analytics** with cost tracking
- **Enhanced features** not available in original agno

## Alternative Installation Options

### Just ClaudeCode (minimal dependencies)
```bash
uv add "git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode-minimal]"
```

### For pyproject.toml
```toml
[project]
dependencies = [
    "agno[claudecode] @ git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno"
]
```

### For requirements.txt
```txt
git+https://github.com/jamesedwards/agno.git#subdirectory=libs/agno&egg=agno[claudecode]
```

## Prerequisites

1. **Claude Code CLI** must be installed:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Python 3.7+** with pip or uv

## Verification

Run this to verify installation:
```bash
python -c "from agno.models.claudecode import ClaudeCode; print('✅ ClaudeCode installed successfully!')"
```

## Next Steps

- Check out the [full installation guide](./GITHUB_INSTALL_GUIDE.md)
- Read the [ClaudeCode vs Claude API comparison](./CLAUDECODE_VS_CLAUDE_COMPARISON.md)
- See [integration documentation](./CLAUDECODE_INTEGRATION.md) for advanced features

## Support

If you encounter issues:
1. Ensure Claude Code CLI is installed and authenticated
2. Try the minimal installation: `agno[claudecode-minimal]`
3. Check the troubleshooting section in the full guide