"""
MailerLite email service using requests with background task support.
Uses the connect.mailerlite.com API endpoint directly.
"""
import requests
import logging
from typing import Tuple, Optional
from app.config import MAILERLITE_API_KEY

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        
        # Debug logging
        logger.debug("=" * 50)
        logger.debug("SENDING EMAIL")
        logger.debug(f"URL: {MAILERLITE_URL}")
        logger.debug(f"From: {from_name} <{from_email}>")
        logger.debug(f"To: {to_name} <{to_email}>")
        logger.debug(f"Subject: {subject}")
        logger.debug(f"HTML Length: {len(html_content)} chars")
        logger.debug(f"API Key (first 20 chars): {MAILERLITE_API_KEY[:20]}...")
        logger.debug("=" * 50)
        
        response = requests.post(
            MAILERLITE_URL,
            json=payload,
            headers=headers,
            timeout=timeout
        )
        
        # Debug response
        logger.debug(f"Response Status Code: {response.status_code}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        logger.debug(f"Response Body: {response.text}")
        logger.debug("=" * 50)
        
        return response.status_code, response.text
        
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error: {e}")
        return 408, "Request timeout - email service took too long to respond"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return 503, "Connection error - could not reach email service"
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 500, f"Email sending failed: {str(e)}"


def send_email_dict(payload: dict, timeout: int = 30) -> Tuple[int, str]:
    """
    Send an email using a dictionary payload (legacy support).
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
        logger.error(f"send_email_dict error: {e}", exc_info=True)
        return 500, f"Email sending failed: {str(e)}"
