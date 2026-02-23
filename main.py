import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Namecheap Email MCP Server")

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    is_html: bool = False

@app.post("/send-email")
async def send_email(request: EmailRequest) -> dict:
    """Send an email via Namecheap SMTP"""
    
    smtp_server = "mail.privateemail.com"
    smtp_port = 587
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    if not sender_email or not sender_password:
        return {"success": False, "error": "EMAIL_ADDRESS or EMAIL_PASSWORD not set"}
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = request.subject
        msg["From"] = sender_email
        msg["To"] = request.to
        
        if request.is_html:
            msg.attach(MIMEText(request.body, "html"))
        else:
            msg.attach(MIMEText(request.body, "plain"))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, request.to, msg.as_string())
        
        return {"success": True, "message": f"Email sent to {request.to}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)