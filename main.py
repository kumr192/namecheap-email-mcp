import os
import json
from dotenv import load_dotenv
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio

load_dotenv()

app = FastAPI(title="Email MCP Server")

async def send_email_impl(to: str, subject: str, body: str, is_html: bool = False):
    """Actually send the email via Resend"""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise Exception("RESEND_API_KEY not set")
    
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
    
    if response.status_code != 200:
        raise Exception(f"Resend error: {response.text}")
    
    return f"Email sent to {to}"

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP Streamable HTTP endpoint"""
    body = await request.json()
    
    # Handle initialize
    if body.get("method") == "initialize":
        response = {
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "serverInfo": {
                    "name": "email-mcp-server",
                    "version": "1.0.0"
                }
            }
        }
        return response
    
    # Handle tool list
    if body.get("method") == "tools/list":
        response = {
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "send_email",
                        "description": "Send an email via Resend",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "to": {"type": "string", "description": "Recipient email"},
                                "subject": {"type": "string", "description": "Email subject"},
                                "body": {"type": "string", "description": "Email body"},
                                "is_html": {"type": "boolean", "description": "Is HTML?"}
                            },
                            "required": ["to", "subject", "body"]
                        }
                    }
                ]
            }
        }
        return response
    
    # Handle tool call
    if body.get("method") == "tools/call":
        tool_name = body.get("params", {}).get("name")
        arguments = body.get("params", {}).get("arguments", {})
        
        if tool_name == "send_email":
            try:
                result = await send_email_impl(
                    to=arguments.get("to"),
                    subject=arguments.get("subject"),
                    body=arguments.get("body"),
                    is_html=arguments.get("is_html", False)
                )
                response = {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {"content": [{"type": "text", "text": result}]}
                }
            except Exception as e:
                response = {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {"code": -32000, "message": str(e)}
                }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "error": {"code": -32601, "message": "Method not found"}
            }
        
        return response
    
    return {"error": "Invalid request"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
