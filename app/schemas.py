from datetime import datetime

from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_creator: bool = False
    
class UserCreate(UserBase):
    password: str
    
class UserLogin(BaseModel):
    username: str
    password: str
    
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr

class EventBase(BaseModel):
    name: str
    details: str
    date: datetime
    
class Event(EventBase):
    id: int
    creator_id: int

class Eventout(EventBase):
    creator_name: str
    link: str

class EventCreate(EventBase):
    available_tickets: int

class EventAttendeeBase(BaseModel):
    event_id: int
    
class EventAttendeeCreate(EventAttendeeBase):
    pass

class Link(BaseModel):
    link: str

    
class NotificationBase(BaseModel):
    reminder_day: datetime
    message: str

class NotificationCreate(NotificationBase):
    pass

class Notification(NotificationBase):
    id: int
    user_email: EmailStr
    
    class Config:
        ofrom_attributes = True
    
class Token(BaseModel):
    access_token: str
    type: str

