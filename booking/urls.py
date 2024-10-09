from django.urls import path
from .views import (
    BookPropertyView,
    BookingUpdateView,
    BookingDetailView,
    BookingListView,
    BookingCancelView,
    BookingConfirmView,
    disabled_dates
)

app_name = 'booking'

urlpatterns = [
    path('book/<int:id>/', BookPropertyView.as_view(), name='book_property'),
    path('update/<int:pk>/', BookingUpdateView.as_view(), name='booking-update'),
    path('detail/<int:pk>/', BookingDetailView.as_view(), name='booking-detail'),
    path('list/', BookingListView.as_view(), name='booking-list'),
    path('cancel/<int:pk>/', BookingCancelView.as_view(), name='booking-cancel'),
    path('confirm/', BookingConfirmView.as_view(), name='booking-confirm'),
    path('disabled-dates/<int:id>/', disabled_dates, name='disabled-dates'),  # Add this pattern
]
