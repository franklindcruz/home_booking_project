from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, DetailView, ListView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Booking
from .forms import BookingForm, BookingUpdateForm, BookingCancellationForm
from properties.models import Property
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from payment.models import Payment  # Assumed to be in payments app
from django.http import JsonResponse


# Booking a specific property
class BookPropertyView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'booking/booking_form.html'  # Create this template
    success_url = reverse_lazy('booking:booking-confirm')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        property_id = self.kwargs.get('id')
        property_instance = get_object_or_404(Property, id=property_id)
        context['property'] = property_instance
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.property = get_object_or_404(Property, id=self.kwargs.get('id'))
        form.instance.total_cost = form.instance.calculate_total_cost()

        # Check for overlapping bookings and other validations
        try:
            form.instance.clean()
        except ValidationError as e:
            form.add_error(None, e.message)
            return self.form_invalid(form)

        booking = form.save(commit=False)
        booking.status = 'pending'
        booking.save()

        # Redirect to the payment page
        return redirect('payments:initiate-payment', booking_id=booking.id)


# Booking update
class BookingUpdateView(LoginRequiredMixin, UpdateView):
    model = Booking
    form_class = BookingUpdateForm
    template_name = 'booking/booking_update.html'
    success_url = reverse_lazy('booking:booking-list')

    def form_valid(self, form):
        booking = self.get_object()
        if booking.status not in ['pending', 'confirmed']:
            messages.error(self.request, "You cannot update a completed or ongoing booking.")
            return redirect('booking:booking-detail', pk=booking.id)

        form.instance.total_cost = form.instance.calculate_total_cost()

        # Check for overlapping bookings and other validations handled in the form
        try:
            form.instance.clean()
        except ValidationError as e:
            form.add_error(None, e.message)
            return self.form_invalid(form)

        return super().form_valid(form)

# Booking detail
class BookingDetailView(LoginRequiredMixin, DetailView):
    model = Booking
    template_name = 'booking/booking_detail.html'
    context_object_name = 'booking'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.get_object()
        payment = Payment.objects.filter(booking=booking).first()
        context['payment'] = payment
        return context

# List of user bookings
class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'booking/booking_list.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by('-created_at')

# Booking cancellation
class BookingCancelView(LoginRequiredMixin, View):
    form_class = BookingCancellationForm
    template_name = 'booking/booking_cancellation.html'
    success_url = reverse_lazy('booking:booking-list')

    def get(self, request, pk, *args, **kwargs):
        booking = get_object_or_404(Booking, pk=pk)
        if booking.user != request.user:
            messages.error(request, "You are not authorized to cancel this booking.")
            return redirect('booking:booking-list')

        if booking.status not in ['pending', 'confirmed', 'ongoing']:
            messages.error(request, "You cannot cancel a completed or already cancelled booking.")
            return redirect('booking:booking-detail', pk=pk)

        form = self.form_class(initial={'booking_id': booking.id})
        return render(request, self.template_name, {'form': form, 'booking': booking})

    def post(self, request, pk, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            booking = Booking.objects.get(id=form.cleaned_data['booking_id'])
            if booking.user != request.user:
                messages.error(request, "You are not authorized to cancel this booking.")
                return redirect('booking:booking-list')

            # Cancel the booking and process refund if necessary
            booking.cancel_booking()
            messages.success(request, "Your booking has been successfully cancelled.")
            return redirect('booking:booking-list')
        else:
            messages.error(request, "There was an issue processing your cancellation request.")
            return redirect('booking:booking-detail', pk=pk)

# Booking confirmation
class BookingConfirmView(LoginRequiredMixin, View):
    template_name = 'booking/booking_confirm.html'

    def get(self, request, *args, **kwargs):
        booking_id = request.GET.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        if booking.status != 'pending':
            messages.error(request, "This booking cannot be confirmed at this time.")
            return redirect('booking:booking-list')

        return render(request, self.template_name, {'booking': booking})


# View to return disabled (unavailable) booking dates for a property
def disabled_dates(request, id):
    property_instance = get_object_or_404(Property, id=id)
    bookings = Booking.objects.filter(property=property_instance, status='confirmed')

    disabled_dates = []
    for booking in bookings:
        # Add all dates between check-in and check-out to disabled_dates
        date_range = [booking.check_in + timezone.timedelta(days=i)
                      for i in range((booking.check_out - booking.check_in).days)]
        disabled_dates.extend(date_range)

    return JsonResponse(disabled_dates, safe=False)