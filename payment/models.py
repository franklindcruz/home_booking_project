from django.db import models
from django.forms import ValidationError
from accounts.models import CustomUser
from booking.models import Booking
from django.utils import timezone
from decimal import Decimal
import razorpay  # type: ignore


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('net_banking', 'Net Banking'),
        ('upi', 'UPI'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')

    # Razorpay-specific fields
    razorpay_order_id = models.CharField(
        max_length=100, blank=True, null=True, unique=True)
    razorpay_payment_id = models.CharField(
        max_length=100, blank=True, null=True, unique=True)
    razorpay_signature = models.CharField(
        max_length=255, blank=True, null=True)
    payment_gateway_response = models.JSONField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-updated_at']
        indexes = [
            models.Index(fields=['user', 'payment_status']),
        ]

    def __str__(self):
        return f"Payment for Booking ID: {self.booking.id} by {self.user.username}"

    def clean(self):
        # Ensure the payment amount matches the booking total cost
        if self.amount <= Decimal('0.00'):
            raise ValidationError("Payment amount must be greater than zero.")
        if self.amount != self.booking.total_cost:
            raise ValidationError(
                "Payment amount does not match the booking total cost.")
        super().clean()

    def initiate_payment(self, razorpay_client):
        """
        Initiates a Razorpay payment by creating an order in Razorpay.
        """
        if not self.razorpay_order_id:
            order_data = {
                'amount': int(self.amount * 100),
                'currency': 'INR',
                'receipt': f'booking_{self.booking.id}',
                'payment_capture': '1',  # Auto-capture payment
            }
            order = razorpay_client.order.create(order_data)
            self.razorpay_order_id = order['id']
            self.save()
        return self.razorpay_order_id

    def verify_payment(self, razorpay_client, payment_data):
        """
        Verifies the Razorpay payment signature and updates the payment status.
        """
        try:
            # Verify Razorpay signature
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': payment_data['razorpay_order_id'],
                'razorpay_payment_id': payment_data['razorpay_payment_id'],
                'razorpay_signature': payment_data['razorpay_signature'],
            })

            # Update payment details
            self.razorpay_payment_id = payment_data['razorpay_payment_id']
            self.razorpay_signature = payment_data['razorpay_signature']
            self.payment_status = 'completed'
            self.save()

            # Confirm the booking only if the payment was successful
            if self.booking.status == 'pending':
                self.booking.confirm_booking()

            return True
        except razorpay.errors.SignatureVerificationError:
            # Mark payment as failed
            self.payment_status = 'failed'
            self.save()

            # Optional: Automatically cancel the booking if payment failed
            if self.booking.status == 'pending':
                self.booking.cancel_booking()

        return False

    def refund_payment(self, razorpay_client):
        """
        Refund the payment through Razorpay. This assumes that the payment was completed successfully.
        """
        if self.payment_status == 'completed':
            refund = razorpay_client.payment.refund(self.razorpay_payment_id, {
                'amount': int(self.amount * 100),
            })
            if refund['status'] == 'processed':
                self.payment_status = 'refunded'
                self.save()
                return True
        return False

    def update_status_based_on_dates(self):
        """
        Automatically update the payment status based on the booking status.
        """
        if self.payment_status == 'pending' and self.booking.status == 'confirmed':
            self.payment_status = 'completed'
            self.save()
        elif self.payment_status == 'completed' and self.booking.status != 'confirmed':
            self.payment_status = 'failed'
            self.save()
        return self.payment_status

    def cancel_payment(self):
        """
        Cancels the payment if it is not yet completed and triggers refund if necessary.
        """
        if self.payment_status == 'pending':
            self.payment_status = 'failed'
            self.save()
        elif self.payment_status == 'completed':
            self.refund_payment()
        return self.payment_status

    def complete_payment(self):
        """
        Marks the payment as completed once the booking is confirmed.
        This can be called automatically or manually depending on the flow.
        """
        if self.payment_status == 'pending' and self.booking.status == 'confirmed':
            self.payment_status = 'completed'
            self.save()
        return self.payment_status

    def update_payment_status(self):
        """
        Update the payment status based on the booking status.
        """
        if self.payment_status == 'pending' and self.booking.status == 'confirmed':
            self.payment_status = 'completed'
            self.save()
        elif self.payment_status == 'completed' and self.booking.status != 'confirmed':
            self.payment_status = 'failed'
            self.save()
        return self.payment_status

    def update_payment_status_based_on_dates(self):
        """
        Automatically update the payment status based on the booking status.
        """
        if self.payment_status == 'pending' and self.booking.status == 'confirmed':
            self.payment_status = 'completed'
            self.save()
        elif self.payment_status == 'completed' and self.booking.status != 'confirmed':
            self.payment_status = 'failed'
            self.save()
        return self.payment_status

    def update_payment_status_based_on_booking(self):
        """
        Update the payment status based on the booking status.
        """
        if self.payment_status == 'pending' and self.booking.status == 'confirmed':
            self.payment_status = 'completed'
            self.save()
        elif self.payment_status == 'completed' and self.booking.status != 'confirmed':
            self.payment_status = 'failed'
            self.save()
        return self.payment_status

    def update_payment_status_based_on_booking_status(self):
        """
        Update the payment status based on the booking status.
        """
        if self.payment_status == 'pending' and self.booking.status == 'confirmed':
            self.payment_status = 'completed'
            self.save()
        elif self.payment_status == 'completed' and self.booking.status != 'confirmed':
            self.payment_status = 'failed'
            self.save()
        return self.payment_status

    def update_payment_status_based_on_booking_dates(self):
        """
        Automatically update the payment status based on the booking status.
        """
        if self.payment_status == 'pending' and self.booking.status == 'confirmed':
            self.payment_status = 'completed'
            self.save()
        elif self.payment_status == 'completed' and self.booking.status != 'confirmed':
            self.payment_status = 'failed'
            self.save()
        return self.payment_status
