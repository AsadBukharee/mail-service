"""
MailerLite email service using requests with background task support.
Uses the connect.mailerlite.com API endpoint directly.
"""
import requests
from typing import Tuple, Optional
from app.config import MAILERLITE_API_KEY

MAILERLITE_URL = "https://connect.mailerlite.com/api/email/send"


def send_email(
    from_email: str,
    from_name: str,
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    timeout: int = 30
) -> Tuple[int, str]:
    """
    Send an email using MailerLite API via requests.
    
    Args:
        from_email: Sender email address
        from_name: Sender name
        to_email: Recipient email address
        to_name: Recipient name
        subject: Email subject
        html_content: HTML body content
        text_content: Optional plain text content
        timeout: Request timeout in seconds
    
    Returns:
        Tuple of (status_code, response_message)
    """
    try:
        headers = {
            "Authorization": f"Bearer {MAILERLITE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": {"email": from_email, "name": from_name},
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject,
            "html": html_content,
        }
        
        if text_content:
            payload["text"] = text_content
        
        response = requests.post(
            MAILERLITE_URL,
            json=payload,
            headers=headers,
            timeout=timeout
        )
        
        return response.status_code, response.text
        
    except requests.exceptions.Timeout:
        return 408, "Request timeout - email service took too long to respond"
    except requests.exceptions.ConnectionError:
        return 503, "Connection error - could not reach email service"
    except Exception as e:
        return 500, f"Email sending failed: {str(e)}"


def send_email_dict(payload: dict, timeout: int = 30) -> Tuple[int, str]:
    """
    Send an email using a dictionary payload (legacy support).
    
    Args:
        payload: Dictionary with email details
        timeout: Request timeout in seconds
    
    Returns:
        Tuple of (status_code, response_message)
    """
    try:
        from_data = payload.get("from", {})
        to_data = payload.get("to", [{}])[0] if payload.get("to") else {}
        
        return send_email(
            from_email=from_data.get("email", ""),
            from_name=from_data.get("name", ""),
            to_email=to_data.get("email", ""),
            to_name=to_data.get("name", ""),
            subject=payload.get("subject", ""),
            html_content=payload.get("html", ""),
            text_content=payload.get("text"),
            timeout=timeout
        )
    except Exception as e:
        return 500, f"Email sending failed: {str(e)}"
