from django import forms
from properties.models import Property, PropertyImage, Amenity
from django.forms import modelformset_factory


class AddPropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        exclude = ['slug', 'created_at', 'updated_at', 'is_deleted', 'owner']
        widgets = {
            'amenities': forms.CheckboxSelectMultiple(),  # Ensure amenities is present
            'price_per_night': forms.NumberInput(attrs={'min': 0}),
            'rooms': forms.NumberInput(attrs={'min': 1}),
            'bathrooms': forms.NumberInput(attrs={'min': 1}),
            'max_guests': forms.NumberInput(attrs={'min': 1}),
        }

    def clean(self):
        cleaned_data = super().clean()
        rooms = cleaned_data.get('rooms')
        bathrooms = cleaned_data.get('bathrooms')
        max_guests = cleaned_data.get('max_guests')
        price_per_night = cleaned_data.get('price_per_night')
        primary_image = cleaned_data.get('primary_image')

        if rooms < 1:
            raise forms.ValidationError(
                'Number of rooms cannot be less than 1.')
        if bathrooms < 1:
            raise forms.ValidationError(
                'Number of bathrooms cannot be less than 1.')
        if max_guests < 1:
            raise forms.ValidationError(
                'Maximum number of guests cannot be less than 1.')
        if price_per_night < 0:
            raise forms.ValidationError('Price per night cannot be negative.')
        if primary_image:
            if primary_image.size > 5242880:
                raise forms.ValidationError('Image file too large ( > 5mb ).')
            if not primary_image.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                raise forms.ValidationError(
                    'Invalid image format. Supported formats are .jpg, .jpeg, .png, .webp.')
        return cleaned_data

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner', None)  # Add owner from kwargs
        super().__init__(*args, **kwargs)
        self.fields['amenities'].queryset = Amenity.objects.all()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.owner:  # Assign the owner before saving
            instance.owner = self.owner
        if commit:
            instance.save()
            self.save_m2m()  # Save many-to-many relationships
        return instance


class PropertyImageForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ['image']

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')

        if image:
            if image.size > 5242880:  # 5MB limit
                raise forms.ValidationError('Image file too large ( > 5mb ).')
            if not image.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                raise forms.ValidationError('Invalid image format. Supported formats are .jpg, .jpeg, .png, .webp.')
        
        return cleaned_data


PropertyImageFormSet = modelformset_factory(
    PropertyImage, fields=('image',), extra=3)
