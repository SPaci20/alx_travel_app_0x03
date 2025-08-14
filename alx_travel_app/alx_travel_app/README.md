# alx_travel_app_0x02
alx_travel_app_0x02
Objective

Integrate the Chapa API for handling payments, allowing users to make bookings with secure payment options. Configure the API to initiate and verify payments and handle the payment status accordingly.

Instructions

Duplicate Project:

Duplicate the project alx_travel_app_0x01 to alx_travel_app_0x02
Set Up Chapa API Credentials:

Create an account with Chapa (https://developer.chapa.co/) to obtain the API keys.
Store the API keys in environment variables for security (CHAPA_SECRET_KEY).
Create Payment Model:

In listings/models.py, create a Payment model to store payment-related information such as booking reference, payment status, amount, and transaction ID.
Create Payment API View:

In listings/views.py, create an API endpoint that initiates the payment by making a POST request to the Chapa API with booking details.
Upon initiating the payment, store the transaction ID returned by Chapa and set the initial status to “Pending.”
Verify Payment:

Add an endpoint in the API to verify the payment status with Chapa after a user completes a payment.
Update the payment status in the Payment model based on the verification response from Chapa (e.g., “Completed” or “Failed”).
Implement Payment Workflow:

When a user creates a booking, initiate the payment process and provide them with a link to complete the payment via Chapa.
On successful payment, send a confirmation email to the user (using Celery for background tasks).
Handle any errors or payment failures gracefully, updating the status in the Payment model accordingly.
Test Payment Integration:

Use Chapa’s sandbox environment to test payment initiation and verification.
Ensure the entire payment workflow functions correctly, from initiation to status verification.