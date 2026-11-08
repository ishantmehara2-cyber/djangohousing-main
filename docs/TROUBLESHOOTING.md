# Troubleshooting Guide

- **Database Connection Errors**: Verify MySQL service is running and credentials in `.env` are correct.
- **Static Files Not Loading**: Run `python manage.py collectstatic` and verify `STATIC_ROOT` settings.
- **CSRF Verification Failed**: Ensure `ALLOWED_HOSTS` includes your deployment domain and HTTPS cookies are properly configured if `DEBUG=False`.
