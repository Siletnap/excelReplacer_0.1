from django.shortcuts import render, redirect
from .models import Boat, TrafficEntry
from .forms import NewBoatForm, NewTrafficForm
from .utils.paginators import DayPaginator
# from .filters import EntryFilter
from django.db.models import Q, F
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from django.views.generic.edit import FormMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.db import transaction
from django.core.paginator import Paginator, InvalidPage
from django.db.models.expressions import OrderBy
from django.utils.functional import cached_property
from datetime import datetime
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.utils import OperationalError




# Whitelist of UI -> DB field to prevent arbitrary order_by injection.
SORT_MAP = {
    "occurred_at": "occurred_at",  # recommended default
    "created":     "created",
    "boatType":    "boatType",
    "name":        "name",
    "berth":       "berth",
    "trDate":      "trDate",
    "trTime":      "trTime",
    "direction":   "direction",
    "passengers":  "passengers",
    "purpose":     "purpose",
    "edr":         "edr",
    "etr":         "etr",
    "trComments":  "trComments",
}

MAX_PER = 500  # protect DB and template; tune for your infra

class BaseListCreateView(FormMixin, ListView):
    """
    Reusable list+create view with server-side search only.
    Subclasses must set: model, form_class, template_name, success_url.
    They can customize: search_fields, column_list, page_title,
    row_partial, form_partial.
    """
    form_class    = None
    success_url   = None
    search_fields = ()      # e.g. ('name','boatType',...)
    column_list   = ()      # [{'field':'name','label':'Name'}, ...]
    page_title    = ''
    row_partial   = ''
    form_partial  = ''

    def get_success_url(self):
        return self.success_url or self.request.path

    # ---- POST: create via the form and PRG redirect ----
    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        form = self.get_form()
        if form.is_valid():
            form.save()
            return redirect(self.get_success_url())
        # invalid → redisplay with errors + list
        ctx = self.get_context_data(form=form)
        return self.render_to_response(ctx)

    # ---- GET: list + empty form ----
    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "POST":
            kwargs["data"] = self.request.POST
        return kwargs

    def get_form(self, form_class=None):
        """
        Return a form instance if form_class is provided; otherwise return None.

        This allows list-only subclasses to inherit the view without providing
        a create form.
        """
        if form_class is None:
            form_class = self.form_class
        if not form_class:
            return None
        # delegate to FormMixin.get_form for normal behaviour
        return super().get_form(form_class)

    def get_queryset(self):
        qs = super().get_queryset()
        q  = self.request.GET.get("q", "").strip()
        if q and self.search_fields:
            or_query = Q()
            for field in self.search_fields:
                or_query |= Q(**{f"{field}__icontains": q})
            qs = qs.filter(or_query)
        return qs  # no order_by here; sorting is JS-only

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "q":           self.request.GET.get("q", "").strip(),
            "column_list": self.column_list,
            "page_title":  self.page_title,
            "row_partial": self.row_partial,
            "form_partial": self.form_partial,
            "traffic_form": NewTrafficForm(),
            "show_traffic_controls": getattr(self, "show_traffic_controls", False),
        })
        return ctx

class BoatListView(BaseListCreateView):
    model         = Boat
    form_class    = NewBoatForm
    template_name = "lists/list_page.html"     # shared page
    success_url   = reverse_lazy("boats")
    page_title    = "Boat List"

    search_fields = ("name", "boatType", "berth", "state", "cid", "ecod")

    column_list = [
        {"field": "boatType", "label": "Type"},
        {"field": "name",     "label": "Name"},
        {"field": "berth",    "label": "Berth"},
        {"field": "state",    "label": "State"},
        {"field": "cid",      "label": "Check-In"},
        {"field": "ecod",     "label": "Check-Out"},
        {"field": "actions",  "label": "Actions"},
    ]
    row_partial  = "lists/boats/_row.html"
    form_partial = "lists/boats/_form_fields.html"

    def get_queryset(self):
        # Start from BaseListCreateView.get_queryset (this applies q-search)
        qs = super().get_queryset()
        # Only show not-deleted and not-archived boats
        return Boat.objects.visible()

