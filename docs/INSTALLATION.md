# Installation Guide

## Prerequisites
- Python 3.10+
- MySQL 8.0+ (or SQLite for development)
- Git

## Step-by-Step Setup
1. Clone repository:
   ```bash
   git clone <repository-url>
   cd housing-clone-django
   ```
2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Start development server:
   ```bash
   python manage.py runserver
   ```
