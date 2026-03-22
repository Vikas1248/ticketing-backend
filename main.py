from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi import HTTPException
from database import SessionLocal, engine, Base
import models

ALLOWED_STATUS = ["Open", "In Progress", "Resolved"]

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


@app.put("/tickets/{ticket_id}")
def update_status(ticket_id: int, status: str, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = status
    db.commit()
    db.refresh(ticket)

    return ticket