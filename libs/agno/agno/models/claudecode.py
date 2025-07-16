"""Claude Code Model - Uses local Claude Code SDK instead of API calls"""

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, Union, Iterator, AsyncIterator

from pydantic import BaseModel

from agno.exceptions import ModelProviderError
from agno.models.base import Model
from agno.models.message import Message
from agno.models.response import ModelResponse
from agno.utils.log import log_debug, log_error, log_warning

try:
    from claude_code_sdk import query, ClaudeCodeOptions
    from claude_code_sdk.types import (
        AssistantMessage,
        TextBlock,
        ToolUseBlock,
        ToolResultBlock,
        UserMessage,
        SystemMessage,
        ResultMessage,
        McpServerConfig,
    )
    from claude_code_sdk._errors import (
        CLINotFoundError,
        CLIConnectionError,
        ProcessError,
        CLIJSONDecodeError,
    )
except ImportError as e:
    raise ImportError(
        "`claude-code-sdk` not installed. Please install it with `pip install claude-code-sdk`"
    ) from e


@dataclass
class ClaudeCode(Model):
    """
    A class representing Claude Code local model.
    
    This uses the Claude Code SDK to interact with the local Claude Code instance
    instead of making HTTP API calls.
    """
    
    id: str = "claude-code-local"
    name: str = "ClaudeCode"
    provider: str = "ClaudeCode"
    
    # Request parameters
    max_tokens: Optional[int] = None  # Not directly supported by SDK
    temperature: Optional[float] = None  # Not directly supported by SDK
    system_prompt: Optional[str] = None
    append_system_prompt: Optional[str] = None
    
    # Claude Code specific options
    allowed_tools: Optional[List[str]] = None
    disallowed_tools: Optional[List[str]] = None
    permission_mode: Optional[str] = None  # 'default', 'acceptEdits', 'bypassPermissions'
    cwd: Optional[str] = None
    max_turns: Optional[int] = 1  # Single turn by default
    max_thinking_tokens: Optional[int] = 8000
    continue_conversation: Optional[bool] = False
    resume: Optional[str] = None
    model: Optional[str] = None  # Model selection if available
    
    # MCP support
    mcp_tools: Optional[List[str]] = None
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None
    
    # Track conversation state for multi-turn
    _conversation_messages: List[Message] = None
    
    def __post_init__(self):
        """Initialize conversation state"""
        if self._conversation_messages is None:
            self._conversation_messages = []
    
    def _format_messages_for_prompt(self, messages: List[Message]) -> str:
        """Format messages into a single prompt for Claude Code"""
        # For multi-turn conversations, we need to track the full history
        if self.continue_conversation:
            self._conversation_messages.extend(messages)
            messages = self._conversation_messages
        
        # Extract system message if present
        system_content = None
        user_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            elif msg.role == "user":
                user_messages.append(msg.content)
            elif msg.role == "assistant":
                # For context, but Claude Code SDK handles this differently
                pass
        
        # Set system prompt if found and not already set
        if system_content and not self.system_prompt:
            self.system_prompt = system_content
        
        # Return the latest user message (Claude Code SDK handles conversation context)
        return user_messages[-1] if user_messages else ""
    
    def _get_claude_code_options(self) -> ClaudeCodeOptions:
        """Build ClaudeCodeOptions from model configuration"""
        options_dict = {}
        
        if self.system_prompt:
            options_dict["system_prompt"] = self.system_prompt
        if self.append_system_prompt:
            options_dict["append_system_prompt"] = self.append_system_prompt
        if self.allowed_tools:
            options_dict["allowed_tools"] = self.allowed_tools
        if self.disallowed_tools:
            options_dict["disallowed_tools"] = self.disallowed_tools
        if self.permission_mode:
            options_dict["permission_mode"] = self.permission_mode
        if self.cwd:
            options_dict["cwd"] = self.cwd
        if self.max_turns:
            options_dict["max_turns"] = self.max_turns
        if self.max_thinking_tokens:
            options_dict["max_thinking_tokens"] = self.max_thinking_tokens
        if self.continue_conversation:
            options_dict["continue_conversation"] = self.continue_conversation
        if self.resume:
            options_dict["resume"] = self.resume
        if self.model:
            options_dict["model"] = self.model
        if self.mcp_tools:
            options_dict["mcp_tools"] = self.mcp_tools
        if self.mcp_servers:
            options_dict["mcp_servers"] = self.mcp_servers
            
        return ClaudeCodeOptions(**options_dict)
    
    def _extract_tool_calls(self, message: AssistantMessage) -> List[Dict[str, Any]]:
        """Extract tool calls from assistant message"""
        tool_calls = []
        
        for block in message.content:
            if isinstance(block, ToolUseBlock):
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input) if block.input else "{}"
                    }
                })
        
        return tool_calls
    
    def _format_response(self, messages: List[Any]) -> Dict[str, Any]:
        """Format the response from Claude Code into expected structure"""
        response_text = ""
        tool_calls = []
        usage_info = {}
        
        for message in messages:
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
                    elif isinstance(block, ToolUseBlock):
                        tool_calls.append({
                            "id": block.id,
                            "type": "function",
                            "function": {
                                "name": block.name,
                                "arguments": json.dumps(block.input) if block.input else "{}"
                            }
                        })
            elif isinstance(message, ResultMessage):
                # Extract usage information
                if message.usage:
                    usage_info = message.usage
                if message.total_cost_usd:
                    usage_info["total_cost_usd"] = message.total_cost_usd
        
        # Build response structure similar to Anthropic API
        response = {
            "id": f"msg_claudecode_{id(self)}",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": response_text
                }
            ],
            "model": self.id,
            "stop_reason": "end_turn"
        }
        
        # Only add usage if we have actual data from Claude Code
        if usage_info:
            response["usage"] = usage_info
        
        # Add tool calls if present
        if tool_calls:
            response["tool_calls"] = tool_calls
        
        return response
    
    async def _query_claude_code(self, prompt: str) -> Dict[str, Any]:
        """Query Claude Code and get the response"""
        try:
            messages = []
            
            async for message in query(prompt=prompt, options=self._get_claude_code_options()):
                messages.append(message)
                log_debug(f"Received message type: {type(message).__name__}")
            
            return self._format_response(messages)
            
        except CLINotFoundError as e:
            raise ModelProviderError(
                message="Claude Code CLI not found. Please install with: npm install -g @anthropic-ai/claude-code",
                model_name=self.name,
                model_id=self.id
            ) from e
        except CLIConnectionError as e:
            raise ModelProviderError(
                message=f"Failed to connect to Claude Code: {str(e)}",
                model_name=self.name,
                model_id=self.id
            ) from e
        except ProcessError as e:
            raise ModelProviderError(
                message=f"Claude Code process failed with exit code {e.exit_code}",
                model_name=self.name,
                model_id=self.id
            ) from e
        except Exception as e:
            log_error(f"Unexpected error querying Claude Code: {str(e)}")
            raise ModelProviderError(
                message=str(e),
                model_name=self.name,
                model_id=self.id
            ) from e
    
    def invoke(
        self,
        messages: List[Message],
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Send a request to Claude Code to generate a response.
        """
        # Handle tools by setting allowed_tools
        if tools:
            tool_names = [tool.get("function", {}).get("name") for tool in tools if tool.get("function")]
            if tool_names and not self.allowed_tools:
                self.allowed_tools = tool_names
        
        # Format messages into a prompt
        prompt = self._format_messages_for_prompt(messages)
        
        # Add any specific instructions for response format
        if response_format:
            prompt += f"\n\nPlease respond in JSON format following this schema: {json.dumps(response_format)}"
        
        # Run async query in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self._query_claude_code(prompt))
        finally:
            loop.close()
        
        return response
    
    async def ainvoke(
        self,
        messages: List[Message],
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Async version of invoke"""
        # Handle tools by setting allowed_tools
        if tools:
            tool_names = [tool.get("function", {}).get("name") for tool in tools if tool.get("function")]
            if tool_names and not self.allowed_tools:
                self.allowed_tools = tool_names
        
        # Format messages into a prompt
        prompt = self._format_messages_for_prompt(messages)
        
        # Add any specific instructions for response format
        if response_format:
            prompt += f"\n\nPlease respond in JSON format following this schema: {json.dumps(response_format)}"
        
        # Query Claude Code
        return await self._query_claude_code(prompt)
    
    def invoke_stream(
        self,
        messages: List[Message],
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> Iterator[Any]:
        """
        Stream a response from Claude Code.
        Note: Real streaming is not supported, but we can yield messages as they come.
        """
        # Handle tools by setting allowed_tools
        if tools:
            tool_names = [tool.get("function", {}).get("name") for tool in tools if tool.get("function")]
            if tool_names and not self.allowed_tools:
                self.allowed_tools = tool_names
        
        prompt = self._format_messages_for_prompt(messages)
        
        if response_format:
            prompt += f"\n\nPlease respond in JSON format following this schema: {json.dumps(response_format)}"
        
        # Run async in sync context and yield results
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def _stream():
            async for message in query(prompt=prompt, options=self._get_claude_code_options()):
                yield message
        
        try:
            gen = _stream()
            while True:
                try:
                    message = loop.run_until_complete(gen.__anext__())
                    yield message
                except StopAsyncIteration:
                    break
        finally:
            loop.close()
    
    async def ainvoke_stream(
        self,
        messages: List[Message],
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> AsyncIterator[Any]:
        """Async streaming of responses"""
        # Handle tools by setting allowed_tools
        if tools:
            tool_names = [tool.get("function", {}).get("name") for tool in tools if tool.get("function")]
            if tool_names and not self.allowed_tools:
                self.allowed_tools = tool_names
        
        prompt = self._format_messages_for_prompt(messages)
        
        if response_format:
            prompt += f"\n\nPlease respond in JSON format following this schema: {json.dumps(response_format)}"
        
        async for message in query(prompt=prompt, options=self._get_claude_code_options()):
            yield message
    
    def parse_provider_response(self, response: Any, **kwargs) -> ModelResponse:
        """Parse the response from Claude Code into a ModelResponse"""
        model_response = ModelResponse()
        model_response.role = "assistant"
        
        if isinstance(response, dict):
            # Extract content from the response
            if "content" in response and isinstance(response["content"], list):
                for block in response["content"]:
                    if block.get("type") == "text":
                        if model_response.content is None:
                            model_response.content = block.get("text", "")
                        else:
                            model_response.content += block.get("text", "")
            
            # Extract tool calls
            if "tool_calls" in response:
                model_response.tool_calls = response["tool_calls"]
            
            # Set usage if available (only from actual SDK data, no estimates)
            if "usage" in response and response["usage"]:
                model_response.response_usage = response["usage"]
            
            # Store full response as provider data
            model_response.provider_data = response
            
            return model_response
        else:
            raise ValueError(f"Unexpected response type: {type(response)}")
    
    def parse_provider_response_delta(self, response: Any) -> ModelResponse:
        """Parse streaming response from Claude Code"""
        model_response = ModelResponse()
        
        if isinstance(response, AssistantMessage):
            for block in response.content:
                if isinstance(block, TextBlock):
                    model_response.content = block.text
                elif isinstance(block, ToolUseBlock):
                    # Handle streaming tool calls
                    model_response.tool_calls = [{
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": json.dumps(block.input) if block.input else "{}"
                        }
                    }]
        elif isinstance(response, SystemMessage):
            # Handle system messages in stream
            model_response.provider_data = {
                "system_message": {
                    "subtype": response.subtype,
                    "data": response.data
                }
            }
        elif isinstance(response, ResultMessage):
            # Final result message with usage data
            if response.usage:
                # Format usage data similar to Anthropic Claude
                usage_dict = {}
                if hasattr(response.usage, 'input_tokens'):
                    usage_dict['input_tokens'] = response.usage.input_tokens
                if hasattr(response.usage, 'output_tokens'):
                    usage_dict['output_tokens'] = response.usage.output_tokens
                
                # Only set response_usage if we have actual token counts
                if usage_dict:
                    model_response.response_usage = usage_dict
            
            # Store additional metadata in provider_data
            model_response.provider_data = {
                "result": {
                    "duration_ms": response.duration_ms,
                    "total_cost_usd": response.total_cost_usd
                }
            }
        
        return model_response