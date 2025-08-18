from django.shortcuts import render, redirect
from .models import Boat, TrafficEntry
from .forms import NewBoatForm, NewTrafficForm
# from .filters import EntryFilter
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from django.views.generic.edit import FormMixin
from django.http import JsonResponse
from django.db import transaction

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
                    pk = int(boat_id)
                except (ValueError, TypeError):
                    pk = None
                if pk is not None:
                    # update by PK — efficient single UPDATE query
                    updated = Boat.objects.filter(pk=pk).update(state=obj.direction)

        # Return JSON for AJAX as before
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "id": obj.id, "boat_updated": bool(updated)})
        return super().form_valid(form)

class TrafficListView(BaseListCreateView):
    model         = TrafficEntry
    form_class    = NewTrafficForm
    template_name = "lists/list_page.html"     # sharetd page
    success_url   = reverse_lazy("traffic")
    page_title    = "Traffic List"

    search_fields = ("boatType", "name", "trDate", "trTime", "direction", "passengers", "purpose", "edr", "etr", "trComments", "berth")

    column_list = [
        {"field": "boatType",   "label": "Type"},
        {"field": "name",       "label": "Name"},
        {"field": "trDate",     "label": "Date"},
        {"field": "trTime",     "label": "Time"},
        {"field": "direction",  "label": "Direction"},
        {"field": "passengers", "label": "Passengers"},
        {"field": "purpose",    "label": "Purpose"},
        {"field": "edr",        "label": "E.R.Date"},
        {"field": "edt",        "label": "E.R.Time"},
        {"field": "trComments", "label": "Comments"},
        {"field": "berth",      "label": "Berth"},
        {"field": "actions",      "label": "Actions"},
    ]
    row_partial  = "lists/traffic/_row.html"
    form_partial = "lists/traffic/_form_fields.html"

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

# def traffic(request):
#     return render(request, 'traffic.html')

# def index(request):
#     # ---------- handle the create form ----------
#     if request.method == "POST":
#         form = NewBoatForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect("index")          # PRG pattern
#     else:
#         form = NewBoatForm()
#
#     # ---------- build the queryset ----------
#     boats = Boat.objects.all()                # base queryset
#     q      = request.GET.get("q", "").strip() # search term
#
#
#     if q:                                     # filter on *either* column
#         boats = boats.filter(
#             Q(name__icontains=q) |            # case‑insensitive contains  :contentReference[oaicite:0]{index=0}
#             Q(boatType__icontains=q) |
#             Q(berth__icontains=q) |
#             Q(state__icontains=q) |
#             Q(cid__icontains=q)|
#             Q(ecod__icontains=q)
#         )
#
#
#     column_list = [
#         {'field': 'boatType', 'label': 'Type'},
#         {'field': 'name', 'label': 'Name'},
#         {'field': 'berth', 'label': 'Berth'},
#         {'field': 'state', 'label': 'State'},
#         {'field': 'cid', 'label': 'Check-In'},
#         {'field': 'ecod', 'label': 'Check-Out'},
#         {'field': 'actions', 'label': 'Actions'},
#     ]
#
#     ctx = {
#         "form": form,
#         "boats": boats,
#         "q": q,
#         "column_list": column_list,
#     }
#
#     return render(request, "index.html", ctx)
