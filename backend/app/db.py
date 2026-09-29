from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DATABASE_URL

engine_kwargs = {'pool_pre_ping': True}
if DATABASE_URL.startswith('sqlite'):
    engine_kwargs['connect_args'] = {'check_same_thread': False}
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Analysis(Base):
    __tablename__ = 'analyses'
    id = Column(String(64), primary_key=True)
    video_name = Column(String(255), nullable=False)
    status = Column(String(30), default='queued', nullable=False)
    frames = Column(Integer, default=0)
    duration_s = Column(Float, default=0)
    total_vehicles = Column(Integer, default=0)
    density = Column(Float, default=0)
    congestion = Column(String(30), default='UNKNOWN')
    flow_vph = Column(Float, default=0)
    annotated_video = Column(Text)
    heatmap = Column(Text)
    error = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

def init_db():
    Base.metadata.create_all(bind=engine)
    
def cleanup_stale_analyses():
    """Mark analyses left in processing state by a previous server run as failed."""
    db = SessionLocal()

    try:
        stale = (
            db.query(Analysis)
            .filter(Analysis.status == "processing")
            .all()
        )

        for analysis in stale:
            analysis.status = "failed"
            analysis.error = "Server stopped before analysis completed."

        db.commit()

        return len(stale)

    finally:
        db.close()