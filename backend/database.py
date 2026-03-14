"""Database connection and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings
from models import Base

# Create engine based on database URL
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_migrations():
    """Run lightweight schema migrations for columns added after initial create_all."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)

    # Migration: add target_price to watch_subscriptions (Phase 1 price target alerts)
    if "watch_subscriptions" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("watch_subscriptions")]
        if "target_price" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE watch_subscriptions ADD COLUMN target_price FLOAT"))
            print("Migration: added target_price column to watch_subscriptions")


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    _run_migrations()
