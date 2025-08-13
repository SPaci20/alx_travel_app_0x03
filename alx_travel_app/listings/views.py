from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from rest_framework import viewsets
from rest_framework.response import Response
from .models import  Booking ,Listing, User
from .serializers import BookingSerializer, ListingSerializer, UserSerializer


class UserViewset(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'bookings'
    lookup_field = 'listings'

class BookingViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'bookings'


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