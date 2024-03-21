from models import Base
from fastapi import FastAPI, Request
from database import engine
from routers import user, event, auth
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles



templates = Jinja2Templates(directory="templates")



Base.metadata.create_all(bind=engine)
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(user.router)
app.include_router(event.router)
app.include_router(auth.router)

# Root route
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Fetch data for the home route
    return templates.TemplateResponse("home.html", {"request": request})