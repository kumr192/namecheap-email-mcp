from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

app = FastAPI(title="Email MCP Server")

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    is_html: bool = False

@app.post("/send-email")
async def send_email(request: EmailRequest) -> dict:
    """Send an email via Resend"""
    
    try:
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            return {"success": False, "error": "RESEND_API_KEY not set"}
        
        sender_email = os.getenv("SENDER_EMAIL", "onboarding@resend.dev")
        
        payload = {
            "from": sender_email,
            "to": request.to,
            "subject": request.subject,
        }
        
        if request.is_html:
            payload["html"] = request.body
        else:
            payload["text"] = request.body
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"}
            )
        
        if response.status_code == 200:
            return {"success": True, "message": f"Email sent to {request.to}"}
        else:
            return {"success": False, "error": response.text}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
