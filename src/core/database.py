from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from src.core.config import settings

# Create engine defensively: if a DATABASE_URL is provided use it, otherwise
# fall back to an ephemeral SQLite in-memory database so tests and CI can run
# without requiring external Postgres credentials.
engine = None
SessionLocal = None
try:
	if settings.DATABASE_URL:
		engine = create_engine(settings.DATABASE_URL, echo=True)
		SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	else:
		logging.info("DATABASE_URL not set; using in-memory SQLite for tests")
		engine = create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
		SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
	logging.warning("Failed to create SQLAlchemy engine with DATABASE_URL=%s: %s", settings.DATABASE_URL, e)
	# As a last resort try in-memory SQLite
	engine = create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
	SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
