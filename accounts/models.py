
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=15, blank=True,
                             null=True, db_index=True)
    city = models.CharField(max_length=100, blank=True,
                            null=True, db_index=True)
    state = models.CharField(max_length=100, blank=True,
                             null=True, db_index=True)
    zip_code = models.CharField(
        max_length=20, blank=True, null=True, db_index=True)
    profile_pic = models.ImageField(
        upload_to='profile_images/', blank=True, null=True, default='avatar_pic.jpg')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    # Validate phone number
    def clean(self):
        if self.phone:
            if len(self.phone) < 10:
                raise ValidationError(
                    "Phone number must be at least 10 digits long.")
            if not self.phone.isdigit():
                raise ValidationError("Phone number must contain only digits.")
        return super().clean()

    def save(self, *args, **kwargs):
        if self.profile_pic:
            # Check file size
            if self.profile_pic.size > 5242880:
                raise ValidationError("Image file too large ( > 5mb )")

            # Check file format
            if not self.profile_pic.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValidationError(
                    "Invalid image format. Supported formats are .jpg, .jpeg, .png")

            # Check image dimensions
            width, height = get_image_dimensions(self.profile_pic)
            if width > 5000 or height > 5000:
                raise ValidationError(
                    "Image dimensions are too large (max 5000x5000).")

        super().save(*args, **kwargs)
