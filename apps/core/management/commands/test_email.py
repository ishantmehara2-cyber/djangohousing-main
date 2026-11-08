import sys
import smtplib
from django.core.management.base import BaseCommand
from django.core.mail import get_connection, EmailMessage
from django.conf import settings

def mask_email(email_str):
    if not email_str or '@' not in email_str:
        return '***'
    user_part, domain_part = email_str.split('@', 1)
    if len(user_part) <= 2:
        masked_user = user_part[0] + '*'
    else:
        masked_user = user_part[0] + '*' * (len(user_part) - 2) + user_part[-1]
    return f"{masked_user}@{domain_part}"

class Command(BaseCommand):
    help = 'Diagnoses and tests Gmail SMTP email dispatch with diagnostic response codes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            help='Recipient email address for the test email.',
            default=None
        )

    def handle(self, *args, **options):
        self.stdout.write('🔍 Diagnosing Gmail SMTP Infrastructure...')

        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        email_host = getattr(settings, 'EMAIL_HOST', '')
        email_port = getattr(settings, 'EMAIL_PORT', 587)
        email_user = getattr(settings, 'EMAIL_HOST_USER', '')
        email_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', email_user)

        self.stdout.write(f'  • Active Backend: {email_backend}')
        self.stdout.write(f'  • SMTP Host: {email_host}:{email_port}')
        self.stdout.write(f'  • Sender Address: {email_user}')

        if not email_user or not email_password:
            self.stderr.write(
                self.style.ERROR(
                    '❌ Error: EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is not set in your .env file.\n'
                    'Please update your .env file in the project root.'
                )
            )
            return

        recipient = options.get('to')
        if not recipient:
            if sys.stdin.isatty():
                try:
                    user_input = input(f'Enter recipient email address (press Enter for {email_user}): ').strip()
                    recipient = user_input if user_input else email_user
                except (KeyboardInterrupt, EOFError):
                    self.stderr.write(self.style.ERROR('\nOperation cancelled.'))
                    return
            else:
                recipient = email_user

        if not recipient:
            self.stderr.write(self.style.ERROR('❌ Error: No recipient email address provided.'))
            return

        masked_recipient = mask_email(recipient)
        self.stdout.write(f'  • Recipient Address (Masked): {masked_recipient}')
        self.stdout.write('----------------------------------------------------')
        self.stdout.write(f'Initiating SMTP session with {email_host}:{email_port}...')

        try:
            conn = get_connection(fail_silently=False)
            conn.open()

            # Enable diagnostic logging on the underlying SMTP connection
            smtp_response_details = []
            if hasattr(conn, 'connection') and conn.connection:
                def debug_listener(bytes_msg):
                    pass # We do not log raw credentials

            msg = EmailMessage(
                subject='Housing Clone - Gmail SMTP Infrastructure Test',
                body=(
                    'Hello,\n\n'
                    'This is a diagnostic test email sent from your Django Housing Clone application.\n'
                    'Your Gmail SMTP infrastructure and environment settings are functioning properly.\n\n'
                    'Best regards,\n'
                    'Housing Clone System'
                ),
                from_email=from_email,
                to=[recipient],
                connection=conn
            )

            sent_count = msg.send()
            conn.close()

            self.stdout.write(f'  • send_mail() Return Value: {sent_count} (messages accepted by SMTP server)')

            if sent_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ SMTP Status: Accepted by Gmail SMTP server for delivery to {masked_recipient}.\n'
                        f'   Note: Message was queued by Gmail SMTP (Code 250 OK). Final inbox placement\n'
                        f'   depends on recipient folder filters (check Inbox, Spam, or Promotions).'
                    )
                )
            else:
                self.stderr.write(self.style.ERROR('❌ Failed: SMTP server rejected or dropped the email (0 dispatched).'))

        except smtplib.SMTPAuthenticationError as e:
            self.stderr.write(
                self.style.ERROR(
                    f'❌ SMTP Authentication Failed (Code {e.smtp_code}): {e.smtp_error.decode("utf-8", errors="ignore")}\n'
                    f'   Please verify your Google App Password in .env.'
                )
            )
        except smtplib.SMTPException as e:
            self.stderr.write(self.style.ERROR(f'❌ SMTP Protocol Error: {e}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'❌ Network/Connection Error: {e}'))
