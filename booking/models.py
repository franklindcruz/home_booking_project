from django.db import models
from accounts.models import CustomUser
from properties.models import Property
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from razorpay import Client  # type: ignore # Import the Razorpay Client for initiating refunds

class Booking(models.Model):
    BOOKING_STATUS_CHOICES = (
        ('pending', 'Pending'),           # Initial state before payment
        ('confirmed', 'Confirmed'),       # After successful payment
        ('ongoing', 'Ongoing'),           # After check-in date is reached
        ('completed', 'Completed'),       # After check-out date is passed
        ('cancelled', 'Cancelled'),       # If booking is cancelled
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateTimeField()
    check_out = models.DateTimeField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    guests = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    status = models.CharField(
        max_length=10, choices=BOOKING_STATUS_CHOICES, default='pending')
    # in your Booking model
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"Booking ID: {self.id} - {self.property.title} by {self.user.username}"

    def clean(self):
        # Ensure check-in is before check-out
        if self.check_in >= self.check_out:
            raise ValidationError("Check-out date must be after check-in date.")

        # Ensure total cost is valid
        if self.total_cost <= 0:
            raise ValidationError("Total cost must be greater than zero.")

        # Ensure the number of guests does not exceed property limits
        if self.guests <= 0:
            raise ValidationError("Number of guests must be at least one.")
        if self.guests > self.property.max_guests:
            raise ValidationError(f"Number of guests exceeds the property limit of {self.property.max_guests}.")
        
        super().clean()

    def confirm_booking(self):
        """
        Confirm the booking after successful payment.
        """
        if self.status == 'pending':
            self.status = 'confirmed'
            self.save()

    def update_status_based_on_dates(self):
        """
        Automatically update the booking status based on check-in and check-out dates.
        """
        now = timezone.now()
        if self.status == 'confirmed' and self.check_in <= now < self.check_out:
            self.status = 'ongoing'
            self.save()
        elif self.status == 'ongoing' and now >= self.check_out:
            self.status = 'completed'
            self.save()

    def cancel_booking(self):
        """
        Cancels the booking if it is not yet completed and triggers refund if necessary.
        """
        if self.status not in ['cancelled', 'completed']:
            self.status = 'cancelled'
            self.save()
            
            # Check if payment was completed and trigger refund
            payment = self.payment_set.filter(payment_status='completed').first()
            if payment:
                razorpay_client = Client(auth=("RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET"))
                payment.refund_payment(razorpay_client)

    def complete_booking(self):
        """
        Marks the booking as completed once the stay is over.
        This can be called automatically or manually depending on the flow.
        """
        if self.status == 'ongoing' and timezone.now() >= self.check_out:
            self.status = 'completed'
            self.save()
            
    def calculate_total_cost(self):
        """
        Calculate the total cost based on the property price and duration of stay.
        """
        duration = self.check_out - self.check_in
        total_days = duration.days
        total_cost = total_days * self.property.price_per_night
        return total_cost
    
    def save(self, *args, **kwargs):
        if not self.total_cost:
            self.total_cost = self.calculate_total_cost()
        self.full_clean()
        super().save(*args, **kwargs)
