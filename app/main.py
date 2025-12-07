# app/main.py
from contextlib import asynccontextmanager
import logging

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.core.config import get_settings
from app.database import create_db_and_tables

# Import models so SQLModel metadata is populated before create_all()
from app.models import user as _user_models  # noqa: F401
from app.models import product as _product_models  # noqa: F401
from app.models import cart as _cart_models  # noqa: F401
from app.models import order as _order_models  # noqa: F401


# Routers
from app.routers.users import router as users_router
from app.routers.products import router as products_router
from app.routers.cart import router as cart_router
from app.routers.orders import router as orders_router

settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup:
      - Verify DB connectivity and create tables.

    Shutdown:
      - No special cleanup needed for sync engine.
    """
    logger.info("🔄 Startup: Connecting to Supabase Postgres...")
    try:
        create_db_and_tables()
        logger.info("✅ Startup: DB connection OK, tables verified.")
    except Exception as e:
        logger.error(f"❌ Startup: DB connection FAILED: {e}")
        raise
    yield


app = FastAPI(
    title=settings.PROJECT_NAME or "Amoura Cake Shop API",
    version="0.1.0",
    lifespan=lifespan,
)


# --- CORS configuration ---
# Updated CORS origins in `app/main.py`
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
    "http://[::1]:3000",
    "http://localhost:3001",  # optional alternate port if needed
    "amourapastry.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Versioned API prefix, e.g. /api/v1
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(products_router, prefix=settings.API_V1_STR)
app.include_router(cart_router, prefix=settings.API_V1_STR)
app.include_router(orders_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "amoura-backend"}