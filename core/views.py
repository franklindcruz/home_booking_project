from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .forms import ContactForm
from properties.models import Property
from django.db.models import Q
from django.core.paginator import Paginator

def homepage_view(request):
    if request.user.is_authenticated:
        # Authenticated users see the dashboard
        return render(request, 'dashboard.html')
    else:
        # Guest users see the homepage
        return render(request, 'homepage.html')

def home(request):
    if request.user.is_authenticated:
        return redirect('user_dashboard')

    # Get 20 available properties with related images
    properties = Property.objects.filter(is_available=True).order_by('-created_at')[:20]
    
    context = {
        'properties': properties,
    }
    
    return render(request, 'core/home.html', context)


def home_properties(request):
    properties = Property.objects.filter(is_available=True)
    
    # Get filter values from the GET request
    query = request.GET.get('query', '').strip()  # Search query for title or city
    price_range = request.GET.get('price_range', '')  # Price range filter
    rooms = request.GET.get('rooms', '')  # Number of rooms filter
    bathrooms = request.GET.get('bathrooms', '')  # Number of bathrooms filter
    max_guests = request.GET.get('max_guests', '')  # Max guests filter

    # Apply filters based on query input
    if query:
        properties = properties.filter(
            Q(title__icontains=query) | 
            Q(city__icontains=query) |
            Q(state__icontains=query)
            ) 

    # Apply price range filter
    if price_range:
        properties = properties.filter(price_per_night__lte=price_range)

    # Apply rooms filter (greater than or equal to the selected number)
    if rooms:
        properties = properties.filter(rooms__gte=rooms)

    # Apply bathrooms filter (greater than or equal to the selected number)
    if bathrooms:
        properties = properties.filter(bathrooms__gte=bathrooms)

    # Apply max guests filter (greater than or equal to the selected number)
    if max_guests:
        properties = properties.filter(max_guests__gte=max_guests)


    # Paginate the filtered results (40 properties per page)
    paginator = Paginator(properties, 40)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pass filters to context to retain filter values in the template
    context = {
        'properties': page_obj,
        'query': query,
        'price_range': price_range,
        'rooms': rooms,
        'bathrooms': bathrooms,
        'max_guests': max_guests,
    }

    return render(request, 'core/home_properties.html', context)


# def home_properties(request):
#     query = request.GET.get('query', '')
#     price_range = request.GET.get('price_range', '500')
#     rooms = request.GET.get('rooms', '')
#     bathrooms = request.GET.get('bathrooms', '')
#     max_guests = request.GET.get('max_guests', '')

#     # Filter out unavailable or deleted properties
#     properties = Property.objects.filter(is_deleted=False, is_available=True)
#     # Apply filters
#     if query:
#         properties = properties.filter(
#             Q(title__icontains=query) |
#             Q(city__icontains=query) |
#             Q(state__icontains=query)
#         )

#     if price_range:
#         try:
#             max_price = int(price_range)
#             properties = properties.filter(price_per_night__lte=max_price)
#         except ValueError:
#             messages.error(request, 'Invalid price range.')

#     if rooms:
#         properties = properties.filter(rooms__gte=rooms)

#     if bathrooms:
#         properties = properties.filter(bathrooms__gte=bathrooms)

#     if max_guests:
#         properties = properties.filter(max_guests__gte=max_guests)

#     # Pagination setup (40 properties per page)
#     paginator = Paginator(properties, 40)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     context = {
#         'properties': page_obj,
#         'query': query,
#         'price_range': price_range,
#         'rooms': rooms,
#         'bathrooms': bathrooms,
#         'max_guests': max_guests
#     }

#     return render(request, 'core/home_properties.html', context)

def about(request):
    if request.user.is_authenticated:
        return redirect('user_dashboard')
    return render(request, 'core/about.html')


def faqs(request):
    if request.user.is_authenticated:
        return redirect('user_dashboard')
    return render(request, 'core/faqs.html')


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Get form data
            name = form.cleaned_data['username']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Compose email message
            email_subject = f"Contact Form: {subject}"
            email_message = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
            
            # Send email
            send_mail(email_subject, email_message, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER], fail_silently=False)
            
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form})

