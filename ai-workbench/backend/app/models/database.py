from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[2]

DATABASE_URL = f"sqlite:///{BACKEND_DIR / 'ai_workbench.db'}"


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def ensure_workflow_step_columns():
    """Add columns introduced after the first release to an existing DB."""

    inspector = inspect(engine)

    if "workflow_steps" not in inspector.get_table_names():
        return

    existing = {
        column["name"]
        for column in inspector.get_columns("workflow_steps")
    }

    statements = {
        "top_k": "ALTER TABLE workflow_steps ADD COLUMN top_k INTEGER DEFAULT 5",
        "document_id": "ALTER TABLE workflow_steps ADD COLUMN document_id VARCHAR(100)",
    }

    with engine.begin() as connection:
        for name, statement in statements.items():
            if name not in existing:
                connection.execute(text(statement))


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()