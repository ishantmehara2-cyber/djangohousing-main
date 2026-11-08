# Housing.clone Django Edition — Production Deployment Guide

## 1. Prerequisites
- Ubuntu 22.04 LTS Server / VPS
- Python 3.10+ & Virtualenv
- MySQL 8.0+ / MariaDB
- Redis (optional for caching/celery)
- Nginx & Gunicorn

---

## 2. Server Setup & Repository Clone
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx mysql-server redis-server -y

cd /var/www
git clone <repository_url> housing-clone-django
cd housing-clone-django
```

---

## 3. Virtual Environment & Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Environment Configuration
Create production `.env` file:
```bash
DJANGO_ENV=production
DEBUG=False
SECRET_KEY=your_secure_random_secret_key_here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_ENGINE=django.db.backends.mysql
DB_NAME=housing_clone_django
DB_USER=housing_db_user
DB_PASSWORD=your_secure_db_password
DB_HOST=127.0.0.1
DB_PORT=3306

REDIS_URL=redis://127.0.0.1:6379/0
SECURE_SSL_REDIRECT=True
```

---

## 5. Database Migration & Static Collection
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

---

## 6. Gunicorn & Systemd Service Configuration
Copy systemd service:
```bash
sudo cp systemd/housing.service /etc/systemd/system/housing.service
sudo systemctl daemon-reload
sudo systemctl start housing
sudo systemctl enable housing
```

---

## 7. Nginx Reverse Proxy Setup
```bash
sudo cp nginx/housing_nginx.conf /etc/nginx/sites-available/housing
sudo ln -s /etc/nginx/sites-available/housing /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 8. SSL Certificate (Certbot)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 9. Automated Database Backups & Background Tasks (Cron)
Add cron jobs:
```bash
crontab -e
```
Add:
```cron
0 2 * * * /var/www/housing-clone-django/.venv/bin/python /var/www/housing-clone-django/manage.py db_backup
0 * * * * /var/www/housing-clone-django/.venv/bin/python /var/www/housing-clone-django/manage.py process_scheduled_tasks
```
