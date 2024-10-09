from django.urls import path
from . import views

urlpatterns = [

    # Property views
    path('add/', views.add_property, name='add_property'),
    path('edit/<int:id>/', views.edit_property, name='edit_property'),
    path('delete/<int:id>/', views.delete_property, name='delete_property'),

    # Property image views
    path('<int:id>/images/add/', views.add_images, name='add_images'),
    path('<int:id>/images/edit/', views.edit_images, name='edit_images'),

    # Property listing and details views
    path('list/', views.properties_list, name='properties_list'),
    path('details/<int:id>/', views.property_details, name='property_details'),

    # User's properties
    path('my-properties/', views.my_properties, name='my_properties'),
]

