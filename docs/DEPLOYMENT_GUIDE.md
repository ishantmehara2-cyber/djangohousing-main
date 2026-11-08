# Production Deployment Guide

1. Set `DEBUG=False` in production environment.
2. Configure strong `SECRET_KEY` and production `ALLOWED_HOSTS`.
3. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```
4. Set up Gunicorn / uWSGI with Nginx reverse proxy and SSL (HTTPS).
5. Configure MySQL production database and run migrations.
