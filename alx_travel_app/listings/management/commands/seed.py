# Implement Seeders:

# Create a management command in listings/management/commands/seed.py to populate the database with sample listings data.
# Run Seed Command:

# Test the seeder by running the command to populate the database with sample data.

from django.core.management.base import BaseCommand
from listings.models import Listing, Review
from django.contrib.auth import get_user_model
import uuid
import random

class Command(BaseCommand):
    help = 'Seed the database with sample data for listings and reviews'

    def handle(self, *args, **kwargs):

        Listing = []
        # Create sample listings
        for _ in range(10):
            listing = Listing.objects.create(
                title=f"Sample Listing {uuid.uuid4()}",
                description="This is a sample listing description.",
                price=random.uniform(50.0, 500.0),
                is_active=True
            )
            Listing.append(listing)
            self.stdout.write(self.style.SUCCESS(f"Created listiing"))

            # Create sample reviews for each listing
            Review = []
            for j in range(5):
                review = Review.objects.create(
                    property_id=listing,
                
                    rating=random.randint(1, 5),
                    comment="This is a sample review."
                )
                Review.append(review)
                self.stdout.write(f"Created review for {listing.title} by {get_user_model.username}")