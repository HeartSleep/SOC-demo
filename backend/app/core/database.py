from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import text
from typing import AsyncGenerator
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Database engine with connection pooling
engine = None
async_session_maker = None
database_connected = False


def get_database_url() -> str:
    """Get database URL from settings"""
    return settings.DATABASE_URL


async def init_database():
    """Initialize database connection with connection pooling"""
    global engine, async_session_maker, database_connected

    try:
        # Create async engine with connection pooling
        engine = create_async_engine(
            get_database_url(),
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,  # Enable connection health checks
            poolclass=QueuePool,
        )

        # Create session factory
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        # Test connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        logger.info(f"Connected to PostgreSQL: {settings.POSTGRES_DB}")
        logger.info(f"Connection pool configured: size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW}")
        database_connected = True

    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        logger.warning("Continuing without database connection")
        database_connected = False


async def close_database():
    """Close database connections and dispose engine"""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connections closed and pool disposed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    Use this in FastAPI endpoint dependencies.

    Example:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_database():
    """Legacy compatibility function"""
    return async_session_maker


def is_database_connected():
    """Check if database is connected"""
    return database_connected


# Create all tables (will be replaced by Alembic migrations)
async def create_tables():
    """Create all tables - for development only, use Alembic in production"""
    if not engine:
        logger.error("Database engine not initialized")
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")