from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    # The fields to be used in displaying the User model.
    list_display = ('email', 'username', 'first_name', 'last_name', 'phone', 'city',
                    'state', 'zip_code', 'profile_image_preview', 'is_active', 'is_staff', 'created_at')

    # Search functionality in the admin panel
    search_fields = ('email', 'username', 'first_name',
                     'last_name', 'phone', 'city')

    # Filters in the admin panel (Filter by staff status, active status, creation date, state)
    list_filter = ('is_active', 'is_staff',
                   'is_superuser', 'state', 'created_at')

    # Fields editable directly from the list view for quick actions
    list_editable = ('is_active', 'is_staff')

    # Ordering by most recent users first
    ordering = ('-created_at',)

    # Specify the read-only fields
    readonly_fields = ('created_at', 'last_login', 'date_joined')

    # Fieldsets
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name',
         'phone', 'city', 'state', 'zip_code', 'profile_pic')}),
        ('Permissions', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # When adding a new user, specify the fields
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'phone', 'city', 'state', 'zip_code', 'password1', 'password2'),
        }),
    )

    # Adding profile image preview in the form
    def profile_image_preview(self, obj):
        if obj.profile_pic:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.profile_pic.url)
        return "No Image"

    profile_image_preview.short_description = "Profile Image"

    # Add custom actions (e.g., activate/deactivate multiple users)
    actions = ['activate_users', 'deactivate_users']

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, "Selected users have been activated.")

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Selected users have been deactivated.")

    activate_users.short_description = "Activate selected users"
    deactivate_users.short_description = "Deactivate selected users"


# Register the CustomUser model with the customized admin
admin.site.register(CustomUser, CustomUserAdmin)
