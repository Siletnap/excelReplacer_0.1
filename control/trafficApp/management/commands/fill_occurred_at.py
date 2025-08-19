# trafficApp/management/commands/fill_occurred_at.py
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import datetime, time
from trafficApp.models import TrafficEntry

BATCH_SIZE = 200

class Command(BaseCommand):
    help = "Populate TrafficEntry.occurred_at from trDate and trTime.\n" \
           "Rules:\n" \
           " - both trDate and trTime present -> combine them\n" \
           " - trDate present, trTime missing -> use trDate at 00:00\n" \
           " - trDate missing -> skip (cannot infer)"

    def handle(self, *args, **options):
        qs = TrafficEntry.objects.filter(occurred_at__isnull=True)
        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("No rows to update."))
            return

        self.stdout.write(f"Found {total} entries with null occurred_at. Processing...")

        to_update = []
        processed = 0

        for entry in qs.iterator():
            processed += 1
            tr_date = entry.trDate
            tr_time = entry.trTime

            if not tr_date:
                # Nothing we can do without a date
                self.stdout.write(f"Skipping id={entry.pk}: no trDate")
                continue

            if tr_time:
                dt = datetime.combine(tr_date, tr_time)   # date + time
            else:
                # trTime missing -> use midnight (00:00)
                dt = datetime.combine(tr_date, time.min)

            # If your project uses timezones, make the datetime aware
            if settings.USE_TZ:
                # use project's default timezone
                tz = timezone.get_default_timezone()
                dt = timezone.make_aware(dt, tz)

            entry.occurred_at = dt
            to_update.append(entry)

            # Flush in batches
            if len(to_update) >= BATCH_SIZE:
                TrafficEntry.objects.bulk_update(to_update, ['occurred_at'], batch_size=BATCH_SIZE)
                self.stdout.write(f"Updated {len(to_update)} entries (processed {processed}/{total})")
                to_update = []

        # final flush
        if to_update:
            TrafficEntry.objects.bulk_update(to_update, ['occurred_at'], batch_size=BATCH_SIZE)
            self.stdout.write(f"Updated final {len(to_update)} entries")

        self.stdout.write(self.style.SUCCESS("Done."))
