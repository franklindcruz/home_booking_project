from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('djadmin/', admin.site.urls),
    
    path('accounts/', include('accounts.urls')),
    path('admin/', include('admin_app.urls')),
    path('booking/', include('booking.urls')),
    path('', include('core.urls')),
    path('properties/', include('properties.urls')),
    path('payment/', include('payment.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
