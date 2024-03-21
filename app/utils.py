from passlib.context import CryptContext
from sqlalchemy.orm import Session
from email.message import EmailMessage
from fastapi import Depends, HTTPException, status, Request
from database import get_db
from pydantic import EmailStr
from config import settings
from datetime import datetime, timezone
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from celery import Celery
import qrcode, smtplib, os
import redis


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

celery = Celery("tasks", broker="redis://localhost:6379/0")

templates = Jinja2Templates(directory="templates")


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def generate_qr_code(user_id: int, username: str, event_name: str, filename):
    qr_data = f"Username: {username}\nUser ID: {user_id}\nEvent Name: {event_name}"
    qr = qrcode.QRCode(
        version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)

@celery.task
def send_mail(receiver_email: EmailStr, subject: str = None, body: str = None, attachment_filename=None):

    msg = EmailMessage()

    msg['From'] = settings.email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.set_content(body)

    with open(attachment_filename, 'rb') as file:
        file_data = file.read()
        msg.add_attachment(file_data, maintype='image', subtype='png', filename=attachment_filename)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(settings.email, settings.email_password)
            smtp.send_message(msg)
            print("Email sent successfully")
    except Exception as e:
        
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail=e)
    finally:
        os.remove(attachment_filename)
        

def send_notification(reminder_time, user_email, event_name, event_date, db: Session = Depends(get_db)):

    current_time = datetime.now()
    current_time_aware = current_time.replace(tzinfo=timezone.utc)
    if current_time_aware == reminder_time:
        subject = f"Notification for the upcoming {event_name}!"
        body = f"This is to notify you of the upcoming {event_name}, which is scheduled to hold on the {event_date}"
        try:
            send_mail.apply_async(args=[user_email, subject, body], eta = reminder_time)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail=e)


def generate_shareable_link(event_name: str) -> str:
    
    return f"http://localhost:8000/events/{event_name}"


def handle_authentication(request: Request, current_user: str, page, **kwargs):
    if current_user is None:
        return RedirectResponse("/auth", status_code=status.HTTP_302_FOUND)
    context = {"request": request, "user": current_user}
    context.update(kwargs)
    return templates.TemplateResponse(page, context)
