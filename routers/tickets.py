from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Asset, Ticket, User
from schemas import TicketCreate, TicketOut, TicketUpdate

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("", response_model=list[TicketOut])
def get_all_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return db.query(Ticket).all()


@router.get("/my", response_model=list[TicketOut])
def get_my_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Ticket).filter(Ticket.created_by == current_user.id).all()


@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    asset = db.query(Asset).filter(Asset.id == payload.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    ticket = Ticket(
        asset_id=payload.asset_id,
        description=payload.description.strip(),
        priority=payload.priority,
        created_by=current_user.id,
        status="Open",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if current_user.role == "admin":
        if payload.description is not None:
            if not payload.description.strip():
                raise HTTPException(status_code=400, detail="Description cannot be empty")
            ticket.description = payload.description.strip()
        if payload.priority is not None:
            ticket.priority = payload.priority
        if payload.status is not None:
            ticket.status = payload.status
    else:
        if ticket.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update your own tickets")
        if ticket.status != "Open":
            raise HTTPException(status_code=403, detail="Only open tickets can be updated")
        if payload.status is not None and payload.status != "Open":
            raise HTTPException(status_code=403, detail="Regular users cannot change ticket status")

        if payload.description is not None:
            if not payload.description.strip():
                raise HTTPException(status_code=400, detail="Description cannot be empty")
            ticket.description = payload.description.strip()
        if payload.priority is not None:
            ticket.priority = payload.priority

    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}", status_code=204)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    db.delete(ticket)
    db.commit()
    return None
