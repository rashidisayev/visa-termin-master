"""
Notification module for visa appointment helper.
Handles sending notifications via Telegram and other channels.
"""
import subprocess
import json
from typing import Optional
from urllib.parse import quote
from . import config, utils


def send_telegram_notification(message: str) -> bool:
    """
    Send notification via Telegram.
    
    Args:
        message: Message to send
        
    Returns:
        True if successful, False otherwise
    """
    logger = utils.setup_logger()
    
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured")
        return False
    
    try:
        api_url = f"{config.TELEGRAM_API_URL}{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        
        # Use curl to send message
        cmd = [
            "curl",
            "-s",
            "-X", "POST",
            api_url,
            "-d", f"chat_id={config.TELEGRAM_CHAT_ID}",
            "-d", f"text={quote(message)}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Telegram notification sent: {message}")
            return True
        else:
            logger.error(f"Failed to send Telegram notification: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {e}")
        return False


def notify_available_date(date: str) -> bool:
    """
    Notify that an appointment date is available.
    
    Args:
        date: Available date string
        
    Returns:
        True if notification sent successfully
    """
    logger = utils.setup_logger()
    
    message = f"✅ Visa appointment available on {date}"
    logger.info(f"Notifying: {message}")
    
    return send_telegram_notification(message)


def notify_appointment_booked(date: str, time: str) -> bool:
    """
    Notify that appointment has been automatically booked.
    
    Args:
        date: Appointment date
        time: Appointment time
        
    Returns:
        True if notification sent successfully
    """
    logger = utils.setup_logger()
    
    message = f"📅 Appointment automatically booked for {date} at {time}"
    logger.info(f"Notifying: {message}")
    
    return send_telegram_notification(message)


def notify_error(error_message: str) -> bool:
    """
    Notify about errors that occurred.
    
    Args:
        error_message: Error description
        
    Returns:
        True if notification sent successfully
    """
    logger = utils.setup_logger()
    
    message = f"⚠️ Error in visa appointment process: {error_message}"
    logger.error(f"Notifying: {message}")
    
    return send_telegram_notification(message)
