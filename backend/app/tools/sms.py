import logging
from ..config import config_manager

logger = logging.getLogger(__name__)

def send_booking_sms(to_number: str, booking_details: dict) -> bool:
    """
    Sends an SMS confirmation to the passenger when a ticket is booked.
    """
    message_body = (
        f"IRCTC Booking Confirmed!\n"
        f"PNR: {booking_details['pnr']}\n"
        f"Train: {booking_details['train_no']} ({booking_details['train_name']})\n"
        f"Date: {booking_details['date']}\n"
        f"Coach/Seat: {booking_details['coach']}/{booking_details['berth']}\n"
        f"Total Price: Rs.{booking_details['price']}\n"
        f"Happy Journey!"
    )
    return send_sms(to_number, message_body)

def send_cancellation_sms(to_number: str, pnr: str, refund_amount: float) -> bool:
    """
    Sends an SMS confirmation when a ticket is cancelled.
    """
    message_body = (
        f"IRCTC Ticket Cancelled!\n"
        f"PNR: {pnr}\n"
        f"Refund Amount: Rs.{refund_amount:.2f} will be credited to source account.\n"
        f"Cancellation Charges: Applied."
    )
    return send_sms(to_number, message_body)

def send_sms(to_number: str, message: str) -> bool:
    """
    Generic SMS sender that supports Twilio and fallback log-mode.
    """
    settings = config_manager.settings
    
    # Clean phone number (default if mock)
    if not to_number or to_number == "WebRTC-User":
        to_number = "+1234567890"

    print(f"--- SMS OUTBOX [To: {to_number}] ---\n{message}\n----------------------------------")
    
    if settings.sms_provider == "twilio" and settings.twilio_account_sid and settings.twilio_auth_token:
        try:
            from twilio.rest import Client
            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            
            # Send message
            client.messages.create(
                body=message,
                from_=settings.twilio_phone_number,
                to=to_number
            )
            logger.info(f"SMS sent successfully via Twilio to {to_number}")
            return True
        except Exception as e:
            logger.error(f"Error sending SMS via Twilio: {e}")
            return False
            
    # Mock SMS success
    logger.info(f"SMS logged in mock mode to {to_number}")
    return True
