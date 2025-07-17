from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse
import smtplib
from email.message import EmailMessage
from config import settings  

router = APIRouter()

@router.post("/send-email")
async def send_email(
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    try:
        msg = EmailMessage()
        msg["Subject"] = "📬 New Message from Portfolio"
        msg["From"] = settings.EMAIL_USER
        msg["To"] = settings.EMAIL_USER  

        msg.set_content(f"""
You received a new message:

👤 Name: {name}
📧 Email: {email}
💬 Message: {message}
""")

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
            server.send_message(msg)


        return JSONResponse(status_code=200, content={"message": "Email sent successfully!"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to send email: {e}"})
