from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import BusinessSettings, InstagramAccount
from app.schemas.schemas import BusinessSettingsUpdate, BusinessSettingsResponse
from app.api.deps import get_current_instagram_account

router = APIRouter()


@router.get("", response_model=BusinessSettingsResponse)
def get_business_settings(
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    settings = db.query(BusinessSettings).filter(
        BusinessSettings.instagram_account_id == account.id
    ).first()

    if not settings:
        settings = BusinessSettings(instagram_account_id=account.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


@router.patch("", response_model=BusinessSettingsResponse)
def update_business_settings(
    update_data: BusinessSettingsUpdate,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    settings = db.query(BusinessSettings).filter(
        BusinessSettings.instagram_account_id == account.id
    ).first()

    if not settings:
        settings = BusinessSettings(instagram_account_id=account.id)
        db.add(settings)

    for field, val in update_data.model_dump(exclude_unset=True).items():
        setattr(settings, field, val)

    db.commit()
    db.refresh(settings)
    return settings
