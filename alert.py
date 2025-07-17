from fastapi.responses import JSONResponse
import smtplib
from email.message import EmailMessage

def send_fraud_alert_email(txn_dict):
    try:
        msg = EmailMessage()
        msg["Subject"] = "🚨 Fraudulent Transaction Detected"
        msg["From"] = "sarfof06@gmail.com"
        msg["To"] = "bentjun25@gmail.com,piesiegloria25@gmail.com"
        msg.set_content(f"A fraud has been detected:\n\n{txn_dict}")

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("sarfof06@gmail.com", "mhtehnhylovnlplj")
            server.send_message(msg, to_addrs=["bentjun25@gmail.com", "piesiegloria25@gmail.com"])

        logging.info("Fraud alert email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send fraud alert email: {e}")
        


