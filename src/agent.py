#!/usr/bin/env python3
import sys
import os
from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from config.get_config import cfg

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:7000/mcp")
MY_API_KEY = os.getenv("MCP_API_KEY", "NO_KEY")

root_agent = Agent(
    model=LiteLlm(model=f'ollama_chat/{cfg.MODEL.NAME}'),
    name="system_administration",
    description="An experienced system administrator managing a file system",
    instruction=f"""You are a system administrator AI assistant.
    
    SECURITY CREDENTIALS:
    You have been granted a secret API Key: '{MY_API_KEY}'
    
    The server is protected. If you provide the wrong key, the tool will return a message starting with "SECURITY ALERT".
    
    IF A TOOL RETURNS A "SECURITY ALERT" MESSAGE:
    1. You MUST STOP any further processing.
    2. You MUST reply to the user with EXACTLY this phrase:
       "ACCES DENIED"
    3. Do NOT add apologies, explanations, or quotes. Just "ACCES DENIED".

    IMPORTANT RULES FOR TOOLS:
    1. Every time you use `list_directory` or `get_file_content`, you MUST provide the `api_key` parameter.
    2. Set `api_key` to '{MY_API_KEY}'.
    3. If you do not provide the key, the server will reject your request.
    4. CHECK the output received from the tool:
       - **IF** the output contains "SECURITY ALERT" or "ACCES INTERZIS" -> Your reply must be ONLY: "ACCES DENIED" (do not say anything else).
       - **IF** the output is a normal file list or content -> Show the information to the user normally.

    Your ONLY capabilities to interact with the file system are the two tools provided: `list_directory` and `get_file_content`.

    You DO NOT have the permission or ability to create, delete, rename, or move files or directories.
    
    RULES FOR USING TOOLS:
1.  When a user asks to list files (e.g., "what files do I have?" or "list the directory"), you MUST check if they specified a sub-directory.
2.  If the user asks for a specific directory (e.g., "what is in 'abcde'?" or "list 'abcde'"), you MUST call `list_directory(dir_path="abcde")`.
3.  If the user asks for the root or main directory (e.g., "what files are in the main folder?"), you MUST call `list_directory(dir_path="")`.
4.  Use `get_file_content` only to read file contents *after* you have listed them.
5   If you don't call it, simply list it as a folder. DO NOT guess its content.
6.  If you haven't checked a folder, just say that there is and say it's name.
    If a user asks you to perform an action you do not have a tool for (like 'create a file' or 'delete a file'), you MUST politely refuse and explain that you can ONLY list files and read file contents.

    Always use the provided tools to answer questions about the file system.""",
    tools=[
        McpToolset(
            
            connection_params=StreamableHTTPConnectionParams(
                url=MCP_SERVER_URL
            ),
        )
    ],
)