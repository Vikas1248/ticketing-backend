from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models

Base.metadata.create_all(bind=engine)

app = FastAPI()

# ✅ ADD THIS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "Backend running 🚀"}

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

@app.get("/tickets")
def get_tickets(db: Session = Depends(get_db)):
    return db.query(models.Ticket).all()