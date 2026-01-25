from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.core.database import get_db
from app.models.match import Match, MatchReport, ReportStatus, MatchStatus
from app.models.match import MatchEvent
from sqlalchemy import func

router = APIRouter()

class ReportResponse(BaseModel):
    id: str
    match_id: str
    version: int
    status: str
    pdf_url: Optional[str] = None
    checksum: Optional[str] = None
    generated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

@router.post("/matches/{match_id}/generate")
async def generate_report(
    match_id: UUID,
    db: Session = Depends(get_db)
):
    """Trigger report generation for a match"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    if match.status != MatchStatus.FINAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Match must be finalized before generating report"
        )
    
    # Get latest report version
    latest_version = db.query(func.max(MatchReport.version)).filter(
        MatchReport.match_id == match_id
    ).scalar() or 0
    
    # Create new report version
    report = MatchReport(
        match_id=match_id,
        version=latest_version + 1,
        status=ReportStatus.GENERATING
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Enqueue generation task
    from app.tasks.reports import generate_match_report_task
    generate_match_report_task.delay(str(match_id), report.version)
    
    return {"report_id": str(report.id), "version": report.version, "status": "generating"}

@router.get("/matches/{match_id}/report")
async def get_match_report(
    match_id: UUID,
    db: Session = Depends(get_db)
):
    """Get the latest report for a match"""
    report = db.query(MatchReport).filter(
        MatchReport.match_id == match_id,
        MatchReport.status == ReportStatus.READY
    ).order_by(MatchReport.version.desc()).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or not ready"
        )
    
    if report.pdf_url:
        return FileResponse(
            report.pdf_url,
            media_type="application/pdf",
            filename=f"match_report_{match_id}_v{report.version}.pdf"
        )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Report PDF not available"
    )

