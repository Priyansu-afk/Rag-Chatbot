import logging
from database.db import engine, Base
# Import models to ensure they are registered with Base metadata before creation
from database.models import User, Document, Conversation, Message, Analytics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """
    Initializes database by creating all defined tables.
    """
    try:
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e

def reset_db():
    """
    Drops all tables and re-creates them. Dangerous, use only for testing.
    """
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped. Re-creating...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database reset complete.")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise e

if __name__ == "__main__":
    init_db()
