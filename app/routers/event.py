import models, oauth2, utils
from typing import List
from database import get_db
from fastapi import APIRouter, Depends, status, BackgroundTasks, Request, Form, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import pytz
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse

templates = Jinja2Templates(directory="templates")


router = APIRouter(
    tags=['Events'],
    prefix='/event'
)

@router.get('/', response_class=HTMLResponse)
async def get_all_events(request: Request, db: Session = Depends(get_db)):
    events = db.query(models.Event).all()
    
    return templates.TemplateResponse("event.html", {"request": request, "events": events})


@router.get("/my_events", response_class=HTMLResponse)
async def get_my_events(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(oauth2.get_current_user)):
    if current_user == None:
        return templates.TemplateResponse("login.html", {'request': request})
    else:
        events1 = db.query(models.Event).filter(models.Event.creator_id == current_user['id']).all()
        events2 = db.query(models.Event).join(models.Ticket).filter(models.Ticket.attendee_id == current_user['id']).all()
        if current_user['creator']:
            response = utils.handle_authentication(request, current_user, 'event.html', events=events1)
        else:
            response = utils.handle_authentication(request, current_user, 'event.html', events=events2)
        
    
    return response

@router.get("/events_by_name", response_class=HTMLResponse)
async def get_events_by_name(request: Request, 
                              event_name: str = Query(..., description="Name of the event to search for"),
                              db: Session = Depends(get_db)):
    events = db.query(models.Event).filter(models.Event.name == event_name).all()
    return templates.TemplateResponse("event.html", {'request': request, 'events': events, 'event_name': event_name})
    


@router.get('/create_event', response_class=HTMLResponse)
async def show_create_event_page(request: Request, current_user: dict = Depends(oauth2.get_current_user)):
    return utils.handle_authentication(request, current_user, 'create_event.html')

@router.post("/event_create", response_class=HTMLResponse)
async def create_event(request: Request, db: Session = Depends(get_db), 
                     name: str = Form(...),
                     details: str = Form(...),
                     date: datetime = Form(...),
                     available_tickets = Form(...),
                     current_user: dict = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(models.User.id == current_user['id']).first()
    if current_user is None:
        return RedirectResponse('/auth/login', status_code=status.HTTP_302_FOUND)
    
    if not current_user['creator']:
        title = 'Error'
        header = 'Not Allowed'
        message = "Upgrade your account to be able to create events"
        return templates.TemplateResponse("plain.html", {"request": request, 'title': title, 'message': message, 'header': header})
    
    
    link = utils.generate_shareable_link(name)
    new_event = models.Event(
        creator_name= user.username,
        creator_id= user.id,
        link=link,
        name = name,
        details=details,
        date=date,
        available_tickets=available_tickets
    )
    db.add(new_event)
    db.commit()
    return RedirectResponse('/event/my_events', status_code=status.HTTP_302_FOUND)

@router.get('/book_event', response_class=HTMLResponse)
async def show_book_event_page(request: Request, event_name = str, current_user: dict = Depends(oauth2.get_current_user), db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.name == event_name).first()
    return utils.handle_authentication(request, current_user, 'book_event.html', event=event)
    

@router.post('/book_event')
async def book_event(request: Request, 
                     event_id: int,
                     number_of_tickets: int = Form(...),
                     db: Session = Depends(get_db), 
                     current_user: dict = Depends(oauth2.get_current_user)):
    
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    user = db.query(models.User).filter(models.User.id == current_user['id']).first()

    if event is None:
        return templates.TemplateResponse("plain.html", {'request': request, 'title': 'Error', 'header': 'Event Not Found!'})
    if event.available_tickets <= 0 or event.available_tickets < number_of_tickets:
        return templates.TemplateResponse("plain.html", {'request': request, 'header': f'We have {event.available_tickets} ticket(s) left!'})
    event.available_tickets -= number_of_tickets
    
    utils.generate_qr_code(current_user['id'], current_user['username'], event.name, 'qrcode.png')
    
    ticket_purchase_subject = f'Thank you for purchasing tickets for the {event.name} event'
    body = f'Hello,\n\nThank you for purchasing tickets for the event: {event.name}.\n\nPlease find your ticket QR code attached.\n\nBest regards,\nYour Event Team'
    try:
        utils.send_mail(user.email, ticket_purchase_subject, body, 'qrcode.png')
    except Exception as e:
        event.available_tickets += 1
        db.commit() 
        return templates.TemplateResponse("plain.html", {'request': request, "header": 'Ticket(s) not purchased, please try again later!'})
    
    booking = models.Ticket(attendee_id = current_user['id'], event_id = event_id)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    header = f"Hello {current_user['username']}, you have successfully booked for the {event.name} event."
    return templates.TemplateResponse("congrats.html", {'request': request, 'header': header, 'event': event, 'number_of_tickets': number_of_tickets})


@router.post('/schedule_notification', response_class=HTMLResponse)
async def schedule_notifications(request: Request,
                                background_tasks: BackgroundTasks,
                                event_id: int,
                                reminder_day: datetime = Form(...),
                                message: str = Form(...),
                                db: Session = Depends(get_db), 
                                current_user: str = Depends(oauth2.get_current_user)):
    
    ticket = db.query(models.Ticket).filter(models.Ticket.event_id == event_id).first()
    user = db.query(models.User).filter(models.User.id == current_user['id']).first()
    if ticket :
        event = db.query(models.Event).filter(models.Event.id == event_id).first()
        now_utc1 = datetime.now(timezone.utc).astimezone(pytz.timezone('Africa/Lagos'))
        event_date_utc1 = event.date.astimezone(pytz.timezone('Africa/Lagos'))
        if event_date_utc1 < now_utc1:
            return templates.TemplateResponse('plain.html', {'request': request, 'header': f'{event.name} event already passed'})
        
        background_tasks.add_task(utils.send_notification, reminder_day, user.email, event.name, event.date)
        new_notification = models.Notification(
            user_email=user.email,
            message = message,
            reminder_day = reminder_day
            )
        
        db.add(new_notification)
        db.commit()
    
    return templates.TemplateResponse("plain.html", {'request': request, 'header': 'Reminder set!', 'reminder_day': reminder_day, 'message': message, 'event_id': event_id})

@router.get("/get_link", response_class=HTMLResponse)
async def get_link(request: Request, event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    msg = event.link
    header = f"Here's the link to the {event.name} event. You can share it on all your social media platforms."
    anchor_url = event.link  
    anchor_text = "Click here to visit the event page"  
    return templates.TemplateResponse("plain.html", {'request': request, 'header': header, 'msg': msg, 'anchor_url': anchor_url, 'anchor_text': anchor_text})
