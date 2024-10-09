from django import forms
from accounts.models import CustomUser
from django.contrib.auth.forms import UserCreationForm
import mimetypes
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name',
                  'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # Remove the request from the kwargs
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].label = ''
            self.fields[fieldname].help_text = ''
            placeholder = {
                'username': 'Username',
                'first_name': 'First Name',
                'last_name': 'Last Name',
                'email': 'Email',
                'password1': 'Password',
                'password2': 'Confirm Password',
            }
            self.fields[fieldname].widget.attrs.update(
                {'placeholder': placeholder.get(fieldname, fieldname.replace('_', ' ').title())})
            self.fields[fieldname].error_messages.update({
                'required': f'{placeholder.get(fieldname, fieldname.replace("_", " ").title())} is required',
                'invalid': f'Enter a valid {placeholder.get(fieldname, fieldname.replace("_", " ").title())}'
            })

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            # Use the stored request
            messages.error(self.request, "Username already exists")
            raise forms.ValidationError("Username already exists")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            messages.error(self.request, "Passwords do not match")
            raise forms.ValidationError("Passwords do not match")


class ForgetPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={'placeholder': 'Email', 'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].label = ''
            self.fields[fieldname].help_text = ''
            placeholder = {
                'email': 'Email',
            }
            self.fields[fieldname].widget.attrs.update(
                {'placeholder': placeholder.get(fieldname, fieldname.replace('_', ' ').title())})
            self.fields[fieldname].error_messages.update({
                'required': f'{placeholder.get(fieldname, fieldname.replace("_", " ").title())} is required',
                'invalid': f'Enter a valid {placeholder.get(fieldname, fieldname.replace("_", " ").title())}'
            })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Email does not exists")
        return email


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Old Password', 'class': 'form-control'}),
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder': 'New Password', 'class': 'form-control'}),
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Confirm Password', 'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].label = ''
            self.fields[fieldname].help_text = ''
            placeholder = {
                'old_password': 'Old Password',
                'password1': 'New Password',
                'password2': 'Confirm Password',
            }
            self.fields[fieldname].widget.attrs.update(
                {'placeholder': placeholder.get(fieldname, fieldname.replace('_', ' ').title())})
            self.fields[fieldname].error_messages.update({
                'required': f'{placeholder.get(fieldname, fieldname.replace("_", " ").title())} is required',
                'invalid': f'Enter a valid {placeholder.get(fieldname, fieldname.replace("_", " ").title())}'
            })

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn’t match.")
        return cleaned_data

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        validate_password(password1)
        return password1


class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone',
                  'city', 'state', 'zip_code', 'profile_pic']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone', 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-control'}),
            'state': forms.TextInput(attrs={'placeholder': 'State', 'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'placeholder': 'Zip Code', 'class': 'form-control'}),
            'profile_pic': forms.FileInput(attrs={'accept': 'image/*', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].label = None
            self.fields[fieldname].help_text = None
            placeholder = {
                'username': 'Username',
                'email': 'Email',
                'phone': 'Phone',
                'city': 'City',
                'state': 'State',
                'zip_code': 'Zip Code',
            }
            self.fields[fieldname].widget.attrs.update(
                {'placeholder': placeholder.get(fieldname, fieldname.replace('_', ' ').title())})
            self.fields[fieldname].error_messages.update({
                'required': f'{placeholder.get(fieldname, fieldname.replace("_", " ").title())} is required',
                'invalid': f'Enter a valid {placeholder.get(fieldname, fieldname.replace("_", " ").title())}'
            })
        self.fields['profile_pic'].widget.attrs.update(
            {'accept': 'image/*', 'placeholder': 'Profile Picture'})
        self.fields['profile_pic'].error_messages.update({
            'required': 'Profile Picture is required',
            'invalid': 'Enter a valid Profile Picture'
        })
        self.fields['profile_pic'].help_text = 'Profile Picture should be less than 5mb and format jpg, jpeg, png'

    def clean_profile_pic(self):
        profile_pic = self.cleaned_data.get('profile_pic')
        if profile_pic:
            # Validate file size (limit: 5MB)
            if profile_pic.size > 5 * 1024 * 1024:
                raise ValidationError("Image file too large ( > 5MB )")

            # Validate file format
            mime_type, _ = mimetypes.guess_type(profile_pic.name)
            if mime_type not in ['image/jpeg', 'image/png']:
                raise ValidationError(
                    'Unsupported file format. Please upload a jpg, jpeg, or png image.')
        return profile_pic