@require_POST
def boat_soft_delete(request, pk):
    """
    Soft-delete a Boat by setting boat.deleted = True.

    Expects POST (AJAX or normal). Returns JSON {ok: True} on success.
    """
    # Optional: restrict to staff/authenticated users
    # if not request.user.is_authenticated:
    #     return JsonResponse({"ok": False, "error": "auth"}, status=403)

    boat = get_object_or_404(Boat, pk=pk)
    # optional: return 400 if already deleted
    if boat.deleted:
        return JsonResponse({"ok": False, "error": "already_deleted"}, status=400)

    now = timezone.now()
    # Retry loop to be resilient to transient "database is locked" on SQLite
    for attempt in range(1, 4):
        try:
            with transaction.atomic():
                Boat.objects.filter(pk=pk, deleted=False).update(
                    deleted=True,
                    deleted_at=now,
                    # deleted_by_id = request.user.pk if you track deleter and field exists
                )
            return JsonResponse({"ok": True, "id": pk})
        except OperationalError as exc:
            if 'locked' in str(exc).lower() and attempt < 3:
                import time
                time.sleep(0.05 * attempt)
                continue
            raise
    return None


class TrafficCreateView(CreateView):
    model = TrafficEntry
    form_class = NewTrafficForm

    def form_invalid(self, form):
        # Return field + non-field errors as JSON for display in the modal
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)

    def form_valid(self, form):
        # Save traffic entry and update the referenced boat (by PK).
        with transaction.atomic():
            obj = form.save()

            # Get submitted boat_id (hidden input). It's optional — check safely.
            boat_id = self.request.POST.get('boat_id')
            updated = 0
            if boat_id:
                try:
                    boat_pk = int(boat_id)
                except (ValueError, TypeError):
                    boat_pk = None
                if boat_pk is not None:
                    # update by PK — efficient single UPDATE query
                    TrafficEntry.objects.filter(pk=obj.pk).update(trafficBoatId_id=boat_pk)
                    if obj.direction == 'arrival':
                        obj.direction = 'in'
                    elif obj.direction == 'departure':
                        obj.direction = 'out'
                    updated = Boat.objects.filter(pk=boat_pk).update(state=obj.direction)

        # Return JSON for AJAX as before
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "id": obj.id, "boat_updated": bool(updated)})
        return super().form_valid(form)



# -- keep SORT_MAP, MAX_PER as you have --

