from fastapi import APIRouter, Depends, Request, status, HTTPException, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from oauth2 import create_access_token
import schemas,models, utils
from fastapi.responses import Response, HTMLResponse, RedirectResponse
from datetime import timedelta
from fastapi.templating import Jinja2Templates
from typing import Optional

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix='/auth',
    tags=["Authentication"]
)

@router.post('/token', response_model=schemas.Token)
async def token_generate(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
   user = db.query(models.User).filter(models.User.username == form_data['username']).first()
   if not user:
       return False
   if not utils.verify(form_data['password'], user.password):
       return False
   access_token = create_access_token(data = {'user_id': user.id, "creator": user.is_creator, "username": user.username})
   
   response.set_cookie(key="access_token", value=access_token, httponly=True)
   
   return True    



@router.get("/", response_class=HTMLResponse)
async def authenticationpage(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        title = "Welcome!"
        msg = f'Good to have you {username}'

        response = templates.TemplateResponse('index.html', {'request':request, 'title': title, 'msg': msg})
        validate_user_cookie = await token_generate(response=response, form_data={'username': username, 'password': password}, db=db)
        
        if not validate_user_cookie: 
            msg = "invalid username or password"
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        
        return response
    
    except HTTPException:
        msg = "Unknown error"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    
    
@router.get('/logout', response_class=HTMLResponse)
async def logout(request:Request):
    msg = "Logged out successfully"
    response = templates.TemplateResponse("home.html", {"request": request, "msg": msg})
    response.delete_cookie(key="access_token")
    return response