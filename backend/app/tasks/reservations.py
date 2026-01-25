from celery import shared_task
from sqlalchemy.orm import Session, joinedload
from app.core.database import SessionLocal
from app.models.booking import Reservation, ReservationStatus
from app.models.venue import Slot, SlotStatus
from datetime import datetime

@shared_task
def expire_pending_reservations():
    """Expire pending reservations that have passed their TTL"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Find expired pending reservations with slot relationship loaded
        expired = db.query(Reservation).options(
            joinedload(Reservation.slot)
        ).filter(
            Reservation.status == ReservationStatus.PENDING,
            Reservation.expires_at < now
        ).all()
        
        for reservation in expired:
            reservation.status = ReservationStatus.CANCELLED
            if reservation.slot:
                reservation.slot.status = SlotStatus.OPEN
        
        db.commit()
        
        if expired:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Expired {len(expired)} pending reservations")
        
        return {"expired_count": len(expired)}
    
    except Exception as e:
        db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error expiring reservations: {e}")
        return {"error": str(e), "expired_count": 0}
    finally:
        db.close()

