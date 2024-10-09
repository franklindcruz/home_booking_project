from django.urls import path
from .views import PaymentInitiateView, PaymentConfirmationView

app_name = 'payments'

urlpatterns = [
    path('initiate-payment/<int:booking_id>/', PaymentInitiateView.as_view(), name='initiate-payment'),
    path('payment-confirmation/', PaymentConfirmationView.as_view(), name='payment-confirmation'),
]
