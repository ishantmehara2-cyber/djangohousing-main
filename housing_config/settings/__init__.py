import os
from pathlib import Path
import dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv.load_dotenv(os.path.join(BASE_DIR, '.env'))

ENVIRONMENT = os.getenv('DJANGO_ENV', 'development').lower()

if ENVIRONMENT == 'production':
    from .production import *
else:
    from .development import *
