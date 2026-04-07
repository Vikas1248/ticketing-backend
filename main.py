from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta
from pydantic import BaseModel
from openai import OpenAI
import os

from database import SessionLocal, engine, Base
import models

# =========================
# APP INIT
# =========================
app = FastAPI()

# =========================
# CORS CONFIG (FIXED)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https://.*\.vercel\.app",  # handles all Vercel URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DB SETUP
# =========================
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# JWT CONFIG
# =========================
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# =========================
# SCHEMAS
# =========================
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str

class CommentCreate(BaseModel):
    message: str

class AssignRequest(BaseModel):
    agent_id: int

# =========================
# REGISTER
# =========================
@app.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        models.User.username == data.email
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        username=data.email,
        password=data.password,  # ⚠️ replace with hash later
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({
        "sub": new_user.username,
        "role": new_user.role,
        "user_id": new_user.id
    })

    return {
        "access_token": token,
        "role": new_user.role
    }

# =========================
# LOGIN
# =========================
@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == data.email
    ).first()

    if not user or user.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": user.username,
        "role": user.role,
        "user_id": user.id
    })

    return {
        "access_token": token,
        "role": user.role
    }

# =========================
# OPENAI SETUP
# =========================
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise Exception("OPENAI_API_KEY not set")

client = OpenAI(api_key=api_key)

# =========================
# AI REPLY
# =========================
@app.post("/tickets/{ticket_id}/ai-reply")
def generate_ai_reply(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    prompt = f"""
    A user raised a support ticket:

    Title: {ticket.title}
    Description: {ticket.description}

    Generate a helpful support reply.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return {"reply": response.choices[0].message.content}

# =========================
# CREATE TICKET
# =========================
@app.post("/tickets")
def create_ticket(
    data: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    ticket = models.Ticket(
        title=data["title"],
        description=data["description"],
        email=user["sub"],
        user_id=user["user_id"]
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket

# =========================
# GET TICKETS (RBAC)
# =========================
@app.get("/tickets")
def get_tickets(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    if user["role"] == "admin":
        return db.query(models.Ticket).all()

    elif user["role"] == "agent":
        return db.query(models.Ticket).filter(
            models.Ticket.assigned_to == user["user_id"]
        ).all()

    else:
        return db.query(models.Ticket).filter(
            models.Ticket.user_id == user["user_id"]
        ).all()

# =========================
# UPDATE STATUS (ADMIN)
# =========================
@app.put("/tickets/{ticket_id}")
def update_status(
    ticket_id: int,
    status: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    ticket = db.query(models.Ticket).filter(
        models.Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = status
    db.commit()
    db.refresh(ticket)

    return ticket

# =========================
# ASSIGN TICKET
# =========================
@app.put("/tickets/{ticket_id}/assign")
def assign_ticket(
    ticket_id: int,
    data: AssignRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    ticket = db.query(models.Ticket).filter(
        models.Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.assigned_to = data.agent_id
    db.commit()

    return {"message": "Ticket assigned successfully"}

# =========================
# COMMENTS
# =========================
@app.post("/tickets/{ticket_id}/comments")
def add_comment(
    ticket_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    new_comment = models.Comment(
        ticket_id=ticket_id,
        user_id=user["user_id"],
        message=comment.message
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment


@app.get("/tickets/{ticket_id}/comments")
def get_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    return db.query(models.Comment).filter(
        models.Comment.ticket_id == ticket_id
    ).all()

# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def home():
    return {"message": "Backend running 🚀"}
