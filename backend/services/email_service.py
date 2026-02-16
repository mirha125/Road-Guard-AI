import emails
from emails.template import JinjaTemplate as T
from ..config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

class EmailService:
    async def send_alert_email(self, to_email: str, location: str, details: str, time: str):
        """
        Send alert email asynchronously
        """
        try:
            # Run the email sending in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._send_email_sync,
                to_email,
                location,
                details,
                time
            )
            return result
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return None

    def _send_email_sync(self, to_email: str, location: str, details: str, time: str):
        """
        Synchronous email sending function (runs in executor)
        """
        try:
            message = emails.Message(
                subject=f"🚨 URGENT ALERT: Traffic Accident Detected at {location}",
                mail_from=(settings.MAIL_FROM_NAME, settings.MAIL_FROM),
            )

            # Beautiful HTML email template
            body = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Traffic Safety Alert</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6;">
                <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f3f4f6; padding: 40px 0;">
                    <tr>
                        <td align="center">
                            <!-- Main Container -->
                            <table role="presentation" style="width: 600px; max-width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">

                                <!-- Header with gradient -->
                                <tr>
                                    <td style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); padding: 40px 30px; text-align: center;">
                                        <div style="background-color: rgba(255,255,255,0.2); border-radius: 50%; width: 80px; height: 80px; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                                            <span style="font-size: 48px; line-height: 1;">🚨</span>
                                        </div>
                                        <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">
                                            URGENT ALERT
                                        </h1>
                                        <p style="color: rgba(255,255,255,0.95); margin: 10px 0 0 0; font-size: 16px; font-weight: 500;">
                                            Traffic Accident Detected
                                        </p>
                                    </td>
                                </tr>

                                <!-- Alert Badge -->
                                <tr>
                                    <td style="padding: 0; text-align: center; transform: translateY(-15px);">
                                        <div style="display: inline-block; background-color: #fef2f2; border: 3px solid #dc2626; border-radius: 12px; padding: 8px 20px; font-weight: 700; color: #dc2626; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; box-shadow: 0 4px 12px rgba(220, 38, 38, 0.2);">
                                            ⚠️ IMMEDIATE ACTION REQUIRED
                                        </div>
                                    </td>
                                </tr>

                                <!-- Content -->
                                <tr>
                                    <td style="padding: 30px 40px;">
                                        <p style="color: #374151; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                            Our AI-powered monitoring system has detected a potential traffic accident. Please review the details below and take necessary action immediately.
                                        </p>

                                        <!-- Info Cards -->
                                        <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                                            <!-- Location -->
                                            <tr>
                                                <td style="padding: 20px; background-color: #f9fafb; border-radius: 12px; margin-bottom: 12px; border-left: 4px solid #3b82f6;">
                                                    <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                                        <tr>
                                                            <td style="width: 40px; vertical-align: top;">
                                                                <span style="font-size: 24px;">📍</span>
                                                            </td>
                                                            <td style="vertical-align: top;">
                                                                <div style="color: #6b7280; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
                                                                    Location
                                                                </div>
                                                                <div style="color: #111827; font-size: 16px; font-weight: 600;">
                                                                    {location}
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>

                                            <!-- Spacer -->
                                            <tr><td style="height: 12px;"></td></tr>

                                            <!-- Time -->
                                            <tr>
                                                <td style="padding: 20px; background-color: #f9fafb; border-radius: 12px; margin-bottom: 12px; border-left: 4px solid #8b5cf6;">
                                                    <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                                        <tr>
                                                            <td style="width: 40px; vertical-align: top;">
                                                                <span style="font-size: 24px;">🕐</span>
                                                            </td>
                                                            <td style="vertical-align: top;">
                                                                <div style="color: #6b7280; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
                                                                    Detection Time
                                                                </div>
                                                                <div style="color: #111827; font-size: 16px; font-weight: 600;">
                                                                    {time}
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>

                                            <!-- Spacer -->
                                            <tr><td style="height: 12px;"></td></tr>

                                            <!-- Details -->
                                            <tr>
                                                <td style="padding: 20px; background-color: #fef2f2; border-radius: 12px; border-left: 4px solid #dc2626;">
                                                    <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                                        <tr>
                                                            <td style="width: 40px; vertical-align: top;">
                                                                <span style="font-size: 24px;">ℹ️</span>
                                                            </td>
                                                            <td style="vertical-align: top;">
                                                                <div style="color: #6b7280; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
                                                                    Alert Details
                                                                </div>
                                                                <div style="color: #111827; font-size: 15px; line-height: 1.6;">
                                                                    {details}
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>

                                        <!-- Action Steps -->
                                        <div style="background-color: #eff6ff; border-radius: 12px; padding: 24px; margin-top: 24px; border: 2px solid #dbeafe;">
                                            <h3 style="color: #1e40af; margin: 0 0 16px 0; font-size: 16px; font-weight: 700;">
                                                🚑 Recommended Actions
                                            </h3>
                                            <ul style="color: #1e3a8a; margin: 0; padding-left: 20px; line-height: 1.8; font-size: 14px;">
                                                <li>Dispatch emergency medical services to the location</li>
                                                <li>Alert nearby traffic authorities</li>
                                                <li>Prepare emergency response team</li>
                                                <li>Monitor the situation for updates</li>
                                            </ul>
                                        </div>
                                    </td>
                                </tr>

                                <!-- Footer -->
                                <tr>
                                    <td style="background-color: #f9fafb; padding: 30px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
                                        <div style="margin-bottom: 12px;">
                                            <span style="font-size: 24px;">🛡️</span>
                                        </div>
                                        <p style="color: #6b7280; font-size: 13px; line-height: 1.6; margin: 0 0 8px 0;">
                                            This alert was generated by <strong style="color: #111827;">RoadGuardAI</strong>
                                        </p>
                                        <p style="color: #9ca3af; font-size: 12px; line-height: 1.5; margin: 0;">
                                            AI-Powered Traffic Safety Monitoring System<br>
                                            Automated Alert • Do Not Reply
                                        </p>
                                        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                                            <p style="color: #9ca3af; font-size: 11px; margin: 0;">
                                                © 2026 RoadGuardAI. All rights reserved.
                                            </p>
                                        </div>
                                    </td>
                                </tr>

                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
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
            logger.info(f"Email sent to {to_email}: Status {r.status_code}")
            return r.status_code
        except Exception as e:
            logger.error(f"Error in _send_email_sync: {e}")
            raise

email_service = EmailService()