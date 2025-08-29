
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
from .models import Payment

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_booking_confirmation_email(self, booking_id, user_email, user_name, listing_title, check_in_date, check_out_date):
    """
    Send booking confirmation email asynchronously
    """
    try:
        subject = f'Booking Confirmation - {listing_title}'
        # HTML email content
        html_message = f"""
        <html>
        <body>
            <h2>Booking Confirmation</h2>
            <p>Dear {user_name},</p>
            <p>Your booking has been confirmed!</p>
            <div style="border: 1px solid #ddd; padding: 15px; margin: 15px 0;">
                <h3>Booking Details:</h3>
                <p><strong>Property:</strong> {listing_title}</p>
                <p><strong>Check-in Date:</strong> {check_in_date}</p>
                <p><strong>Check-out Date:</strong> {check_out_date}</p>
                <p><strong>Booking ID:</strong> #{booking_id}</p>
            </div>
            <p>Thank you for choosing our service!</p>
            <p>Best regards,<br>ALX Travel App Team</p>
        </body>
        </html>
        """
        # Plain text version
        plain_message = strip_tags(html_message)
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Booking confirmation email sent successfully to {user_email} for booking {booking_id}")
        return f"Email sent successfully to {user_email}"
    except Exception as exc:
        logger.error(f"Error sending email to {user_email} for booking {booking_id}: {str(exc)}")
        # Retry the task with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task
def send_booking_reminder_email(booking_id, user_email, user_name, listing_title, check_in_date):
    """
    Send booking reminder email (can be scheduled)
    """
    try:
        subject = f'Booking Reminder - {listing_title}'
        message = f"""
        Dear {user_name},
        
        This is a friendly reminder about your upcoming booking:
        
        Property: {listing_title}
        Check-in Date: {check_in_date}
        Booking ID: #{booking_id}
        
        We look forward to your stay!
        
        Best regards,
        ALX Travel App Team
        """
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.info(f"Booking reminder email sent to {user_email} for booking {booking_id}")
        return f"Reminder email sent to {user_email}"
    except Exception as exc:
        logger.error(f"Error sending reminder email: {str(exc)}")
        raise exc

@shared_task
def send_payment_confirmation_email(payment_id: int):
    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return
    subject = f"Payment Confirmed for Booking {payment.booking_reference}"
    message = (
        f"Hi {payment.customer_first_name or ''},\n\n"
        f"Your payment of {payment.amount} {payment.currency} for booking "
        f"{payment.booking_reference} was successful.\n\n"
        f"Transaction Reference: {payment.tx_ref}\n"
        f"Processor ID: {payment.processor_tx_id or 'N/A'}\n\n"
        "Thank you for booking with us!"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [payment.customer_email], fail_silently=True)
