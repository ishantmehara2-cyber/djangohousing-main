import os
import datetime
import shutil
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Creates a timestamped backup of the database (SQLite or MySQL)'

    def handle(self, *args, **options):
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        db_settings = settings.DATABASES['default']
        engine = db_settings['ENGINE']
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        if 'sqlite3' in engine:
            db_path = db_settings['NAME']
            backup_file = os.path.join(backup_dir, f'backup_sqlite_{timestamp}.sqlite3')
            shutil.copy2(db_path, backup_file)
            self.stdout.write(self.style.SUCCESS(f"Successfully backed up SQLite database to {backup_file}"))
        elif 'mysql' in engine:
            db_name = db_settings['NAME']
            db_user = db_settings['USER']
            db_password = db_settings['PASSWORD']
            db_host = db_settings['HOST']
            db_port = db_settings['PORT']
            backup_file = os.path.join(backup_dir, f'backup_mysql_{timestamp}.sql')

            cmd = f"mysqldump -h {db_host} -P {db_port} -u {db_user} {f'-p{db_password}' if db_password else ''} {db_name} > \"{backup_file}\""
            ret = os.system(cmd)
            if ret == 0:
                self.stdout.write(self.style.SUCCESS(f"Successfully backed up MySQL database to {backup_file}"))
            else:
                self.stdout.write(self.style.ERROR(f"MySQL backup failed with exit code {ret}"))
        else:
            self.stdout.write(self.style.WARNING(f"Database engine {engine} is not explicitly supported for automatic backup."))
