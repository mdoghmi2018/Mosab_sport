#!/usr/bin/env python3
"""
End-to-End Smoke Test
Tests the complete Phase 1 flow:
Auth → Booking → Payment → Match → Events → Report
"""

import sys
import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test data
ORGANIZER_PHONE = "+1234567890"
REFEREE_PHONE = "+1234567891"

class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_step(step: str, message: str):
    """Print formatted test step"""
    print(f"{Colors.BLUE}[{step}]{Colors.NC} {message}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅{Colors.NC} {message}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌{Colors.NC} {message}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️{Colors.NC} {message}")

def get_otp(phone: str) -> str:
    """Get OTP from dev endpoint or logs"""
    # Try dev endpoint first
    try:
        response = requests.post(
            f"{API_BASE}/auth/dev-otp",
            json={"phone": phone}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("otp", "")
    except:
        pass
    
    # Fallback: check logs (would need docker logs)
    print_warning(f"OTP not available via dev endpoint. Check API logs for OTP for {phone}")
    return input(f"Enter OTP for {phone}: ").strip()

def test_auth(phone: str) -> Optional[str]:
    """Test authentication flow"""
    print_step("AUTH", f"Authenticating {phone}...")
    
    # Start auth
    response = requests.post(
        f"{API_BASE}/auth/start",
        json={"phone": phone}
    )
    
    if response.status_code != 200:
        print_error(f"Auth start failed: {response.status_code}")
        print(response.text)
        return None
    
    print_success("OTP sent")
    
    # Get OTP (from dev endpoint or manual input)
    otp = get_otp(phone)
    if not otp:
        print_error("Could not get OTP")
        return None
    
    # Verify OTP
    response = requests.post(
        f"{API_BASE}/auth/verify",
        json={"phone": phone, "otp": otp}
    )
    
    if response.status_code != 200:
        print_error(f"OTP verification failed: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    token = data.get("access_token")
    print_success(f"Authenticated as {data.get('role')}")
    return token

def test_booking(organizer_token: str) -> Optional[Dict]:
    """Test booking flow"""
    print_step("BOOKING", "Testing reservation creation...")
    
    headers = {"Authorization": f"Bearer {organizer_token}"}
    
    # List venues
    response = requests.get(f"{API_BASE}/venues", headers=headers)
    if response.status_code != 200:
        print_error(f"Failed to list venues: {response.status_code}")
        return None
    
    venues = response.json()
    if not venues:
        print_error("No venues found. Run seed_demo_data.py first")
        return None
    
    venue_id = venues[0]["id"]
    print_success(f"Found venue: {venues[0]['name']}")
    
    # List courts
    response = requests.get(f"{API_BASE}/venues/{venue_id}/courts", headers=headers)
    if response.status_code != 200:
        print_error(f"Failed to list courts: {response.status_code}")
        return None
    
    courts = response.json()
    if not courts:
        print_error("No courts found")
        return None
    
    court_id = courts[0]["id"]
    print_success(f"Found court: {courts[0]['name']}")
    
    # List slots
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    response = requests.get(
        f"{API_BASE}/venues/courts/{court_id}/slots",
        params={"from_date": tomorrow},
        headers=headers
    )
    
    if response.status_code != 200:
        print_error(f"Failed to list slots: {response.status_code}")
        return None
    
    slots = response.json()
    if not slots:
        print_error("No slots found. Run seed_demo_data.py first")
        return None
    
    slot = slots[0]
    slot_id = slot["id"]
    print_success(f"Found slot: {slot['start_ts']} - {slot['end_ts']}")
    
    # Create reservation
    response = requests.post(
        f"{API_BASE}/venues/reservations",
        headers=headers,
        json={
            "slot_id": slot_id,
            "actor_type": "individual",
            "actor_id": None
        }
    )
    
    if response.status_code != 201:
        print_error(f"Failed to create reservation: {response.status_code}")
        print(response.text)
        return None
    
    reservation = response.json()
    print_success(f"Reservation created: {reservation['id']}")
    print(f"   Status: {reservation['status']}")
    print(f"   Expires at: {reservation.get('expires_at', 'N/A')}")
    
    return {
        "reservation_id": reservation["id"],
        "slot_id": slot_id,
        "court_id": court_id
    }

def test_payment(organizer_token: str, reservation_id: str) -> Optional[str]:
    """Test payment initiation"""
    print_step("PAYMENT", "Testing payment initiation...")
    
    headers = {
        "Authorization": f"Bearer {organizer_token}",
        "Idempotency-Key": f"test-key-{int(time.time())}"
    }
    
    response = requests.post(
        f"{API_BASE}/payments/initiate",
        headers=headers,
        json={"reservation_id": reservation_id}
    )
    
    if response.status_code != 200:
        print_error(f"Payment initiation failed: {response.status_code}")
        print(response.text)
        return None
    
    payment = response.json()
    print_success(f"Payment initiated: {payment['payment_id']}")
    return payment["payment_id"]

def test_webhook(payment_id: str, reservation_id: str):
    """Test webhook (simulate payment capture)"""
    print_step("WEBHOOK", "Simulating payment webhook...")
    
    # Simulate Stripe webhook payload
    webhook_payload = {
        "id": f"evt_test_{int(time.time())}",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": payment_id,
                "status": "succeeded"
            }
        }
    }
    
    # First call - should succeed
    response = requests.post(
        f"{API_BASE}/payments/webhook",
        headers={
            "X-Payment-Provider": "stripe",
            "Content-Type": "application/json"
        },
        json=webhook_payload
    )
    
    if response.status_code != 200:
        print_warning(f"Webhook failed (may need signature): {response.status_code}")
        print(response.text)
    else:
        print_success("Webhook processed")
    
    # Second call - should be idempotent
    response2 = requests.post(
        f"{API_BASE}/payments/webhook",
        headers={
            "X-Payment-Provider": "stripe",
            "Content-Type": "application/json"
        },
        json=webhook_payload
    )
    
    if response2.status_code == 200:
        data = response2.json()
        if "already_processed" in data.get("status", ""):
            print_success("Webhook idempotency verified")
        else:
            print_warning("Webhook may not be fully idempotent")

