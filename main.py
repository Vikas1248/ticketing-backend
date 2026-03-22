from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta

from database import SessionLocal, engine, Base
import models

# =========================
# APP INIT
# =========================
app = FastAPI()

# =========================
# CORS CONFIG
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# =========================
# LOGIN API
# =========================
@app.post("/login")
def login(username: str, password: str):
    if username == "admin" and password == "admin123":
        token = create_access_token({"sub": username})
        return {
            "access_token": token,
            "token_type": "bearer"
        }

    raise HTTPException(status_code=401, detail="Invalid credentials")

# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def home():
    return {"message": "Backend running 🚀"}

# =========================
# CREATE TICKET (PUBLIC)
# =========================
@app.post("/tickets")
def create_ticket(data: dict, db: Session = Depends(get_db)):
    ticket = models.Ticket(
        title=data["title"],
        description=data["description"],
        email=data["email"]
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

# =========================
# GET TICKETS (PROTECTED)
# =========================
@app.get("/tickets")
def get_tickets(
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)  # 🔐 Protected
):
    return db.query(models.Ticket).all()

# =========================
# UPDATE STATUS (PROTECTED)
# =========================
ALLOWED_STATUS = ["Open", "In Progress", "Resolved"]

@app.put("/tickets/{ticket_id}")
def update_status(
    ticket_id: int,
    status: str,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)  # 🔐 Protected
):
    if status not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, detail="Invalid status")

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = status
    db.commit()
    db.refresh(ticket)

    return ticket