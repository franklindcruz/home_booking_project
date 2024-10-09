from django.db import models
from accounts.models import CustomUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _ 
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify


class Amenity(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Property(models.Model):

    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, db_index=True, unique=True)
    city = models.CharField(max_length=255, db_index=True)
    state = models.CharField(max_length=255, db_index=True)
    # Adjusted to a smaller max_length
    zip_code = models.CharField(max_length=20)
    primary_image = models.ImageField(
        upload_to='property_images/', default='home_default.jpg')
    price_per_night = models.IntegerField(validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)
    rooms = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    bathrooms = models.IntegerField(
        validators=[MinValueValidator(1)], default=1)
    max_guests = models.IntegerField(
        validators=[MinValueValidator(1)], default=1)
    amenities = models.ManyToManyField(Amenity, blank=True)
    is_deleted = models.BooleanField(default=False)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-updated_at']

    def __str__(self):
        return self.title

    def clean(self):
        if self.rooms < 1:
            raise ValidationError(_('Number of rooms cannot be less than 1.'))
        if self.bathrooms < 1:
            raise ValidationError(
                _('Number of bathrooms cannot be less than 1.'))
        if self.max_guests < 1:
            raise ValidationError(
                _('Maximum number of guests cannot be less than 1.'))

        if self.price_per_night < 0:
            raise ValidationError(_('Price per night cannot be negative.'))

        if self.primary_image:
            if self.primary_image.size > 5242880:  # 5MB limit
                raise ValidationError(_("Image file too large ( > 5mb )."))
            if not self.primary_image.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                raise ValidationError(
                    _("Invalid image format. Supported formats are .jpg, .jpeg, .png, .webp."))

        super().clean()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        self.full_clean()  # Ensure validation
        super().save(*args, **kwargs)


class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name='property_images')
    image = models.ImageField(
        upload_to='property_images/', null=True, blank=True, default='home_default.jpg')

    def __str__(self):
        return f"Image for {self.property.title}"

    def clean(self):
        if self.image:
            if self.image.size > 5242880:  # 5MB limit
                raise ValidationError(_("Image file too large ( > 5mb )."))
            if not self.image.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                raise ValidationError(
                    _("Invalid image format. Supported formats are .jpg, .jpeg, .png, .webp."))

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensure validation
        super().save(*args, **kwargs)


class Review(models.Model):
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, db_index=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)],
                                 choices=[(i, str(i)) for i in range(1, 6)], default=1)
    comment = models.TextField(blank=True, null=True, max_length=500)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['property', 'user'], name='unique_review_per_user_per_property')]
        ordering = ['-created_at', '-updated_at']

    def __str__(self):
        return f"Review for {self.property.title} by {self.user.username}"

    def clean(self):
        if self.property.owner == self.user:
            raise ValidationError(_('You cannot review your own property.'))
        if not self.property.is_available:
            raise ValidationError(
                _('You cannot review an unavailable property.'))
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensure validation
        super().save(*args, **kwargs)


class Reply(models.Model):
    review = models.OneToOneField(
        Review, on_delete=models.CASCADE, related_name='reply')
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reply_text = models.TextField(max_length=300)  # Recommended size limit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-updated_at']

    def save(self, *args, **kwargs):
        if self.review.property.owner != self.owner:
            raise ValidationError(
                _("You can only reply to your own property's reviews."))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reply to {self.review} by {self.owner.username}"
