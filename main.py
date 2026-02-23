import os
from dotenv import load_dotenv
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

load_dotenv()

server = Server("email-mcp-server")

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "send_email":
        to = arguments.get("to")
        subject = arguments.get("subject")
        body = arguments.get("body")
        is_html = arguments.get("is_html", False)
        
        try:
            api_key = os.getenv("RESEND_API_KEY")
            if not api_key:
                return [TextContent(type="text", text="Error: RESEND_API_KEY not set")]
            
            sender_email = os.getenv("SENDER_EMAIL", "onboarding@resend.dev")
            
            payload = {
                "from": sender_email,
                "to": to,
                "subject": subject,
            }
            
            if is_html:
                payload["html"] = body
            else:
                payload["text"] = body
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers={"Authorization": f"Bearer {api_key}"}
                )
            
            if response.status_code == 200:
                return [TextContent(type="text", text=f"Email sent to {to}")]
            else:
                return [TextContent(type="text", text=f"Error: {response.text}")]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="send_email",
            description="Send an email via Resend",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body"},
                    "is_html": {"type": "boolean", "description": "Is body HTML?", "default": False}
                },
                "required": ["to", "subject", "body"]
            }
        )
    ]

if __name__ == "__main__":
    from mcp.server.stdio import stdio_server
    import asyncio
    
    # For local testing with stdio
    asyncio.run(stdio_server(server))
