"""
FastAPI routers for email service with background task processing.
"""
from fastapi import APIRouter, Depends, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import EmailLog
from app.schemas import EmailRequest
from app.mailerlite import send_email

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def send_email_background(email_log_id: int, payload: dict):
    """
    Background task to send email and update log status.
    
    Args:
        email_log_id: ID of the email log entry to update
        payload: Email payload with from, to, subject, template_data
    """
    from jinja2 import Environment, FileSystemLoader
    
    db = SessionLocal()
    try:
        # Get the email log entry
        log = db.query(EmailLog).filter(EmailLog.id == email_log_id).first()
        if not log:
            return
        
        # Render the welcome template with Jinja2
        env = Environment(loader=FileSystemLoader("app/templates/emails"))
        template = env.get_template("welcome.html")
        
        # Get template data from payload
        template_data = payload.get("template_data", {})
        from_data = payload.get("from", {})
        to_data = payload.get("to", [{}])[0] if payload.get("to") else {}
        
        # Default template variables
        html_content = template.render(
            user_name=to_data.get("name", "User"),
            company_name=template_data.get("company_name", "Our Company"),
            login_url=template_data.get("login_url", "#"),
            support_url=template_data.get("support_url", "#"),
            year=template_data.get("year", "2026"),
        )
        
        status_code, response = send_email(
            from_email=from_data.get("email", ""),
            from_name=from_data.get("name", ""),
            to_email=to_data.get("email", ""),
            to_name=to_data.get("name", ""),
            subject=payload.get("subject", ""),
            html_content=html_content,
        )
        
        # Update log status (2xx is success)
        log.status = "sent" if 200 <= status_code < 300 else "failed"
        log.response = response
        db.commit()
        
    except Exception as e:
        # Update log with error
        if log:
            log.status = "failed"
            log.response = str(e)
            db.commit()
    finally:
        db.close()


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Home page with API links."""
    links = [
        {"name": "API Docs (Swagger)", "url": "/docs"},
        {"name": "API Docs (ReDoc)", "url": "/redoc"},
        {"name": "Send Email (POST)", "url": "/send-email"},
        {"name": "Email Status UI", "url": "/status"},
        {"name": "Email Status API", "url": "/api/status"},
        {"name": "Health Check", "url": "/health"},
    ]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "links": links,
        },
    )


@router.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/send-email")
def send_mail(
    data: EmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Queue an email for sending in the background.
    
    Returns immediately with queued status. Email is sent asynchronously.
    """
    # Build the email payload
    payload = {
        "from": {"email": data.sender_email, "name": data.sender_name},
        "to": [{"email": data.receiver_email, "name": data.receiver_name}],
        "subject": data.subject,
        "html": data.content
    }

    # Create log entry with pending status
    log = EmailLog(
        sender_email=data.sender_email,
        receiver_email=data.receiver_email,
        subject=data.subject,
        status="pending",
        response="Email queued for sending"
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # Add email sending to background tasks
    background_tasks.add_task(send_email_background, log.id, payload)

    return {
        "status": "queued",
        "email_id": log.id,
        "message": "Email queued for sending in background"
    }


@router.get("/status", response_class=HTMLResponse)
def status_page(request: Request):
    """Email status UI page."""
    return templates.TemplateResponse("status.html", {"request": request})


@router.get("/api/status")
def email_status(
    page: int = 1,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Get paginated email status list.
    
    Args:
        page: Page number (1-indexed)
        status: Optional filter by status (pending, sent, failed)
    """
    query = db.query(EmailLog)
    if status:
        query = query.filter(EmailLog.status == status)

    per_page = 10
    total = query.count()
    emails = query.order_by(EmailLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "data": [
            {
                "id": e.id,
                "sender": e.sender_email,
                "receiver": e.receiver_email,
                "subject": e.subject,
                "status": e.status,
                "response": e.response,
                "created_at": e.created_at
            } for e in emails
        ]
    }
