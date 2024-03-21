import utils, models, oauth2
from sqlalchemy.orm import Session
from fastapi import Depends, status, APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from database import get_db
from typing import List
import utils
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix= "/user",
    tags=['Users']
)

@router.get('/create_account', response_class=HTMLResponse)
async def create_user_page(request: Request):
    return templates.TemplateResponse("create_account.html", {'request':request})

@router.post('/create_account', response_class=HTMLResponse)
async def create_user(request: Request, 
                      username: str = Form(...),
                      email: EmailStr = Form(...),
                      is_creator: bool = Form(False),
                      password: str = Form(...),
                      db: Session = Depends(get_db)):
    existing_username = db.query(models.User.username).filter(models.User.username == username).first()
    existing_email = db.query(models.User.email).filter(models.User.email == email).first()
    if existing_email or existing_username:
        header = 'Username or email already exists!'
        message1 = 'Change username or email and try again'
        return templates.TemplateResponse("plain.html", {'request': request, 'header': header, 'message': message1})
    hashed_password = utils.hash(password)
    password = hashed_password
    new_user = models.User(
        username = username,
        email = email, 
        is_creator = is_creator,
        password = hashed_password
    )
    db.add(new_user)
    db.commit()
    message = f'Good to have you {username}'
    title = 'Welcome!'
    if is_creator:
        return templates.TemplateResponse("user_page_creator.html", {'request': request, 'message': message, 'title': title})
    else:
        return templates.TemplateResponse("user_page.html", {'request': request, 'message': message, 'title': title})
        


@router.get("/attendees", response_class=HTMLResponse)
async def get_attendees_by_event(request: Request, event_id: int, db: Session = Depends(get_db), current_user: str = Depends(oauth2.get_current_user)):
    created_events = db.query(models.Event).filter(models.Event.creator_id ==current_user['id']).all()
    attendees = []
    for event in created_events:
        attendees.extend(db.query(models.User).join(models.Ticket).filter(event_id==event.id).all())
    return templates.TemplateResponse("attendees.html", {"request": request, "attendees": attendees, 'event_id': event_id})

@router.get('/account_update', response_class=HTMLResponse)
async def account_update_page(request:Request):
    return templates.TemplateResponse('create_account.html', {request:request})

@router.post('/account_update')
async def account_update(request: Request, 
                         is_creator: bool = Form(...),
                         current_user: dict = Depends(oauth2.get_current_user), 
                         db = Session(get_db)):
    user = db.query(models.User).filter(models.User.id == current_user['user_id']).first()
    
    if user:
        user.is_creator = is_creator
        db.commit()
        title = "Account Changed"
        header = 'Successful change of account'
        if is_creator:
            message = 'Congrats you are now a creator'
            return templates.TemplateResponse('plain.html', {'request': request, 'title': title, 'header': header, 'message': message})
        else:
            message = "You are no longer a creator"
            return templates.TemplateResponse('plain.html', {'request': request, 'title': title, 'header': header, 'message': message})
    else:
        return RedirectResponse("/auth", status_code=status.HTTP_302_FOUND)
            
@router.get('/my_page', response_class=HTMLResponse)
async def my_page(request: Request, current_user = Depends(oauth2.get_current_user)):
    if current_user == None:
       return templates.TemplateResponse("login.html", {'request':request})
    elif current_user['creator']:
        return templates.TemplateResponse("user_page_creator.html", {'request': request})
    elif not current_user['creator']:
        return templates.TemplateResponse("user_page.html", {'request': request})
    
