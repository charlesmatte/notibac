import logging

from django.conf import settings
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

logger = logging.getLogger(__name__)


def send_verification_sms(phone_number, code):
    """Send SMS verification code via Twilio.

    Returns True on success, False on failure.
    """
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
        logger.error("Twilio credentials not configured")
        return False

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Votre code de vérification Notibac: {code}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number,
        )
        logger.info(f"SMS sent successfully: {message.sid}")
        return True
    except TwilioRestException as e:
        logger.error(f"Twilio error: {e}")
        return False
