from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv

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
        from resend import Resend
        
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            return {"success": False, "error": "RESEND_API_KEY not set"}
        
        client = Resend(api_key=api_key)
        sender_email = os.getenv("SENDER_EMAIL", "onboarding@resend.dev")
        
        email_dict = {
            "from": sender_email,
            "to": request.to,
            "subject": request.subject,
        }
        
        if request.is_html:
            email_dict["html"] = request.body
        else:
            email_dict["text"] = request.body
        
        response = client.emails.send(email_dict)
        
        return {"success": True, "message": f"Email sent to {request.to}", "id": response.get("id")}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
