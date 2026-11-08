# Database Setup (MySQL / SQLite)

## SQLite (Default Development)
Out-of-the-box zero-config SQLite (`db.sqlite3`) is enabled when `DB_ENGINE=django.db.backends.sqlite3`.

## MySQL Production Setup
1. Create MySQL database:
   ```sql
   CREATE DATABASE housing_clone_django CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. Configure `.env` with MySQL credentials.
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Seed initial locations, packages, and property types:
   ```bash
   python manage.py seed_locations
   python manage.py seed_packages
   ```
