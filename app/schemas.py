from pydantic import BaseModel, EmailStr

class EmailRequest(BaseModel):
    sender_email: EmailStr
    sender_name: str
    receiver_email: EmailStr
    receiver_name: str
    subject: str
    content: str  # HTML
