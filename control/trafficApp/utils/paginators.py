# trafficApp/utils/paginators.py
from datetime import timedelta
from django.core.paginator import InvalidPage
from django.db.models import Min, Max, F
from django.db.models.functions import TruncDate, Coalesce

class DayPage:
    """A minimal Page-like object Django templates expect."""
    def __init__(self, *, day, object_list, number, paginator):
        self.day = day
        self.object_list = object_list
        self.number = number
        self.paginator = paginator

    def has_other_pages(self): return self.paginator.num_pages > 1
    def has_previous(self):    return self.number > 1
    def has_next(self):        return self.number < self.paginator.num_pages
    def previous_page_number(self):
        if not self.has_previous(): raise InvalidPage("No previous page")
        return self.number - 1
    def next_page_number(self):
        if not self.has_next(): raise InvalidPage("No next page")
        return self.number + 1

class DayPaginator:
    """
    Paginates a queryset by calendar day (descending), optionally including empty days.
    Expects the queryset to be fully filtered/sorted for intra-day order already.
    """
    def __init__(self, base_qs, *, include_empty_days=True):
        self.base_qs = base_qs

        # Normalize a date column: day = date(occurred_at) or fallback to trDate
        dates_qs = (
            base_qs
            .annotate(day=Coalesce(TruncDate("occurred_at"), F("trDate")))
            .exclude(day__isnull=True)
        )

        if include_empty_days:
            agg = dates_qs.aggregate(min=Min("day"), max=Max("day"))
            start, end = agg["min"], agg["max"]
            self.days = []
            if start and end:
                cur = end
                while cur >= start:
                    self.days.append(cur)
                    cur -= timedelta(days=1)
        else:
            self.days = list(
                dates_qs.values_list("day", flat=True).distinct().order_by("-day")
            )

        self.count = len(self.days)
        self.num_pages = self.count or 1
        self.page_range = range(1, self.num_pages + 1)

    def page(self, number):
        try:
            number = int(number or 1)
        except ValueError:
            raise InvalidPage("Invalid page number")

        if number < 1 or number > self.num_pages:
            raise InvalidPage("That page does not exist")

        if not self.days:  # no rows at all
            return DayPage(day=None, object_list=self.base_qs.none(), number=1, paginator=self)

        day = self.days[number - 1]
        day_qs = (
            self.base_qs
            .annotate(day=Coalesce(TruncDate("occurred_at"), F("trDate")))
            .filter(day=day)
        )
        return DayPage(day=day, object_list=day_qs, number=number, paginator=self)
