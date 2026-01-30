import requests
from app.config import MAILERLITE_API_KEY

MAILERLITE_URL = "https://connect.mailerlite.com/api/email/send"

def send_email(payload: dict):
    headers = {
        "Authorization": f"Bearer {MAILERLITE_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(MAILERLITE_URL, json=payload, headers=headers)
    return response.status_code, response.text
