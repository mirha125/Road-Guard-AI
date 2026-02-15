import emails
from emails.template import JinjaTemplate as T
from ..config import settings
class EmailService:
    def send_alert_email(self, to_email: str, location: str, details: str, time: str):
        message = emails.Message(
            subject=f"ALERT: Incident at {location}",
            mail_from=(settings.MAIL_FROM_NAME, settings.MAIL_FROM),
        )
        body = f"""
        <h1>Traffic Safety Alert</h1>
        <p><strong>Location:</strong> {location}</p>
        <p><strong>Time:</strong> {time}</p>
        <p><strong>Details:</strong> {details}</p>
        <p>Please take necessary action immediately.</p>
        """
        message.html = body
        r = message.send(
            to=to_email,
            smtp={
                "host": settings.MAIL_SERVER,
                "port": settings.MAIL_PORT,
                "user": settings.MAIL_USERNAME,
                "password": settings.MAIL_PASSWORD,
                "tls": True,
            },
        )
        return r.status_code
email_service = EmailService()