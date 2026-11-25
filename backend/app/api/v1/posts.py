from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.models import (
    PostProductLink, ProcessedComment, Product,
    InstagramAccount, User
)
from app.schemas.schemas import (
    PostProductLinkCreate, PostProductLinkUpdate,
    PostProductLinkResponse, InstagramMediaItem,
    ProcessedCommentResponse, ProductResponse
)
from app.api.deps import get_current_instagram_account, get_current_user
from app.core.security import decrypt_token
from app.services.instagram.client import instagram_client

router = APIRouter()


@router.get("", response_model=List[InstagramMediaItem])
async def list_instagram_posts(
    limit: int = Query(25, ge=1, le=50),
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """
    Fetch recent Instagram posts and reels for the connected account
    and merge existing product link metadata.
    """
    access_token = decrypt_token(account.token_encrypted)
    try:
        media_items = await instagram_client.get_recent_media(access_token=access_token, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch posts from Meta Graph API: {str(e)}"
        )

    # Fetch existing links for this account
    existing_links = db.query(PostProductLink).filter(
        PostProductLink.instagram_account_id == account.id,
        PostProductLink.is_active == True
    ).all()
    link_map = {l.media_id: l for l in existing_links}

    results: List[InstagramMediaItem] = []
    for m in media_items:
        m_id = str(m.get("id"))
        link = link_map.get(m_id)
        results.append(
            InstagramMediaItem(
                id=m_id,
                caption=m.get("caption"),
                media_type=m.get("media_type", "VIDEO"),
                media_url=m.get("media_url"),
                permalink=m.get("permalink"),
                thumbnail_url=m.get("thumbnail_url") or m.get("media_url"),
                timestamp=m.get("timestamp"),
                linked_product_ids=link.product_ids if link else [],
                is_linked=bool(link and link.product_ids),
                auto_dm_enabled=link.auto_dm_enabled if link else True
            )
        )

    return results


@router.get("/links", response_model=List[PostProductLinkResponse])
def list_post_links(
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """
    List all linked posts and reels for this account with full product details.
    """
    links = db.query(PostProductLink).filter(
        PostProductLink.instagram_account_id == account.id
    ).order_by(desc(PostProductLink.created_at)).all()

    response: List[PostProductLinkResponse] = []
    for link in links:
        products = []
        if link.product_ids:
            products = db.query(Product).filter(
                Product.id.in_(link.product_ids),
                Product.instagram_account_id == account.id
            ).all()

        p_responses = [ProductResponse.from_orm(p) for p in products]

        response.append(
            PostProductLinkResponse(
                id=link.id,
                instagram_account_id=link.instagram_account_id,
                media_id=link.media_id,
                media_type=link.media_type,
                permalink=link.permalink,
                caption=link.caption,
                thumbnail_url=link.thumbnail_url,
                product_ids=link.product_ids or [],
                products=p_responses,
                custom_reply_template=link.custom_reply_template,
                auto_dm_enabled=link.auto_dm_enabled,
                public_reply_enabled=link.public_reply_enabled,
                public_reply_text=link.public_reply_text,
                is_active=link.is_active,
                created_at=link.created_at,
                updated_at=link.updated_at
            )
        )

    return response


@router.post("/link", response_model=PostProductLinkResponse)
def create_or_update_post_link(
    data: PostProductLinkCreate,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """
    Link one or more catalogue products to an Instagram Post or Reel.
    Validates that product IDs belong strictly to the authenticated account.
    """
    # Validate product IDs
    if data.product_ids:
        valid_prods = db.query(Product).filter(
            Product.id.in_(data.product_ids),
            Product.instagram_account_id == account.id
        ).all()
        if len(valid_prods) != len(data.product_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more specified product IDs do not belong to your catalogue."
            )
    else:
        valid_prods = []

    # Check if link already exists for this media_id
    link = db.query(PostProductLink).filter(
        PostProductLink.instagram_account_id == account.id,
        PostProductLink.media_id == data.media_id
    ).first()

    if link:
        link.product_ids = data.product_ids
        link.media_type = data.media_type or link.media_type
        link.permalink = data.permalink or link.permalink
        link.caption = data.caption or link.caption
        link.thumbnail_url = data.thumbnail_url or link.thumbnail_url
        link.custom_reply_template = data.custom_reply_template
        link.auto_dm_enabled = data.auto_dm_enabled
        link.public_reply_enabled = data.public_reply_enabled
        link.public_reply_text = data.public_reply_text
        link.is_active = True
    else:
        link = PostProductLink(
            instagram_account_id=account.id,
            media_id=data.media_id,
            media_type=data.media_type or "VIDEO",
            permalink=data.permalink,
            caption=data.caption,
            thumbnail_url=data.thumbnail_url,
            product_ids=data.product_ids,
            custom_reply_template=data.custom_reply_template,
            auto_dm_enabled=data.auto_dm_enabled,
            public_reply_enabled=data.public_reply_enabled,
            public_reply_text=data.public_reply_text,
            is_active=True
        )
        db.add(link)

    db.commit()
    db.refresh(link)

    p_responses = [ProductResponse.from_orm(p) for p in valid_prods]

    return PostProductLinkResponse(
        id=link.id,
        instagram_account_id=link.instagram_account_id,
        media_id=link.media_id,
        media_type=link.media_type,
        permalink=link.permalink,
        caption=link.caption,
        thumbnail_url=link.thumbnail_url,
        product_ids=link.product_ids or [],
        products=p_responses,
        custom_reply_template=link.custom_reply_template,
        auto_dm_enabled=link.auto_dm_enabled,
        public_reply_enabled=link.public_reply_enabled,
        public_reply_text=link.public_reply_text,
        is_active=link.is_active,
        created_at=link.created_at,
        updated_at=link.updated_at
    )


@router.put("/link/{link_id}", response_model=PostProductLinkResponse)
def update_post_link(
    link_id: str,
    data: PostProductLinkUpdate,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """
    Update post-to-product mapping settings.
    """
    link = db.query(PostProductLink).filter(
        PostProductLink.id == link_id,
        PostProductLink.instagram_account_id == account.id
    ).first()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found.")

    if data.product_ids is not None:
        valid_prods = db.query(Product).filter(
            Product.id.in_(data.product_ids),
            Product.instagram_account_id == account.id
        ).all()
        if len(valid_prods) != len(data.product_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more specified product IDs do not belong to your catalogue."
            )
        link.product_ids = data.product_ids
    else:
        valid_prods = db.query(Product).filter(
            Product.id.in_(link.product_ids or []),
            Product.instagram_account_id == account.id
        ).all()

    if data.custom_reply_template is not None:
        link.custom_reply_template = data.custom_reply_template
    if data.auto_dm_enabled is not None:
        link.auto_dm_enabled = data.auto_dm_enabled
    if data.public_reply_enabled is not None:
        link.public_reply_enabled = data.public_reply_enabled
    if data.public_reply_text is not None:
        link.public_reply_text = data.public_reply_text
    if data.is_active is not None:
        link.is_active = data.is_active

    db.commit()
    db.refresh(link)

    p_responses = [ProductResponse.from_orm(p) for p in valid_prods]

    return PostProductLinkResponse(
        id=link.id,
        instagram_account_id=link.instagram_account_id,
        media_id=link.media_id,
        media_type=link.media_type,
        permalink=link.permalink,
        caption=link.caption,
        thumbnail_url=link.thumbnail_url,
        product_ids=link.product_ids or [],
        products=p_responses,
        custom_reply_template=link.custom_reply_template,
        auto_dm_enabled=link.auto_dm_enabled,
        public_reply_enabled=link.public_reply_enabled,
        public_reply_text=link.public_reply_text,
        is_active=link.is_active,
        created_at=link.created_at,
        updated_at=link.updated_at
    )


@router.delete("/link/{link_id}")
def delete_post_link(
    link_id: str,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """
    Remove product links from a post or reel.
    """
    link = db.query(PostProductLink).filter(
        PostProductLink.id == link_id,
        PostProductLink.instagram_account_id == account.id
    ).first()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found.")

    db.delete(link)
    db.commit()
    return {"message": "Link deleted successfully."}


@router.get("/activity", response_model=List[ProcessedCommentResponse])
def get_comment_activity(
    limit: int = Query(50, ge=1, le=100),
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """
    View activity log of processed comments and auto-sent private DMs.
    """
    comments = db.query(ProcessedComment).filter(
        ProcessedComment.instagram_account_id == account.id
    ).order_by(desc(ProcessedComment.created_at)).limit(limit).all()

    return comments
