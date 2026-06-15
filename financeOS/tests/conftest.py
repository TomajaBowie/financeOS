import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.models import User, Account, Transaction, Category, Budget, RecurringTransaction
from app.services.category_service import seed_default_categories

TEST_DATABASE_URL = "postgresql://postgres:password@db_test:5432/financeos_test"

test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    seed_default_categories(session)
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        yield db

    from app.main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(client):
    response = client.post("/api/auth/register", json={
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "password123"
    })
    return response.json()


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    response = client.post("/api/auth/login", json={
        "email": "testuser@example.com",
        "password": "password123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_account(client, auth_headers):
    response = client.post("/api/accounts", json={
        "name": "Test Account",
        "account_type": "checking",
        "initial_balance": "1000.00",
        "currency": "USD"
    }, headers=auth_headers)
    return response.json()