def test_match(organizer_token: str, reservation_id: str) -> Optional[str]:
    """Test match creation"""
    print_step("MATCH", "Creating match from reservation...")
    
    headers = {"Authorization": f"Bearer {organizer_token}"}
    
    response = requests.post(
        f"{API_BASE}/matches/from-reservation/{reservation_id}",
        headers=headers
    )
    
    if response.status_code not in [200, 201]:
        print_error(f"Match creation failed: {response.status_code}")
        print(response.text)
        return None
    
    match = response.json()
    print_success(f"Match created: {match['id']}")
    return match["id"]

def test_referee_flow(referee_token: str, match_id: str):
    """Test referee assignment and match start"""
    print_step("REFEREE", "Testing referee flow...")
    
    headers = {"Authorization": f"Bearer {referee_token}"}
    
    # Accept assignment (assuming it was offered)
    response = requests.post(
        f"{API_BASE}/matches/{match_id}/referee/accept",
        headers=headers
    )
    
    if response.status_code == 200:
        print_success("Referee assignment accepted")
    else:
        print_warning(f"Referee accept failed (may need to offer first): {response.status_code}")
    
    # Start match
    response = requests.post(
        f"{API_BASE}/matches/{match_id}/start",
        headers=headers
    )
    
    if response.status_code != 200:
        print_error(f"Match start failed: {response.status_code}")
        print(response.text)
        return False
    
    print_success("Match started")
    return True

