from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, accounts, transactions, categories, budgets, recurring, reports
from app.services.category_service import seed_default_categories
from app.database import SessionLocal

app = FastAPI(
    title="FinanceOS API",
    description="A comprehensive personal finance management platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(budgets.router)
app.include_router(recurring.router)
app.include_router(reports.router)


@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        seed_default_categories(db)
        db.close()
    except Exception as e:
        print(f"Warning: Startup error: {e}")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "FinanceOS API"}