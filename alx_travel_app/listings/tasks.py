from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Payment

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
