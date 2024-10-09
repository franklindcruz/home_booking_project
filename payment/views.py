
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from booking.models import Booking
from django.conf import settings
import razorpay # type: ignore

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))

class PaymentInitiateView(LoginRequiredMixin, View):
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        order_data = {
            "amount": int(booking.total_cost * 100),
            "currency": "INR",
            "payment_capture": "1",
        }

        order = razorpay_client.order.create(data=order_data)
        booking.razorpay_order_id = order['id']
        booking.save()

        context = {
          'order': order, 
          'booking': booking, 
          'razorpay_key': settings.RAZORPAY_KEY
          }
        
        return render(request, 'payment/payment.html', context)

class PaymentConfirmationView(View):
    def post(self, request):
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature,
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)

            booking = Booking.objects.get(razorpay_order_id=order_id)
            booking.status = 'confirmed'
            booking.save()

            messages.success(request, "Payment successful! Your booking is confirmed.")
            return redirect('booking:booking-list')

        except Exception as e:
            messages.error(request, "Payment verification failed. Please try again.")
            return redirect('booking:booking-list')
