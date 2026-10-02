import smtplib
from email.message import EmailMessage
from app.config import settings

def test_smtp():
    msg = EmailMessage()
    msg.set_content("This is a test email")
    msg["Subject"] = "Test Email"
    msg["From"] = f"Mirabooks <{settings.mailgun_sender_email}>"
    msg["To"] = "oladimejimirawoola@gmail.com"

    try:
        # Connect to Mailgun SMTP
        s = smtplib.SMTP("smtp.eu.mailgun.org", 587)
        s.starttls()
        
        # Use postmaster@domain and the key they provided as password
        username = f"postmaster@{settings.mailgun_domain}"
        password = settings.mailgun_api_key
        
        s.login(username, password)
        s.send_message(msg)
        s.quit()
        print("SMTP Success!")
    except Exception as e:
        print(f"SMTP Failed: {e}")

if __name__ == "__main__":
    test_smtp()
