from django import forms
from django.utils import timezone
from .models import Booking
from django.core.exceptions import ValidationError
from properties.models import Property

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['check_in', 'check_out', 'guests']
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date', 'id': 'checkin-date'}),
            'check_out': forms.DateInput(attrs={'type': 'date', 'id': 'checkout-date'}),
        }
        labels = {
            'check_in': 'Check-in Date',
            'check_out': 'Check-out Date',
            'guests': 'Number of Guests',
        }

    def clean_check_in(self):
        check_in = self.cleaned_data.get('check_in')
        if check_in and check_in < timezone.now().date() + timezone.timedelta(days=1):
            raise forms.ValidationError("Check-in date must be at least one day from today.")
        return check_in
    
    def clean_check_out(self):
        check_out = self.cleaned_data.get('check_out')
        check_in = self.cleaned_data.get('check_in')
        if check_out and check_in and check_out <= check_in:
            raise forms.ValidationError("Check-out date must be after check-in date.")
        return check_out

    def calculate_total_cost(self):
        """
        Calculate total cost based on the property price per night and duration of stay.
        """
        check_in = self.cleaned_data.get('check_in')
        check_out = self.cleaned_data.get('check_out')
        property = self.instance.property

        if check_in and check_out and property:
            duration = (check_out - check_in).days
            total_cost = duration * property.price_per_night
            return total_cost
        return 0

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.total_cost = self.calculate_total_cost()  # Calculate total cost when saving the form

        if commit:
            instance.save()
        return instance

class BookingUpdateForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['check_in', 'check_out', 'guests']
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date'}),
            'check_out': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'check_in': 'Check-in Date',
            'check_out': 'Check-out Date',
            'guests': 'Number of Guests',
        }

    def clean_check_in(self):
        check_in = self.cleaned_data.get('check_in')
        if check_in and check_in < timezone.now().date() + timezone.timedelta(days=1):
            raise forms.ValidationError("Check-in date must be at least one day from today.")
        return check_in
    
    def clean_check_out(self):
        check_out = self.cleaned_data.get('check_out')
        check_in = self.cleaned_data.get('check_in')
        if check_out and check_in and check_out <= check_in:
            raise forms.ValidationError("Check-out date must be after check-in date.")
        return check_out

    def clean_guests(self):
        guests = self.cleaned_data.get('guests')
        property = self.instance.property

        if property and guests > property.max_guests:
            raise forms.ValidationError(f"Guest count cannot exceed the maximum limit of {property.max_guests}.")
        
        return guests

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        property = self.instance.property

        if property and check_in and check_out:
            if self.is_overlapping(property, check_in, check_out):
                raise forms.ValidationError("The selected dates are already booked.")

        return cleaned_data

    @staticmethod
    def is_overlapping(property, check_in, check_out):
        overlapping_bookings = Booking.objects.filter(
            property=property,
            check_in__lt=check_out,
            check_out__gt=check_in,
            status__in=['confirmed', 'ongoing']
        ).exclude(id=self.instance.id)  # type: ignore
        return overlapping_bookings.exists()

    def calculate_total_cost(self):
        check_in = self.cleaned_data.get('check_in')
        check_out = self.cleaned_data.get('check_out')
        property = self.instance.property

        if check_in and check_out and property:
            duration = (check_out - check_in).days
            total_cost = duration * property.price_per_night
            return total_cost
        return 0

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.total_cost = self.calculate_total_cost()

        if commit:
            instance.save()
        return instance


class BookingCancellationForm(forms.Form):
    booking_id = forms.IntegerField(widget=forms.HiddenInput())
    cancellation_reason = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.Textarea(attrs={'placeholder': 'Reason for cancellation (optional)', 'rows': 3})
    )

    def clean_booking_id(self):
        booking_id = self.cleaned_data.get('booking_id')
        try:
            booking = Booking.objects.get(id=booking_id)
            if booking.status not in ['confirmed', 'ongoing']:
                raise forms.ValidationError("You can only cancel confirmed or ongoing bookings.")
        except Booking.DoesNotExist:
            raise forms.ValidationError("Booking not found.")
        return booking_id
          
    def save(self):
        booking = Booking.objects.get(id=self.cleaned_data['booking_id'])
        booking.cancel_booking()
        return booking
