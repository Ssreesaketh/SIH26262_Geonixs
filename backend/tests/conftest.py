import os
import shutil

TEST_DB_PATH = "./test_sih_workflow.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

os.environ["DATABASE_URL"] = SQLALCHEMY_DATABASE_URL
os.environ["ENVIRONMENT"] = "testing"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
import app.main as app_main
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.models.entities import Region, Institution, User, WorkflowTemplate
from app.seed_data import seed_database

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Patch main engine and sessionmaker so startup lifespan uses test SQLite
app_main.engine = engine
app_main.SessionLocal = TestingSessionLocal

@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

@pytest.fixture(autouse=True)
def reseed_per_test():
    db = TestingSessionLocal()
    seed_database(db, reset=True)
    db.close()
    yield

@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def officer_token(db_session):
    user = db_session.query(User).filter(User.email == "officer.north@aicte.gov.in").first()
    return create_access_token(
        subject=user.id,
        extra_claims={"role": user.role, "region_id": user.region_id, "institution_id": None}
    )

@pytest.fixture
def institution_token(db_session):
    user = db_session.query(User).filter(User.email == "principal@zenith.edu.in").first()
    return create_access_token(
        subject=user.id,
        extra_claims={"role": user.role, "region_id": user.region_id, "institution_id": user.institution_id}
    )

@pytest.fixture
def admin_token(db_session):
    user = db_session.query(User).filter(User.email == "admin@aicte.gov.in").first()
    return create_access_token(
        subject=user.id,
        extra_claims={"role": user.role, "region_id": None, "institution_id": None}
    )
