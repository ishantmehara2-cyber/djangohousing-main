import os
from pathlib import Path
import dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(os.path.join(BASE_DIR, '.env'))

ENVIRONMENT = os.getenv('DJANGO_ENV', 'development').lower()

if ENVIRONMENT == 'production':
    from housing_config.settings.production import *
else:
    from housing_config.settings.development import *
