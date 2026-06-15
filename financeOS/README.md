# FinanceOS API

A personal finance management platform built with FastAPI and PostgreSQL.

## Features

- JWT authentication with access and refresh tokens
- Multi-account management with real-time balance tracking
- Transaction logging with category classification and date filtering
- Budget limits per category with overspend detection
- Recurring transaction scheduling (daily, weekly, monthly, yearly)
- Financial reports — net worth, spending trends, weekly and monthly summaries

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Migrations:** Alembic
- **Auth:** JWT via python-jose
- **Testing:** pytest with FastAPI TestClient

## Getting Started

### Prerequisites
- Docker and Docker Compose

### Run the API

```bash
git clone <your-repo-url>
cd financeOS
docker-compose up --build
```

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

### Run Tests

```bash
docker-compose exec api pytest tests/ -v
```

## Project Structure
app/
├── models/        # SQLAlchemy database models
├── schemas/       # Pydantic request/response schemas
├── routers/       # API endpoint definitions
├── services/      # Business logic layer
└── utils/         # Date helpers and financial calculations
tests/             # pytest test suite

## API Endpoints

| Group | Endpoints |
|---|---|
| Auth | POST /api/auth/register, /login, /refresh, /change-password |
| Accounts | GET/POST /api/accounts, transfer, recalculate |
| Transactions | GET/POST /api/transactions, date/category filtering, monthly summary |
| Categories | GET/POST /api/categories |
| Budgets | GET/POST /api/budgets, budget status tracking |
| Recurring | GET/POST /api/recurring, generate due transactions |
| Reports | /api/reports/net-worth, /trend, /weekly, /monthly-trends |