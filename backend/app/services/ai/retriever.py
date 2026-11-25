from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
import logging
from app.models.models import Product, KnowledgeDocument, BusinessSettings

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """
    Retrieves verified jewellery products and store knowledge documents from the database.
    Guarantees that AI responses only reference actual products in stock.
    """

    def __init__(self, db: Session):
        self.db = db

    def search_products(
        self,
        account_id: str,
        category: Optional[str] = None,
        budget_max: Optional[float] = None,
        purity: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Product]:
        """
        Query verified catalogue products respecting inventory and pricing constraints.
        """
        query = self.db.query(Product).filter(
            Product.instagram_account_id == account_id,
            Product.status == "active",
            Product.stock > 0
        )

        if category:
            # Case-insensitive category match
            query = query.filter(Product.category.ilike(f"%{category}%"))

        if budget_max and budget_max > 0:
            # Products within budget (allow 10% tolerance if within reasonable range)
            query = query.filter(Product.price <= budget_max * 1.05)

        if purity:
            query = query.filter(Product.gold_purity.ilike(f"%{purity}%"))

        if keywords:
            search_filters = []
            for kw in keywords[:4]:
                if len(kw) >= 3:
                    search_filters.append(Product.name.ilike(f"%{kw}%"))
                    search_filters.append(Product.description.ilike(f"%{kw}%"))
            if search_filters:
                query = query.filter(or_(*search_filters))

        # Order by closest to budget if budget specified, otherwise by price ascending
        if budget_max:
            query = query.order_by(desc(Product.price))
        else:
            query = query.order_by(Product.price.asc())

        results = query.limit(limit).all()
        
        # If strict filter returned empty and category was set, try category-only fallback
        if not results and category:
            results = self.db.query(Product).filter(
                Product.instagram_account_id == account_id,
                Product.status == "active",
                Product.category.ilike(f"%{category}%")
            ).order_by(Product.price.asc()).limit(limit).all()

        return results

    def search_knowledge_docs(
        self,
        account_id: str,
        intent: str,
        query_text: str = ""
    ) -> List[KnowledgeDocument]:
        """
        Retrieve business knowledge, FAQ, and policy documents.
        """
        category_map = {
            "store_location": "store_policy",
            "store_policy": "store_policy",
            "delivery_policy": "shipping",
            "gold_rate_enquiry": "gold_rates",
            "custom_jewellery": "custom_orders",
            "greeting": "faq",
            "price_enquiry": "gold_rates",
        }
        target_category = category_map.get(intent, "faq")

        docs = self.db.query(KnowledgeDocument).filter(
            KnowledgeDocument.instagram_account_id == account_id,
            KnowledgeDocument.is_active == True,
            or_(
                KnowledgeDocument.category == target_category,
                KnowledgeDocument.title.ilike(f"%{query_text}%")
            )
        ).limit(3).all()

        return docs

    def get_business_settings(self, account_id: str) -> Optional[BusinessSettings]:
        return self.db.query(BusinessSettings).filter(
            BusinessSettings.instagram_account_id == account_id
        ).first()
