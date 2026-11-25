import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure test environment
os.environ["TESTING"] = "True"
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["MOCK_INSTAGRAM_API"] = "True"
os.environ["MOCK_AI_PROVIDER"] = "True"
os.environ["INSTAGRAM_APP_SECRET"] = "test_app_secret_12345"
os.environ["INSTAGRAM_WEBHOOK_VERIFY_TOKEN"] = "jewelai_verify_token_secure_2026"

from app.core.database import Base, get_db
from app.main import app
from app.models.models import User, InstagramAccount, BusinessSettings
from app.core.security import hash_password, encrypt_token
from app.services.catalogue.catalogue_service import CatalogueService
from app.api.deps import get_current_user, get_current_instagram_account

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    
    # Create test owner
    user = User(
        name="Test Owner",
        email="owner@jewelai.com",
        password_hash=hash_password("testpass123"),
        role="owner"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create connected test Instagram Account
    account = InstagramAccount(
        user_id=user.id,
        ig_user_id="17841400009999999",
        username="luxeaurajewels_test",
        name="Luxe Aura Test Account",
        token_encrypted=encrypt_token("test_meta_long_lived_token_xyz"),
        is_connected=True,
        webhook_subscribed=True
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    # Create business settings
    settings = BusinessSettings(
        instagram_account_id=account.id,
        business_name="Luxe Aura Jewels",
        auto_reply_enabled=True,
        gold_rate_24k_per_10g=78500.0,
        gold_rate_22k_per_10g=72000.0,
        gold_rate_18k_per_10g=58900.0
    )
    db.add(settings)
    db.commit()

    # Seed products
    cat_service = CatalogueService(db)
    cat_service.seed_initial_products_if_empty(account.id)

    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_user():
        return db_session.query(User).first()

    def override_get_account():
        return db_session.query(InstagramAccount).first()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_user
    app.dependency_overrides[get_current_instagram_account] = override_get_account
    
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
