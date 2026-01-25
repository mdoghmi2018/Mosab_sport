from fastapi import APIRouter
from app.api.v1 import auth, booking, payments, matchops, reports, awards, pt, formation, ads, admin

api_router = APIRouter()

# Phase 1 - Core
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(booking.router, prefix="/venues", tags=["Booking"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(matchops.router, prefix="/matches", tags=["Match Operations"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])

# Phase 2 - v1.2 enhancements
api_router.include_router(awards.router, prefix="/awards", tags=["Awards"])
api_router.include_router(pt.router, prefix="/pt", tags=["Personal Training"])
api_router.include_router(formation.router, prefix="/formations", tags=["Formations"])
api_router.include_router(ads.router, prefix="/ads", tags=["Advertising"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])