class TrafficListView(BaseListCreateView):
    model         = TrafficEntry
    form_class    = NewTrafficForm
    template_name = "lists/list_page.html"
    success_url   = reverse_lazy("traffic")
    page_title    = "Traffic List"
    show_traffic_controls = True


    search_fields = ("boatType", "name", "trDate", "trTime", "direction",
                     "passengers", "purpose", "edr", "etr", "trComments",
                     "berth", "occurred_at")

    # ---- Controls from GET ----
    @cached_property
    def mode(self):
        m = (self.request.GET.get("mode") or "day").lower()
        return "day" if m == "day" else "per"

    @cached_property
    def per(self):
        if self.mode != "per":
            return None
        try:
            n = int(self.request.GET.get("per", 10))
        except ValueError:
            n = 10
        return max(1, min(n, MAX_PER))

    @cached_property
    def sort_key(self):
        key = (self.request.GET.get("sort") or "occurred_at")
        return key if key in SORT_MAP else "occurred_at"

    @cached_property
    def sort_dir(self):
        d = (self.request.GET.get("dir") or "desc").lower()
        return "asc" if d == "asc" else "desc"

    def get_queryset(self):
        qs = super().get_queryset()  # keeps your search filter
        field = SORT_MAP[self.sort_key]
        if self.sort_dir == "asc":
            ordering = [F(field).asc(nulls_last=True)]
        else:
            ordering = [F(field).desc(nulls_last=True)]
        ordering.append("id")  # stable tiebreaker
        return qs.order_by(*ordering)


    column_list = [
        {"field": "boatType",       "label": "Type"},
        {"field": "name",           "label": "Name"},
        {"field": "trDate",         "label": "Date"},
        {"field": "trTime",         "label": "Time"},
        {"field": "direction",      "label": "Direction"},
        {"field": "passengers",     "label": "Passengers"},
        {"field": "purpose",        "label": "Purpose"},
        {"field": "edr",            "label": "E.R.Date"},
        {"field": "edt",            "label": "E.R.Time"},
        {"field": "trComments",     "label": "Comments"},
        {"field": "berth",          "label": "Berth"},
        {"field": "actions",        "label": "Actions"},
        {"field": "occurred_at",    "label": "Occured at"},
    ]
    row_partial  = "lists/traffic/_row.html"
    form_partial = "lists/traffic/_form_fields.html"


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "mode": self.mode,
            "per": self.per,
            "sort": self.sort_key,
            "dir":  self.sort_dir,
        })

        # pagination
        if self.mode == "day":
            qs = ctx["object_list"]
            paginator = DayPaginator(qs, include_empty_days=True)

            # Min/max for the date picker
            if paginator.days:
                max_day = paginator.days[0]  # newest first in our DayPaginator
                min_day = paginator.days[-1]  # oldest
            else:
                max_day = min_day = None

            # If a specific day is requested, compute its page index
            requested_day_str = self.request.GET.get("day")
            if requested_day_str:
                try:
                    requested_day = datetime.strptime(requested_day_str, "%Y-%m-%d").date()
                except ValueError:
                    requested_day = None
                # If within range, jump there; otherwise clamp to range
                if requested_day and paginator.days:
                    if requested_day > max_day:
                        page_number = 1
                    elif requested_day < min_day:
                        page_number = paginator.num_pages
                    else:
                        try:
                            page_number = paginator.days.index(requested_day) + 1
                        except ValueError:
                            # Shouldn't happen with include_empty_days=True, but guard anyway
                            page_number = 1
                else:
                    page_number = 1
            else:
                page_number = self.request.GET.get("page") or 1
            try:
                page_obj = paginator.page(page_number)
            except InvalidPage:
                page_obj = paginator.page(1)
            ctx.update({
                "is_paginated": True,
                "paginator": paginator,
                "page_obj": page_obj,
                "object_list": page_obj.object_list,
                "group_day": page_obj.day,
                "empty_day": not page_obj.object_list.exists(),
                # expose bounds for the date picker
                "min_day": min_day.isoformat() if min_day else "",
                "max_day": max_day.isoformat() if max_day else "",
            })
        else:
            from django.core.paginator import Paginator
            per = self.per or 10
            paginator = Paginator(ctx["object_list"], per)
            page_number = self.request.GET.get("page") or 1
            try:
                page_obj = paginator.page(page_number)
            except InvalidPage:
                page_obj = paginator.page(1)
            ctx.update({
                "is_paginated": True,
                "paginator": paginator,
                "page_obj": page_obj,
                "object_list": page_obj.object_list,
            })
        return ctx





# class TrafficListView(BaseListCreateView):
#     model         = TrafficEntry
#     form_class    = NewTrafficForm
#     template_name = "lists/list_page.html"     # sharetd page
#     success_url   = reverse_lazy("traffic")
#     page_title    = "Traffic List"
#
#     search_fields = ("boatType", "name", "trDate", "trTime", "direction", "passengers", "purpose", "edr", "etr", "trComments", "berth", "occurred_at")
#
#     # order by occurred_at if present (newer first). If occurred_at is missing / null,
#     # fallback to trDate then trTime so chronological order is preserved as much as possible.
#
#
#     def get_queryset(self):
#         qs = super().get_queryset()
#
#         # best if you have an occurred_at DateTimeField; otherwise fallback:
#
#         if hasattr(self.model, "occurred_at"):
#             return qs.order_by("-occurred_at")
#
#         return qs.order_by("-trDate", "-trTime")
#
#     column_list = [
#         {"field": "boatType",       "label": "Type"},
#         {"field": "name",           "label": "Name"},
#         {"field": "trDate",         "label": "Date"},
#         {"field": "trTime",         "label": "Time"},
#         {"field": "direction",      "label": "Direction"},
#         {"field": "passengers",     "label": "Passengers"},
#         {"field": "purpose",        "label": "Purpose"},
#         {"field": "edr",            "label": "E.R.Date"},
#         {"field": "edt",            "label": "E.R.Time"},
#         {"field": "trComments",     "label": "Comments"},
#         {"field": "berth",          "label": "Berth"},
#         {"field": "actions",        "label": "Actions"},
#         {"field": "occurred_at",    "label": "Occured at"},
#     ]
#     row_partial  = "lists/traffic/_row.html"
#     form_partial = "lists/traffic/_form_fields.html"


