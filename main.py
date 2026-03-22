

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

# ✅ OPTIONS handler (AFTER app is created)
@app.options("/{rest_of_path:path}")
async def preflight_handler():
    return {"message": "OK"}

# =========================
# CORS CONFIG
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ticketing-frontend-blao.vercel.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
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

# ✅ FIXED: return FULL payload
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload   # ✅ contains sub + role
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# =========================
# LOGIN API (DB-based)
# =========================
@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": user.username,
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role
    }

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
    user: dict = Depends(get_current_user)
):
    return db.query(models.Ticket).all()

# =========================
# UPDATE STATUS (ADMIN ONLY)
# =========================
ALLOWED_STATUS = ["Open", "In Progress", "Resolved"]

@app.put("/tickets/{ticket_id}")
def update_status(
    ticket_id: int,
    status: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    # 🔐 ROLE CHECK
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # ✅ Status validation
    if status not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, detail="Invalid status")

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = status
    db.commit()
    db.refresh(ticket)

    return ticket