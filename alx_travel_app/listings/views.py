from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.utils import timezone
import uuid
import requests

from .models import Booking, Listing, User, Payment
from .serializers import BookingSerializer, ListingSerializer, UserSerializer
from .tasks import send_booking_confirmation_email
import logging

# -------------------------------
# User, Booking, Listing ViewSets
# -------------------------------

class UserViewset(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'bookings'
    lookup_field = 'listings'



class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        """
        Create a new booking and trigger email notification
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            booking = serializer.save(user=request.user)
            send_booking_confirmation_email.delay(
                booking_id=booking.id,
                user_email=request.user.email,
                user_name=request.user.get_full_name() or request.user.username,
                listing_title=booking.listing.title,
                check_in_date=booking.check_in_date.strftime('%Y-%m-%d'),
                check_out_date=booking.check_out_date.strftime('%Y-%m-%d')
            )
            self.logger.info(f"Booking created and email task queued for booking {booking.id}")
            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    'message': 'Booking created successfully. Confirmation email will be sent shortly.',
                    'booking': serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except Exception as e:
            self.logger.error(f"Error creating booking: {str(e)}")
            return Response(
                {'error': 'Failed to create booking'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_queryset(self):
        """
        Filter bookings for the current user
        """
        return self.queryset.filter(user=self.request.user)


class ListingViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing listing instances.
    """
    serializer_class = ListingSerializer
    queryset = Listing.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'property'

    @action(detail=False, methods=['post'])
    def create_listing(self, request):
        """
        Create a new listing for the authenticated user.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def retrieve_bookings(self, request, pk=None):
        """
        Retrieve all bookings for a specific listing.
        """
        listing = self.get_object()
        bookings = listing.bookings.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put', 'patch'])
    def update_booking(self, request, pk=None):
        """
        Update a booking for a specific listing.
        """
        listing = self.get_object()
        booking = listing.bookings.filter(id=request.data['id']).first()
        if booking:
            serializer = BookingSerializer(booking, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['delete'])
    def delete_booking(self, request, pk=None):
        """
        Delete a booking for a specific listing.
        """
        listing = self.get_object()
        booking = listing.bookings.filter(id=request.data['id']).first()
        if booking:
            booking.delete()
            return Response({'message': 'Booking deleted'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)


# -------------------------------
# Chapa Payment Integration Views
# -------------------------------

CHAPA_INIT_URL = f"{settings.CHAPA_PUBLIC_BASE}/v1/transaction/initialize"
CHAPA_VERIFY_URL = f"{settings.CHAPA_PUBLIC_BASE}/v1/transaction/verify"
DEFAULT_TIMEOUT = 20  # seconds

class InitiatePaymentAPIView(APIView):
    """
    Initialize a payment for a booking using Chapa.
    """
    def post(self, request):
        data = request.data
        for field in ["booking_reference", "amount", "email"]:
            if not data.get(field):
                return Response({"detail": f"{field} is required."}, status=400)

        booking_reference = str(data["booking_reference"])
        amount = str(data["amount"])
        currency = data.get("currency", "ETB")
        email = data["email"]
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        return_url = data.get("return_url") or settings.CHAPA_RETURN_URL
        callback_url = settings.CHAPA_CALLBACK_URL

        tx_ref = f"{booking_reference}-{uuid.uuid4().hex[:10]}"

        payload = {
            "amount": amount,
            "currency": currency,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": tx_ref,
            "return_url": return_url,
        }
        if callback_url:
            payload["callback_url"] = callback_url

        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        payment = Payment.objects.create(
            booking_reference=booking_reference,
            tx_ref=tx_ref,
            amount=amount,
            currency=currency,
            status=Payment.Status.PENDING,
            customer_email=email,
            customer_first_name=first_name,
            customer_last_name=last_name,
        )

        try:
            resp = requests.post(CHAPA_INIT_URL, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)
            data_resp = resp.json()
        except Exception as exc:
            payment.mark_failed({"error": str(exc), "when": "initialize_exception"})
            return Response({"detail": "Failed to contact payment gateway."}, status=502)

        if resp.status_code == 200 and data_resp.get("status") == "success":
            checkout_url = data_resp.get("data", {}).get("checkout_url")
            payment.checkout_url = checkout_url
            payment.gateway_payload = data_resp
            payment.save(update_fields=["checkout_url", "gateway_payload", "updated_at"])
            return Response({
                "message": "Payment initialized.",
                "tx_ref": tx_ref,
                "checkout_url": checkout_url
            }, status=201)

        payment.mark_failed(data_resp)
        return Response({"detail": "Payment initialization failed.", "gateway": data_resp}, status=400)


class VerifyPaymentAPIView(APIView):
    """
    Verify a payment using Chapa.
    """
    def get(self, request):
        tx_ref = request.query_params.get("tx_ref")
        if not tx_ref:
            return Response({"detail": "tx_ref is required."}, status=400)

        try:
            payment = Payment.objects.get(tx_ref=tx_ref)
        except Payment.DoesNotExist:
            return Response({"detail": "Payment not found."}, status=404)

        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.get(f"{CHAPA_VERIFY_URL}/{tx_ref}", headers=headers, timeout=DEFAULT_TIMEOUT)
            data_resp = resp.json()
        except Exception as exc:
            return Response({"detail": "Verification error.", "error": str(exc)}, status=502)

        if resp.status_code == 200 and data_resp.get("status") == "success" and data_resp.get("data", {}).get("status") == "success":
            payment.mark_success(data_resp)
            # Optional: Celery email task
            try:
                from .tasks import send_payment_confirmation_email
                send_payment_confirmation_email.delay(payment.id)
            except Exception:
                pass
            return Response({
                "message": "Payment verified successfully.",
                "status": payment.status,
                "booking_reference": payment.booking_reference,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "processor_tx_id": payment.processor_tx_id,
            })

        payment.mark_failed(data_resp)
        return Response({
            "message": "Payment not successful.",
            "status": payment.status,
            "gateway": data_resp
        }, status=400)


class ChapaWebhookAPIView(APIView):
    """
    Optional webhook for Chapa callback.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        tx_ref = request.data.get("tx_ref") or request.data.get("data", {}).get("tx_ref")
        if not tx_ref:
            return Response({"detail": "tx_ref missing."}, status=400)

        request._request.GET = request._request.GET.copy()
        request._request.GET["tx_ref"] = tx_ref
        return VerifyPaymentAPIView().get(request)
