"""
Twilio Alert Dispatcher for D-SQUARE 2.0
Sends emergency SMS and WhatsApp notifications to first responders and authorities.
Includes fallback logging mechanism when Twilio credentials are not set.
"""

import os
import time
from typing import Dict, Any

# Environment variables or configuration defaults
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "DEMO_TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "DEMO_TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "+18005550199")
EMERGENCY_CONTACTS = [
    "+919876543210", # NDRF Disaster Response Control Room
    "+919811002233", # State Emergency Response Center
]

class TwilioAlertDispatcher:
    """
    Handles emergency SMS and WhatsApp notifications for CRITICAL and HIGH risk alerts.
    """

    def __init__(self):
        self.client = None
        if TWILIO_ACCOUNT_SID != "DEMO_TWILIO_ACCOUNT_SID":
            try:
                from twilio.rest import Client
                self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            except Exception as e:
                print(f"[TwilioAlert] Warning: Failed to initialize Twilio client: {e}")

    def send_emergency_alert(self, disaster_type: str, risk_level: str, confidence: float, location: str, lat: float, lon: float) -> Dict[str, Any]:
        """
        Sends emergency SMS/WhatsApp dispatch message.
        """
        message_body = (
            f"[EMERGENCY ALERT] D-SQUARE 2.0 EMERGENCY ALERT\n"
            f"Risk Level: {risk_level.upper()} ({confidence}% Confidence)\n"
            f"Disaster Type: {disaster_type.upper()}\n"
            f"Location: {location} (Lat: {lat:.4f}, Lon: {lon:.4f})\n"
            f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Action Required: Dispatch Emergency Response Team immediately.\n"
            f"Dashboard: http://d-square.bhuvan.isro.gov.in"
        )

        results = []
        if self.client:
            for recipient in EMERGENCY_CONTACTS:
                try:
                    msg = self.client.messages.create(
                        body=message_body,
                        from_=TWILIO_PHONE_NUMBER,
                        to=recipient
                    )
                    results.append({"to": recipient, "sid": msg.sid, "status": "SENT"})
                except Exception as ex:
                    results.append({"to": recipient, "status": "FAILED", "error": str(ex)})
        else:
            # Simulated Twilio Dispatch Log
            print("\n==================================================")
            print("  [TWILIO SMS SIMULATED EMERGENCY ALERT DISPATCH]")
            print("==================================================")
            print(message_body)
            print("--------------------------------------------------")
            for recipient in EMERGENCY_CONTACTS:
                results.append({
                    "to": recipient,
                    "sid": f"SIM_MSG_{int(time.time())}",
                    "status": "SENT_SIMULATED"
                })

        return {
            "dispatched": True,
            "disaster_type": disaster_type,
            "risk_level": risk_level,
            "recipients_notified": len(results),
            "dispatch_logs": results
        }
