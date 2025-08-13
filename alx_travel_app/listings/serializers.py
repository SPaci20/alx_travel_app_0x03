#Set Up Serializers:

#Create serializers in listings/serializers.py for Listing and Booking models.

from rest_framework import serializers
from .models import  Listing, Booking, User


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255, required=False, read_only=True)
    last_name = serializers.CharField(max_length=255, required=False, read_only=True)
    phone_number = serializers.CharField(max_length=14, required=True)
    class Meta:
        model = User
        fields = ('id', 'username',
                  'email', 'first_name',
                  'phone_number', 'password',
                  'last_name'
                  )
        read_only_fields = ('id','password',
                            'phone_number', 'last_name',
                            'first_name',
                            )  # Prevent ID modification

class ListingSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    title = serializers.CharField(max_length=255, required=True)
    class Meta:
        model = Listing
        fields = '__all__'
        read_only_fields = ['id', 'created_at',
                            'updated_at','description',
                            'is_active', 'price',
                            'title','ceated_at',
                            'updated_at'
                            ]
        extra_kwargs = {
            'title': {'required': True, 'max_length': 255},
            'description': {'required': True},
            'price': {'required': True, 'max_digits': 10, 'decimal_places': 2},
            'is_active': {'default': True}
        }

class BookingSerializer(serializers.ModelSerializer):
        # listings = ListingSerializer(many=True, read_only=True)
        user_id = serializers.PrimaryKeyRelatedField(
            read_only=True, source='user_id.username')
        start_date =serializers.DateField()
        end_date = serializers.DateField()
        total_price = serializers.DecimalField(
             max_digits=10,
             decimal_places=2,
             read_only=True
             )
        status = serializers.CharField(read_only=True)
        created_at = serializers.DateTimeField(read_only=True)
        updated_at = serializers.DateTimeField(read_only=True)
        property_id = serializers.PrimaryKeyRelatedField(
             many=True,
             read_only=True
             )


        def validate(self, data):
             '''
             Custom validation to ensure user is authenticated
             before creating a booking.
             '''
                # Check if the user is authenticated
             request = self.context.get('request')
             if not request.user.is_authenticated:
                 raise serializers.ValidationError("User must be authenticated to create a booking.")
             return data
        class Meta:
            model = Booking
            fields = '__all__'
            read_only_fields = ['booking_id', 'created_at',
                                'updated_at', 'status', 
                                'property_id', 'user_id',
                                'total_price','user_id',
                                'start_date','end_date',''
                                ]
            extra_kwargs = {
                'property_id': {'required': True},
                'user_id': {'required': True},
                'start_date': {'required': True},
                'end_date': {'required': True},
                'total_price': {
                     'required': True, 
                     'max_digits': 10,
                     'decimal_places': 2
                     },
                'status': {'default': 'pending'}
            }