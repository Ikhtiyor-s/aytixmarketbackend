from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.dependencies import get_current_admin
from app.models import User, FAQ
from app.schemas import FAQCreate, FAQUpdate, FAQResponse

router = APIRouter(prefix="/faq", tags=["faq"])


@router.get("/public", response_model=List[FAQResponse])
async def get_public_faqs(
    category: str = None,
    db: Session = Depends(get_db)
):
    """Get all active FAQs for public display (no auth required)."""
    query = db.query(FAQ).filter(FAQ.status == "active")
    if category:
        query = query.filter(FAQ.category == category)
    faqs = query.order_by(FAQ.order, FAQ.created_at.desc()).all()
    return faqs


@router.get("/", response_model=List[FAQResponse])
async def get_all_faqs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all FAQs (admin only)."""
    faqs = db.query(FAQ).order_by(FAQ.order, FAQ.created_at.desc()).all()
    return faqs


@router.get("/{faq_id}", response_model=FAQResponse)
async def get_faq(
    faq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get a single FAQ by ID."""
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return faq


@router.post("/", response_model=FAQResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(
    faq_data: FAQCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new FAQ (admin only)."""
    faq = FAQ(**faq_data.model_dump())
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return faq


@router.put("/{faq_id}", response_model=FAQResponse)
async def update_faq(
    faq_id: int,
    faq_data: FAQUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a FAQ (admin only)."""
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    update_data = faq_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(faq, field, value)

    db.commit()
    db.refresh(faq)
    return faq


@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(
    faq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a FAQ (admin only)."""
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    db.delete(faq)
    db.commit()
    return None
