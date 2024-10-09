from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .forms import UserRegisterForm, UpdateProfileForm, ChangePasswordForm, ForgetPasswordForm
from accounts.models import CustomUser
from properties.models import Property

# Create your views here.
def user_register(request):
    if request.user.is_authenticated:
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request=request)
        # check user already exists
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful!")
            return redirect('login')
        else:
            # Handle non-field errors if needed
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = UserRegisterForm( request=request)
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_user')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser or user.is_staff:
                messages.error(request, 'You are not authorized to log in from this page.')
                return redirect('login')

            login(request, user)

            # Set session expiry based on the remember_me checkbox
            request.session.set_expiry(1209600 if remember_me else 0)  # 2 weeks or browser close
            messages.success(request, 'Logged in successfully')
            return redirect('home')

        messages.error(request, 'Username or Password is incorrect')

    return render(request, 'accounts/login.html')


def user_logout(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('home')


@login_required
def user_dashboard(request):
    user = request.user
    properties = Property.objects.filter(owner=user)
    return render(request, 'accounts/user_dashboard.html', {'properties': properties})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data.get('old_password')
            new_password = form.cleaned_data.get('password1')
            user = request.user

            if not user.check_password(old_password):
                messages.error(request, 'Incorrect old password')
                return redirect('change_password')

            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)

            messages.success(request, 'Password changed successfully')
            return redirect('user_profile', id=user.id)

        messages.error(request, 'Passwords do not match')
    
    form = ChangePasswordForm()
    return render(request, 'accounts/change_password.html', {'form': form})


def forgot_password(request):
    if request.method == 'POST':
        form = ForgetPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                # Email logic
                reset_link = f"{request.scheme}://{request.get_host()}/reset/{uid}/{token}/"
                mail_subject = "Reset your password"
                message = render_to_string('accounts/password_reset_email.html', {
                    'user': user,
                    'reset_link': reset_link
                })
                send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [email])

                messages.success(request, 'Password reset email sent successfully')
                return redirect('login')

            except CustomUser.DoesNotExist:
                messages.error(request, 'Email does not exist')

    form = ForgetPasswordForm()
    return render(request, 'accounts/forgot_password.html', {'form': form})



def user_profile(request, id):
    profile_user = get_object_or_404(CustomUser, id=id)
    return render(request, 'accounts/profile.html', {'profile_user': profile_user})


@login_required
def update_profile(request, id):
    user = get_object_or_404(CustomUser, id=id)
    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('user_profile', id=id)
    
    form = UpdateProfileForm(instance=user)
    return render(request, 'accounts/update_profile.html', {'form': form})
