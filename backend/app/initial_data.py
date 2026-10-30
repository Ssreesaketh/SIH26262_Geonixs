import logging
from app.core.database import SessionLocal, Base, engine
from app.seed_data import seed_database
from app.services.sla_engine import SLAEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Seeding initial data...")
    db = SessionLocal()
    try:
        seed_database(db, reset=False)
        SLAEngine.evaluate_all(db)
        logger.info("Database initialized and seeded successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
