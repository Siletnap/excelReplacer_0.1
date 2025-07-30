from django.shortcuts import render, redirect
from .models import Boat
from .forms import NewBoatForm
# from .filters import EntryFilter
from django.db.models import Q


def index(request):
    # ---------- handle the create form ----------
    if request.method == "POST":
        form = NewBoatForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("index")          # PRG pattern
    else:
        form = NewBoatForm()

    # ---------- build the queryset ----------
    boats = Boat.objects.all()                # base queryset
    q      = request.GET.get("q", "").strip() # search term


    if q:                                     # filter on *either* column
        boats = boats.filter(
            Q(name__icontains=q) |            # case‑insensitive contains  :contentReference[oaicite:0]{index=0}
            Q(boatType__icontains=q) |
            Q(berth__icontains=q) |
            Q(state__icontains=q) |
            Q(cid__icontains=q)|
            Q(ecod__icontains=q)
        )


    column_list = [
        {'field': 'boatType', 'label': 'Type'},
        {'field': 'name', 'label': 'Name'},
        {'field': 'berth', 'label': 'Berth'},
        {'field': 'state', 'label': 'State'},
        {'field': 'cid', 'label': 'Check-In'},
        {'field': 'ecod', 'label': 'Check-Out'},
        {'field': 'actions', 'label': 'Actions'},
    ]

    ctx = {
        "form": form,
        "boats": boats,
        "q": q,
        "column_list": column_list,
    }

    return render(request, "index.html", ctx)

def update(request, pk):
    boat = Boat.objects.get(id = pk)
    form = NewBoatForm(instance=boat)
    if request.method == 'POST':
        form = NewBoatForm(request.POST, instance=boat)
        if form.is_valid():
            form.save()
            return redirect('index')
    return render(request, 'update.html', {'boat':boat, 'form': form})

def delete(request, pk):
    boat = Boat.objects.get(id = pk)
    if request.method == 'POST':
        boat.delete()
        return redirect('index')
    return render(request, 'delete.html', {'boat':boat})

def traffic(request):
    return render(request, 'traffic.html')
