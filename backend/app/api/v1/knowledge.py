from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.models import KnowledgeDocument, InstagramAccount
from app.schemas.schemas import (
    KnowledgeDocCreate, KnowledgeDocUpdate, KnowledgeDocResponse
)
from app.api.deps import get_current_instagram_account

router = APIRouter()

DEFAULT_FAQS = [
    {
        "category": "faq",
        "title": "Hallmarking & Certification",
        "content": "All our gold jewellery is 100% BIS Hallmarked (with HUID laser inscription). Our diamond jewellery comes with authentic IGI / SGL certificates specifying carat, clarity, and color."
    },
    {
        "category": "store_policy",
        "title": "Return and Exchange Policy",
        "content": "We offer a 7-day hassle-free return or exchange policy on undamaged items with original invoice and certificate. We also offer lifetime gold buyback at current market gold rate minus making charges."
    },
    {
        "category": "shipping",
        "title": "Insured Shipping & Delivery",
        "content": "We offer 100% fully insured, tamper-proof courier delivery across all pin codes in India within 3-5 business days. International shipping is available upon custom inquiry."
    },
    {
        "category": "custom_orders",
        "title": "Custom Bespoke Jewellery",
        "content": "We specialize in personalized bridal and everyday custom designs. Share your reference photograph, budget, and gold purity preference, and our CAD artisans will craft your bespoke design within 10-14 days."
    }
]


@router.get("", response_model=List[KnowledgeDocResponse])
def list_knowledge_docs(
    category: Optional[str] = None,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    query = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.instagram_account_id == account.id
    )
    if category:
        query = query.filter(KnowledgeDocument.category == category)

    docs = query.order_by(desc(KnowledgeDocument.created_at)).all()

    # Seed default FAQs if empty
    if not docs:
        for f in DEFAULT_FAQS:
            doc = KnowledgeDocument(
                instagram_account_id=account.id,
                category=f["category"],
                title=f["title"],
                content=f["content"],
                is_active=True
            )
            db.add(doc)
        db.commit()
        docs = query.order_by(desc(KnowledgeDocument.created_at)).all()

    return docs


@router.post("", response_model=KnowledgeDocResponse)
def create_knowledge_doc(
    data: KnowledgeDocCreate,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    doc = KnowledgeDocument(
        instagram_account_id=account.id,
        category=data.category,
        title=data.title,
        content=data.content,
        is_active=data.is_active
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.patch("/{doc_id}", response_model=KnowledgeDocResponse)
def update_knowledge_doc(
    doc_id: str,
    data: KnowledgeDocUpdate,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.instagram_account_id == account.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(doc, field, val)

    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{doc_id}")
def delete_knowledge_doc(
    doc_id: str,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.instagram_account_id == account.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(doc)
    db.commit()
    return {"message": "Knowledge document deleted"}
