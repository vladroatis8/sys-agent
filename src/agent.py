#!/usr/bin/env python3
import sys
import os
from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
# MODIFICARE: Importam StreamableHTTPConnectionParams in loc de Stdio
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from config.get_config import cfg

# Preluam URL-ul din variabilele de mediu (setate in docker-compose)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:7000/mcp")

root_agent = Agent(
    model=LiteLlm(model=f'ollama_chat/{cfg.MODEL.NAME}'),
    name="system_administration",
    description="An experienced system administrator managing a file system",
    instruction="""You are a system administrator AI assistant.
    
    Your ONLY capabilities to interact with the file system are the two tools provided: `list_directory` and `get_file_content`.

    You DO NOT have the permission or ability to create, delete, rename, or move files or directories.
    
    RULES FOR USING TOOLS:
1.  When a user asks to list files (e.g., "what files do I have?" or "list the directory"), you MUST check if they specified a sub-directory.
2.  If the user asks for a specific directory (e.g., "what is in 'abcde'?" or "list 'abcde'"), you MUST call `list_directory(dir_path="abcde")`.
3.  If the user asks for the root or main directory (e.g., "what files are in the main folder?"), you MUST call `list_directory(dir_path="")`.
4.  Use `get_file_content` only to read file contents *after* you have listed them.

    If a user asks you to perform an action you do not have a tool for (like 'create a file' or 'delete a file'), you MUST politely refuse and explain that you can ONLY list files and read file contents.

    Always use the provided tools to answer questions about the file system.""",
    tools=[
        McpToolset(
            # MODIFICARE: Folosim HTTP cu URL-ul serverului
            connection_params=StreamableHTTPConnectionParams(
                url=MCP_SERVER_URL
            ),
        )
    ],
)