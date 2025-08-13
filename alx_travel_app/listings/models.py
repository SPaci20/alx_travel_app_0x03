from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser,Group, Permission

from django.db.models.constraints import UniqueConstraint

class User(AbstractUser):
    '''Custom user model for the travel app, extending Django's AbstractUser.'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    booking = models.ManyToManyField('Booking', related_name='booking', blank=True)
    listings = models.ManyToManyField('Listing', related_name='listing', blank=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(
        max_length=15,
        blank=False,
        null=True
        )
    groups = models.ManyToManyField(
         Group,
         blank=True,
         verbose_name='groups',
         help_text='A user will get all permissions granted to each of their groups.',
         related_name="listing_user_groups",  # <--- Add this
         related_query_name="chats_user",
     )
    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
        related_name="listing_user_permissions",  # <--- Add this
        related_query_name="chats_user",
    )


class Listing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['created_at', 'updated_at'], name='unique_created_updated_price')
        ]

    def __str__(self):
        """String representation of the Listing model."""
        return f"{self.title} - {self.price} - {'Active' if self.is_active else 'Inactive'}"


class Booking(models.Model):
    """Model representing a booking for a listing."""
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property_id = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_booking')
    # listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='listing_bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['property_id', 'user_id', 'start_date', 'end_date'], name='unique_booking_dates')
        ]

    def __str__(self):
        return f"Booking {self.booking_id} by {self.user_id.username} from {self.start_date} to {self.end_date} - {self.status}"


class Review(models.Model):
    """Model representing a review for a listing."""
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property_id = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['property_id', 'user_id', 'created_at', 'updated_at'],\
                             name='unique_review_per_user_created_and_updated_at')
        ]

    def __str__(self):
        return f"Review {self.review_id} for {self.property_id.title} by {self.user_id.username} - Rating: {self.rating}"