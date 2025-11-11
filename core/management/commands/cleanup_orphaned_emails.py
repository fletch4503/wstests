from django.core.management.base import BaseCommand
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Clean up orphaned EmailAddress records where the associated user does not exist."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Query for orphaned EmailAddress records
        orphaned_emails = EmailAddress.objects.exclude(user__in=User.objects.all())

        count = orphaned_emails.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS("No orphaned EmailAddress records found.")
            )
            return

        if dry_run:
            self.stdout.write(f"Dry run: Found {count} orphaned EmailAddress records:")
            for email in orphaned_emails:
                self.stdout.write(f"  - Email: {email.email}, User ID: {email.user_id}")
        else:
            deleted_count, _ = orphaned_emails.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Deleted {deleted_count} orphaned EmailAddress records."
                )
            )
