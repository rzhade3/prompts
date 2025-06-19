#!/usr/bin/env python3
"""
MCP Server for AI Prompts Repository

This server exposes AI prompts as resources and provides tools for discovering and retrieving prompts.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
)


class PromptsServer:
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.server = Server("prompts-server")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP server handlers"""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List all available prompt resources"""
            resources = []
            if self.prompts_dir.exists():
                for prompt_file in self.prompts_dir.glob("*.md"):
                    resources.append(Resource(
                        uri=f"prompts://{prompt_file.stem}",
                        name=prompt_file.stem.replace("-", " ").title(),
                        description=f"AI prompt for {prompt_file.stem.replace('-', ' ')}",
                        mimeType="text/markdown"
                    ))
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a specific prompt resource"""
            if not uri.startswith("prompts://"):
                raise ValueError(f"Invalid URI: {uri}")
            
            prompt_name = uri.replace("prompts://", "")
            prompt_file = self.prompts_dir / f"{prompt_name}.md"
            
            if not prompt_file.exists():
                raise FileNotFoundError(f"Prompt not found: {prompt_name}")
            
            return prompt_file.read_text(encoding="utf-8")
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="list_prompts",
                    description="List all available prompts with their descriptions",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_prompt",
                    description="Get the content of a specific prompt by name",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the prompt to retrieve"
                            }
                        },
                        "required": ["name"]
                    }
                ),
                Tool(
                    name="search_prompts",
                    description="Search prompts by keyword in their content or filename",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search term to look for in prompt names and content"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            
            if name == "list_prompts":
                return await self._list_prompts()
            elif name == "get_prompt":
                prompt_name = arguments.get("name")
                if not prompt_name:
                    return [TextContent(type="text", text="Error: prompt name is required")]
                return await self._get_prompt(prompt_name)
            elif name == "search_prompts":
                query = arguments.get("query")
                if not query:
                    return [TextContent(type="text", text="Error: search query is required")]
                return await self._search_prompts(query)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    async def _list_prompts(self) -> List[TextContent]:
        """List all available prompts"""
        if not self.prompts_dir.exists():
            return [TextContent(type="text", text="No prompts directory found")]
        
        prompts = []
        for prompt_file in self.prompts_dir.glob("*.md"):
            # Read first few lines to get description
            content = prompt_file.read_text(encoding="utf-8")
            first_line = content.split('\n')[0] if content else ""
            
            prompts.append({
                "name": prompt_file.stem,
                "title": prompt_file.stem.replace("-", " ").title(),
                "description": first_line[:100] + "..." if len(first_line) > 100 else first_line,
                "file": prompt_file.name
            })
        
        result = "Available Prompts:\n\n"
        for prompt in prompts:
            result += f"**{prompt['title']}** (`{prompt['name']}`)\n"
            result += f"Description: {prompt['description']}\n\n"
        
        return [TextContent(type="text", text=result)]
    
    async def _get_prompt(self, name: str) -> List[TextContent]:
        """Get a specific prompt by name"""
        prompt_file = self.prompts_dir / f"{name}.md"
        
        if not prompt_file.exists():
            return [TextContent(type="text", text=f"Prompt '{name}' not found")]
        
        content = prompt_file.read_text(encoding="utf-8")
        return [TextContent(type="text", text=content)]
    
    async def _search_prompts(self, query: str) -> List[TextContent]:
        """Search prompts by query"""
        if not self.prompts_dir.exists():
            return [TextContent(type="text", text="No prompts directory found")]
        
        results = []
        query_lower = query.lower()
        
        for prompt_file in self.prompts_dir.glob("*.md"):
            # Check filename
            if query_lower in prompt_file.stem.lower():
                content = prompt_file.read_text(encoding="utf-8")
                first_line = content.split('\n')[0] if content else ""
                results.append({
                    "name": prompt_file.stem,
                    "match_type": "filename",
                    "description": first_line[:100] + "..." if len(first_line) > 100 else first_line
                })
                continue
            
            # Check content
            content = prompt_file.read_text(encoding="utf-8")
            if query_lower in content.lower():
                first_line = content.split('\n')[0] if content else ""
                results.append({
                    "name": prompt_file.stem,
                    "match_type": "content", 
                    "description": first_line[:100] + "..." if len(first_line) > 100 else first_line
                })
        
        if not results:
            return [TextContent(type="text", text=f"No prompts found matching '{query}'")]
        
        result_text = f"Found {len(results)} prompt(s) matching '{query}':\n\n"
        for item in results:
            result_text += f"**{item['name'].replace('-', ' ').title()}** (`{item['name']}`)\n"
            result_text += f"Match: {item['match_type']}\n"
            result_text += f"Description: {item['description']}\n\n"
        
        return [TextContent(type="text", text=result_text)]

    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, 
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point"""
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    prompts_dir = script_dir / "prompts"
    
    if not prompts_dir.exists():
        print(f"Error: Prompts directory not found at {prompts_dir}", file=sys.stderr)
        sys.exit(1)
    
    server = PromptsServer(prompts_dir)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()