from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from properties.models import Property, PropertyImage, Review
# No need for PropertyImageForm since it’s handled in the formset
from properties.forms import AddPropertyForm, PropertyImageFormSet

# View to add a new property


@login_required
def add_property(request):
    if request.method == 'POST':
        form = AddPropertyForm(request.POST, request.FILES, owner=request.user)
        if form.is_valid():
            property_instance = form.save()
            messages.success(request, 'Property added successfully!')
            return redirect('add_images', id=property_instance.id)
        else:
            messages.error(
                request, 'Error adding property. Please correct the issues.')
    else:
        form = AddPropertyForm(owner=request.user)

    return render(request, 'properties/add_property.html', {'form': form})


# View to add images to a property
@login_required
def add_images(request, id):
    property_instance = get_object_or_404(Property, id=id, owner=request.user)

    max_images = 3
    existing_images_count = PropertyImage.objects.filter(
        property=property_instance).count()
    remaining_images = max_images - existing_images_count

    if remaining_images <= 0:
        messages.error(
            request, 'You have reached the maximum number of images for this property.')
        return redirect('property_details', id=property_instance.id)

    # Use the globally defined PropertyImageFormSet
    if request.method == 'POST':
        formset = PropertyImageFormSet(
            request.POST, request.FILES, queryset=PropertyImage.objects.filter(property=property_instance))

        if formset.is_valid():
            for form in formset:
                if form.cleaned_data.get('image'):
                    image_instance = form.save(commit=False)
                    image_instance.property = property_instance
                    image_instance.save()

            messages.success(request, 'Images added successfully.')
            return redirect('property_details', id=property_instance.id)
        else:
            messages.error(
                request, 'Error adding images. Please correct the issues.')
    else:
        formset = PropertyImageFormSet(
            queryset=PropertyImage.objects.filter(property=property_instance))

    return render(request, 'properties/add_images.html', {
        'formset': formset,
        'property': property_instance,
        'remaining_images': remaining_images,
    })


# View to edit property images
@login_required
def edit_images(request, id):
    property_instance = get_object_or_404(Property, id=id, owner=request.user)

    if request.method == 'POST':
        formset = PropertyImageFormSet(
            request.POST, request.FILES, queryset=PropertyImage.objects.filter(property=property_instance))

        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.property = property_instance
                instance.save()

            for form in formset.deleted_forms:
                if form.instance.pk:
                    form.instance.delete()

            messages.success(request, 'Images updated successfully')
            return redirect('property_details', id=property_instance.id)
        else:
            messages.error(
                request, 'Error updating images. Please correct the issues.')
    else:
        formset = PropertyImageFormSet(
            queryset=PropertyImage.objects.filter(property=property_instance))

    return render(request, 'properties/edit_images.html', {
        'formset': formset,
        'property': property_instance,
    })


# View to edit a property
@login_required
def edit_property(request, id):
    property_instance = get_object_or_404(Property, id=id)

    if request.user != property_instance.owner:
        raise PermissionDenied

    if request.method == 'POST':
        form = AddPropertyForm(request.POST, request.FILES,
                               instance=property_instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property updated successfully.')
            return redirect('my_properties')
        else:
            messages.error(
                request, 'Error updating property. Please correct the issues.')
    else:
        form = AddPropertyForm(instance=property_instance)

    return render(request, 'properties/edit_property.html', {'form': form, 'property': property_instance})


# View to delete a property
@login_required
def delete_property(request, id):
    property_instance = get_object_or_404(Property, id=id, owner=request.user)

    if request.method == 'POST':
        property_instance.delete()
        messages.success(
            request, f'The property "{property_instance.title}" was deleted successfully.')
        return redirect('my_properties')

    return render(request, 'properties/confirm_delete.html', {'property': property_instance})


# View to list all properties with filters
def properties_list(request):
    properties = Property.objects.filter(is_available=True)

    query = request.GET.get('query', '').strip()
    price_range = request.GET.get('price_range', '')
    rooms = request.GET.get('rooms', '')
    bathrooms = request.GET.get('bathrooms', '')
    max_guests = request.GET.get('max_guests', '')

    if query:
        properties = properties.filter(
            Q(title__icontains=query) |
            Q(city__icontains=query) |
            Q(state__icontains=query)
        )
    if price_range:
        properties = properties.filter(price_per_night__lte=price_range)
    if rooms:
        properties = properties.filter(rooms__gte=rooms)
    if bathrooms:
        properties = properties.filter(bathrooms__gte=bathrooms)
    if max_guests:
        properties = properties.filter(max_guests__gte=max_guests)

    paginator = Paginator(properties, 40)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'properties/properties_list.html', {
        'properties': page_obj,
        'query': query,
        'price_range': price_range,
        'rooms': rooms,
        'bathrooms': bathrooms,
        'max_guests': max_guests
    })


# View to show property details
def property_details(request, id):
    property_instance = get_object_or_404(Property, id=id, is_deleted=False)
    images = PropertyImage.objects.filter(property=property_instance)
    reviews = Review.objects.filter(property=property_instance, is_deleted=False)
    
    # Check if the user has booked this property
    has_booked = property_instance.bookings.filter(user=request.user).exists() if request.user.is_authenticated else False
    
    context = {
        'property': property_instance,
        'images': images,
        'reviews': reviews,
        'has_booked': has_booked
    }
    return render(request, 'properties/property_details.html', context)

# View to list properties added by the logged-in user
@login_required
def my_properties(request):
    search_query = request.GET.get('search', '')

    properties = Property.objects.filter(owner=request.user)

    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(price_per_night__icontains=search_query)
        )

    return render(request, 'properties/my_properties.html', {
        'properties': properties,
        'search_query': search_query
    })
