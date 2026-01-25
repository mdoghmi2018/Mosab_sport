from celery import shared_task
from sqlalchemy.orm import Session, joinedload
from app.core.database import SessionLocal
from app.models.match import Match, MatchEvent, MatchReport, ReportStatus
from app.models.booking import Reservation
from app.models.venue import Venue, Court, Slot
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import hashlib
import json
import os
from datetime import datetime
from uuid import UUID
from app.core.config import settings

@shared_task
def generate_match_report_task(match_id: str, version: int = None):
    """Generate match report PDF"""
    db = SessionLocal()
    report = None
    try:
        # Convert string to UUID
        try:
            match_uuid = UUID(match_id)
        except ValueError:
            return {"error": "Invalid match_id format"}
        
        match = db.query(Match).options(
            joinedload(Match.reservation).joinedload(Reservation.slot).joinedload(Slot.court).joinedload(Court.venue)
        ).filter(Match.id == match_uuid).first()
        
        if not match:
            return {"error": "Match not found"}
        
        # Get latest version if not specified
        if version is None:
            latest = db.query(MatchReport).filter(
                MatchReport.match_id == match_uuid
            ).order_by(MatchReport.version.desc()).first()
            version = (latest.version + 1) if latest else 1
        
        report = db.query(MatchReport).filter(
            MatchReport.match_id == match_uuid,
            MatchReport.version == version
        ).first()
        
        if not report:
            report = MatchReport(
                match_id=match_uuid,
                version=version,
                status=ReportStatus.GENERATING
            )
            db.add(report)
            db.commit()
        
        # Load match data
        events = db.query(MatchEvent).filter(
            MatchEvent.match_id == match_uuid
        ).order_by(MatchEvent.seq).all()
        
        reservation = match.reservation
        slot = reservation.slot
        court = slot.court
        venue = court.venue
        
        # Build report JSON (canonical)
        report_data = {
            "match_id": str(match_uuid),
            "version": version,
            "sport": match.sport,
            "venue": {
                "name": venue.name,
                "location": venue.location_json
            },
            "court": {
                "name": court.name,
                "sport": court.sport
            },
            "slot": {
                "start": slot.start_ts.isoformat(),
                "end": slot.end_ts.isoformat()
            },
            "events": [
                {
                    "seq": event.seq,
                    "ts": event.ts.isoformat(),
                    "type": event.type,
                    "payload": event.payload_json
                }
                for event in events
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Compute checksum
        report_json_str = json.dumps(report_data, sort_keys=True)
        checksum = hashlib.sha256(report_json_str.encode()).hexdigest()
        
        # Generate PDF
        os.makedirs(settings.REPORT_STORAGE_PATH, exist_ok=True)
        pdf_filename = f"match_{match_uuid}_v{version}.pdf"
        pdf_path = os.path.join(settings.REPORT_STORAGE_PATH, pdf_filename)
        
        generate_pdf(report_data, pdf_path)
        
        # Update report
        report.status = ReportStatus.READY
        report.pdf_url = pdf_path
        report.checksum = checksum
        report.report_json = report_data
        report.generated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "report_id": str(report.id),
            "version": version,
            "checksum": checksum,
            "pdf_url": pdf_path
        }
    
    except Exception as e:
        if report:
            report.status = ReportStatus.FAILED
            db.commit()
        return {"error": str(e)}
    finally:
        db.close()

def generate_pdf(report_data: dict, output_path: str):
    """Generate PDF from report data"""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, f"Match Report - {report_data['sport'].upper()}")
    
    # Venue info
    y = height - 100
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Venue: {report_data['venue']['name']}")
    y -= 20
    c.drawString(50, y, f"Court: {report_data['court']['name']}")
    y -= 20
    c.drawString(50, y, f"Date: {report_data['slot']['start']}")
    
    # Events
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Match Events")
    y -= 20
    
    c.setFont("Helvetica", 10)
    for event in report_data['events']:
        if y < 100:
            c.showPage()
            y = height - 50
        
        event_text = f"{event['seq']}. [{event['ts']}] {event['type']}"
        c.drawString(50, y, event_text)
        y -= 15
    
    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(50, 30, f"Generated: {report_data['generated_at']}")
    c.drawString(50, 15, f"Version: {report_data['version']}")
    
    c.save()

