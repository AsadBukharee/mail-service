from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import EmailLog
from app.schemas import EmailRequest
from app.mailerlite import send_email
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/send-email")
def send_mail(data: EmailRequest, db: Session = Depends(get_db)):
    payload = {
        "from": {"email": data.sender_email, "name": data.sender_name},
        "to": [{"email": data.receiver_email, "name": data.receiver_name}],
        "subject": data.subject,
        "html": data.content
    }

    status_code, response = send_email(payload)

    log = EmailLog(
        sender_email=data.sender_email,
        receiver_email=data.receiver_email,
        subject=data.subject,
        status="sent" if status_code == 200 else "failed",
        response=response
    )
    db.add(log)
    db.commit()

    return {"status": log.status}

@router.get("/status", response_class=HTMLResponse)
def status_page(request: Request):
    return templates.TemplateResponse("status.html", {"request": request})

@router.get("/api/status")
def email_status(
    page: int = 1,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(EmailLog)
    if status:
        query = query.filter(EmailLog.status == status)

    per_page = 10
    total = query.count()
    emails = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total": total,
        "page": page,
        "data": [
            {
                "id": e.id,
                "sender": e.sender_email,
                "receiver": e.receiver_email,
                "subject": e.subject,
                "status": e.status,
                "created_at": e.created_at
            } for e in emails
        ]
    }
