from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
import time
from app.core.database import get_db
from app.core.config import settings
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.booking import Reservation, ReservationStatus
from app.models.payment import Payment, PaymentStatus, PaymentEvent
from app.models.venue import Slot, SlotStatus
from app.models.match import Match, MatchStatus

router = APIRouter()

class PaymentInitiateRequest(BaseModel):
    reservation_id: UUID

class PaymentInitiateResponse(BaseModel):
    payment_id: str
    payment_url: str
    status: str

class PaymentWebhookPayload(BaseModel):
    provider_event_id: str
    provider_ref: Optional[str] = None
    status: str
    amount_cents: int
    currency: str
    timestamp: str
    raw_payload: dict

@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    request: PaymentInitiateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate payment for a reservation"""
    reservation = db.query(Reservation).options(
        joinedload(Reservation.slot)
    ).filter(
        Reservation.id == request.reservation_id,
        Reservation.booked_by_user_id == current_user.id
    ).first()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    if reservation.status != ReservationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation is not in pending status"
        )
    
    # Check if payment already exists (idempotency)
    if idempotency_key:
        existing_payment = db.query(Payment).filter(
            Payment.reservation_id == request.reservation_id
        ).first()
        if existing_payment:
            return PaymentInitiateResponse(
                payment_id=str(existing_payment.id),
                payment_url=f"/payments/{existing_payment.id}/checkout",  # TODO: actual payment URL
                status=existing_payment.status.value
            )
    
    # Create payment
    payment = Payment(
        provider="stripe",  # TODO: make configurable
        amount_cents=reservation.slot.price_cents,
        currency=reservation.slot.currency,
        status=PaymentStatus.INITIATED,
        reservation_id=reservation.id
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # TODO: Integrate with actual payment provider
    payment_url = f"/payments/{payment.id}/checkout"
    
    return PaymentInitiateResponse(
        payment_id=str(payment.id),
        payment_url=payment_url,
        status=payment.status.value
    )

@router.post("/webhook")
async def payment_webhook(
    request: Request,
    provider: str = Header(..., alias="X-Payment-Provider"),
    db: Session = Depends(get_db)
):
    """Handle payment webhook with idempotency and signature verification"""
    import json
    # Read body once for signature verification and JSON parsing
    body = await request.body()
    payload = json.loads(body)
    provider_event_id = payload.get("id") or payload.get("event_id")
    
    if not provider_event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing provider_event_id"
        )
    
    # Check idempotency - if event already processed, return 200
    existing_event = db.query(PaymentEvent).filter(
        PaymentEvent.provider == provider,
        PaymentEvent.provider_event_id == provider_event_id
    ).first()
    
    if existing_event:
        return {"status": "already_processed", "event_id": str(existing_event.id)}
    
    # Use transaction for atomicity
    try:
        # Store webhook event
        payment_event = PaymentEvent(
            provider=provider,
            provider_event_id=provider_event_id,
            payload_json=payload
        )
        db.add(payment_event)
        
        # Verify webhook signature (if configured)
        if settings.STRIPE_WEBHOOK_SECRET and provider == "stripe":
            import hmac
            import hashlib
            sig_header = request.headers.get("Stripe-Signature")
            if sig_header:
                try:
                    # Stripe signature verification
                    elements = sig_header.split(',')
                    timestamp = None
                    signatures = []
                    for element in elements:
                        key, value = element.split('=')
                        if key == 't':
                            timestamp = int(value)
                        elif key == 'v1':
                            signatures.append(value)
                    
                    # Verify timestamp (prevent replay attacks)
                    current_time = int(time.time())
                    if abs(current_time - timestamp) > 300:  # 5 minutes
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Webhook timestamp too old"
                        )
                    
                    # Verify signature using the body we already read
                    signed_payload = f"{timestamp}.{body.decode()}"
                    expected_sig = hmac.new(
                        settings.STRIPE_WEBHOOK_SECRET.encode(),
                        signed_payload.encode(),
                        hashlib.sha256
                    ).hexdigest()
                    
                    if not any(hmac.compare_digest(expected_sig, sig) for sig in signatures):
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid webhook signature"
                        )
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Webhook verification failed: {str(e)}"
                    )
        
        # Update payment and reservation status
        payment_ref = payload.get("payment_id") or payload.get("data", {}).get("object", {}).get("id")
        if payment_ref:
            payment = db.query(Payment).options(
                joinedload(Payment.reservation).joinedload(Reservation.slot).joinedload(Slot.court)
            ).filter(
                Payment.provider_ref == payment_ref
            ).first()
            
            if payment:
                # Determine payment status from webhook
                webhook_status = payload.get("type") or payload.get("status", "").lower()
                
                if "succeeded" in webhook_status or "captured" in webhook_status:
                    payment.status = PaymentStatus.CAPTURED
                    payment.provider_ref = payment_ref
                    
                    # Update reservation
                    reservation = payment.reservation
                    reservation.status = ReservationStatus.PAID
                    reservation.payment_id = payment.id
                    
                    # Update slot
                    reservation.slot.status = SlotStatus.BOOKED
                    
                    # Create match automatically
                    match = Match(
                        reservation_id=reservation.id,
                        sport=reservation.slot.court.sport,
                        status=MatchStatus.SCHEDULED
                    )
                    db.add(match)
                
                elif "failed" in webhook_status:
                    payment.status = PaymentStatus.FAILED
                    reservation = payment.reservation
                    reservation.status = ReservationStatus.CANCELLED
                    reservation.slot.status = SlotStatus.OPEN
        
        db.commit()
        return {"status": "processed", "event_id": str(payment_event.id)}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )

