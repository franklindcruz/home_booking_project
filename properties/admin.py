from django.contrib import admin
from properties.models import Property, PropertyImage, Amenity
from django.utils.html import format_html

# Inline for PropertyImage
class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1  # Number of empty forms for adding images
    
    # Display a small preview of the uploaded image in the list display
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: auto;" />', obj.image.url)
        return ""
    image_preview.short_description = 'Image Preview'


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'city', 'state', 'price_per_night','is_deleted' ,'is_available', 'created_at', 'updated_at', 'primary_image_preview')
    list_filter = ('city', 'state', 'is_available', 'created_at', 'updated_at')
    search_fields = ('title', 'city', 'state', 'owner__email', 'owner__phone')
    readonly_fields = ['slug', 'created_at', 'updated_at', 'primary_image_preview']  # Add primary_image_preview here
    
    # Inline for related images to show them in the Property admin page
    inlines = [PropertyImageInline]

    # To handle many-to-many fields like amenities
    filter_horizontal = ('amenities',)

    # Image preview method
    def primary_image_preview(self, obj):
        if obj.primary_image:
            return format_html('<img src="{}" style="width: 50px; height: auto;" />', obj.primary_image.url)
        return ""
    primary_image_preview.short_description = 'Primary Image'


    # Customize the admin form display
    fieldsets = (
        (None, {
            'fields': ('owner', 'title', 'city', 'state', 'zip_code', 'rooms', 'bathrooms', 'max_guests', 'price_per_night', 'is_available', 'is_deleted','primary_image')  # Remove primary_image_preview from here
        }),
        ('Additional Info', {
            'fields': ('amenities',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'image_preview')
    
    # Image preview in the list display
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 100px; height: auto;" />', obj.image.url)
        return ""
    image_preview.short_description = 'Image Preview'