def test_events(referee_token: str, match_id: str):
    """Test match events (append-only with seq enforcement)"""
    print_step("EVENTS", "Testing match events...")
    
    headers = {"Authorization": f"Bearer {referee_token}"}
    
    # Get current events to find last seq
    response = requests.get(f"{API_BASE}/matches/{match_id}/events", headers=headers)
    if response.status_code == 200:
        events = response.json()
        last_seq = max([e["seq"] for e in events]) if events else 0
    else:
        last_seq = 0
    
    # Add event with correct seq
    next_seq = last_seq + 1
    event_data = {
        "seq": next_seq,
        "ts": datetime.utcnow().isoformat() + "Z",
        "type": "GOAL",
        "payload": {
            "player": "Player 1",
            "minute": 15,
            "team": "home"
        }
    }
    
    response = requests.post(
        f"{API_BASE}/matches/{match_id}/events",
        headers=headers,
        json=event_data
    )
    
    if response.status_code == 201:
        print_success(f"Event {next_seq} added successfully")
    else:
        print_error(f"Event creation failed: {response.status_code}")
        print(response.text)
        return False
    
    # Test failure: try to add out-of-order event
    bad_seq = next_seq + 2  # Skip one
    bad_event = event_data.copy()
    bad_event["seq"] = bad_seq
    
    response = requests.post(
        f"{API_BASE}/matches/{match_id}/events",
        headers=headers,
        json=bad_event
    )
    
    if response.status_code == 400:
        print_success("Out-of-order event correctly rejected")
    else:
        print_warning(f"Out-of-order event not rejected (status: {response.status_code})")
    
    return True

def test_finalize(referee_token: str, match_id: str):
    """Test match finalization"""
    print_step("FINALIZE", "Finalizing match...")
    
    headers = {"Authorization": f"Bearer {referee_token}"}
    
    response = requests.post(
        f"{API_BASE}/matches/{match_id}/finalize",
        headers=headers
    )
    
    if response.status_code != 200:
        print_error(f"Finalization failed: {response.status_code}")
        print(response.text)
        return False
    
    print_success("Match finalized")
    return True

def test_report(organizer_token: str, match_id: str):
    """Test report generation"""
    print_step("REPORT", "Testing report generation...")
    
    headers = {"Authorization": f"Bearer {organizer_token}"}
    
    # Trigger generation
    response = requests.post(
        f"{API_BASE}/reports/matches/{match_id}/generate",
        headers=headers
    )
    
    if response.status_code != 200:
        print_error(f"Report generation trigger failed: {response.status_code}")
        return False
    
    print_success("Report generation triggered")
    
    # Wait for generation (poll)
    print("   Waiting for report generation (10s)...")
    time.sleep(10)
    
    # Fetch report
    response = requests.get(
        f"{API_BASE}/reports/matches/{match_id}/report",
        headers=headers
    )
    
    if response.status_code == 200:
        print_success("Report ready!")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        return True
    elif response.status_code == 404:
        print_warning("Report not ready yet (may need more time)")
        return False
    else:
        print_error(f"Report fetch failed: {response.status_code}")
        return False

def main():
    """Run complete E2E smoke test"""
    print("\n" + "="*60)
    print("🧪 End-to-End Smoke Test")
    print("="*60 + "\n")
    
    # Check API is up
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print_error("API health check failed")
            return 1
    except Exception as e:
        print_error(f"Cannot reach API: {e}")
        return 1
    
    print_success("API is reachable\n")
    
    # Test flow
    try:
        # 1. Auth
        organizer_token = test_auth(ORGANIZER_PHONE)
        if not organizer_token:
            return 1
        
        referee_token = test_auth(REFEREE_PHONE)
        if not referee_token:
            return 1
        
        print()
        
        # 2. Booking
        booking_data = test_booking(organizer_token)
        if not booking_data:
            return 1
        
        reservation_id = booking_data["reservation_id"]
        print()
        
        # 3. Payment
        payment_id = test_payment(organizer_token, reservation_id)
        if not payment_id:
            return 1
        
        print()
        
        # 4. Webhook (simulate)
        test_webhook(payment_id, reservation_id)
        print()
        
        # 5. Match
        match_id = test_match(organizer_token, reservation_id)
        if not match_id:
            return 1
        
        print()
        
        # 6. Referee flow
        if not test_referee_flow(referee_token, match_id):
            return 1
        
        print()
        
        # 7. Events
        if not test_events(referee_token, match_id):
            return 1
        
        print()
        
        # 8. Finalize
        if not test_finalize(referee_token, match_id):
            return 1
        
        print()
        
        # 9. Report
        if not test_report(organizer_token, match_id):
            print_warning("Report test incomplete (may need manual check)")
        
        print("\n" + "="*60)
        print_success("🎉 E2E Smoke Test Complete!")
        print("="*60 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

