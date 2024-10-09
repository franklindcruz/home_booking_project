from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('homepage/', views.homepage_view, name='homepage'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faqs/', views.faqs, name='faqs'),
    path('all_properties/', views.home_properties, name='home_properties'),
]
