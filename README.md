# Prompts - MCP Server

This repository contains many AI prompts for common tasks, now available as an MCP (Model Context Protocol) Server for automated prompt discovery and retrieval.

## Using the Prompts

The prompts work primarily with OpenAI's GPT4o model, but should work with any GPT model. Some system prompts require customization - see content in Mustache tags (e.g., `{{ variable }}`) for placeholders to replace with your own content.

## MCP Server

This repository now functions as an MCP Server, allowing AI assistants to automatically discover and retrieve prompts.

### Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python3 server.py
   ```
   
   Or use the convenience script:
   ```bash
   ./run-server.sh
   ```

### MCP Client Configuration

Add this to your MCP client configuration (typically `mcp-config.json`):

```json
{
  "mcpServers": {
    "prompts": {
      "command": "python3",
      "args": ["server.py"],
      "env": {}
    }
  }
}
```

### Available Resources and Tools

The MCP server provides:

**Resources:**
- Each prompt file is exposed as a resource with URI `prompts://{prompt-name}`
- Resources can be read to get the full prompt content

**Tools:**
- `list_prompts`: List all available prompts with descriptions
- `get_prompt`: Get the content of a specific prompt by name  
- `search_prompts`: Search prompts by keyword in filename or content

### Available Prompts

- **Copyediting**: Expert prose editing for grammar, style, and clarity
- **Prompt Improvement**: Enhance AI prompt quality and specificity
- **Prose Evaluation**: Analyze transitions and flow in written content
- **Style Guide Generation**: Create reproducible style guides from text samples
- **GitHub Issues**: Generate detailed Jira tickets from requirements