class PendingDeletionsView(BaseListCreateView):
    model = Boat
    template_name = "lists/list_page.html"   # new template (see below)
    context_object_name = "objects"
    page_title = "Pending Deletions"
    success_url   = reverse_lazy("pending-deletions")
    show_traffic_controls = False
    paginate_by = 25

    search_fields = ("name", "boatType", "berth")

    column_list = [
        {"field": "boatType",   "label": "Type"},
        {"field": "name",       "label": "Name"},
        {"field": "berth",      "label": "Berth"},
        {"field": "remaining",  "label": "Remaining"},
        {"field": "actions",    "label": "Actions"},
    ]

    row_partial  = "lists/pending_deletions_/_row.html"
    form_partial = "lists/pending_deletions_/empty_form.html"

    def get_queryset(self):
        qs = super().get_queryset()
        # Only deleted and not yet archived
        qs = qs.filter(deleted=True, archived=False).order_by('-deleted_at', '-created')
        q = self.request.GET.get("q", "").strip()
        if q:
            # reuse same simple q search against name/berth/boatType
            qs = qs.filter(Q(name__icontains=q) | Q(berth__icontains=q) | Q(boatType__icontains=q))
        return qs.order_by('-deleted_at', '-created')

# Archive endpoint (set archived=True)
# @login_required
# @user_passes_test(staff_required)
@require_POST
def boat_archive(request, pk):
    boat = get_object_or_404(Boat, pk=pk)
    if boat.archived:
        return JsonResponse({'ok': False, 'error': 'already_archived'}, status=400)
    # Only archive boats that are already deleted (our workflow)
    if not boat.deleted:
        return JsonResponse({'ok': False, 'error': 'not_deleted'}, status=400)

    # lightly retry on sqlite lock
    for attempt in range(1, 4):
        try:
            with transaction.atomic():
                updated = Boat.objects.filter(pk=pk, deleted=True, archived=False).update(
                    archived=True,
                    archived_at=timezone.now()
                )
            return JsonResponse({'ok': bool(updated), 'id': pk})
        except OperationalError as exc:
            if 'locked' in str(exc).lower() and attempt < 3:
                import time;
                time.sleep(0.05 * attempt)
                continue
            raise
    return None


# Cancel pending deletion (unset deleted flag)
# @login_required
# @user_passes_test(staff_required)
@require_POST
def boat_cancel_delete(request, pk):
    boat = get_object_or_404(Boat, pk=pk)
    if not boat.deleted:
        return JsonResponse({'ok': False, 'error': 'not_deleted'}, status=400)

    # retry lightly for sqlite lock in dev
    for attempt in range(1, 4):
        try:
            with transaction.atomic():
                updated = Boat.objects.filter(pk=pk, deleted=True).update(
                    deleted=False,
                    deleted_at=None
                )
            return JsonResponse({'ok': bool(updated), 'id': pk})
        except OperationalError as e:
            if 'locked' in str(e).lower() and attempt < 3:
                import time; time.sleep(0.05 * attempt)
                continue
            raise
    return None


# Helper permission — change to appropriate condition for your app
# def staff_required(user):
#     return user.is_active and user.is_staff

def update(request, pk):
    boat = Boat.objects.get(id = pk)
    form = NewBoatForm(instance=boat)
    if request.method == 'POST':
        form = NewBoatForm(request.POST, instance=boat)
        if form.is_valid():
            form.save()
            return redirect('boats')
    return render(request, 'update.html', {'boat':boat, 'form': form})

def delete(request, pk):
    boat = Boat.objects.get(id = pk)
    if request.method == 'POST':
        boat.delete()
        return redirect('boats')
    return render(request, 'delete.html', {'boat':boat})