from django.conf import settings


class AdminSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request is for the admin site
        if request.path.startswith('/admin/'):
            # Modify session for admin requests
            # Flag for admin session
            request.session['is_admin_session'] = True
            request.session.set_expiry(3600)  # Admin session timeout in 1 hour
            request.session.save()

        # Else, handle user session separately
        elif request.path.startswith('/accounts/') or request.path.startswith('/users/'):
            request.session['is_user_session'] = True  # Flag for user session
            # User session timeout in 24 hours
            request.session.set_expiry(86400)
            request.session.save()

        response = self.get_response(request)
        return response
