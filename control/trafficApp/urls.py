from django.urls import path
from . import views


urlpatterns = [
    path('', views.BoatListView.as_view(), name = 'boats'),
    path('traffic/', views.TrafficListView.as_view(), name = 'traffic'),
    path('update/<int:pk>', views.update, name = 'update'),
    path('delete_boat/<int:pk>', views.delete, name = 'delete'),
    path("traffic/create/", views.TrafficCreateView.as_view(), name="traffic-create"),  # POST target
    path("boats/<int:pk>/soft-delete/", views.boat_soft_delete, name="boat-soft-delete"),
    path('pending_deletions/', views.PendingDeletionsView.as_view(), name='pending-deletions'),
    path('pending_deletions/<int:pk>/archive/', views.boat_archive, name='boat-archive'),
    path('pending_deletions/<int:pk>/cancel_delete/', views.boat_cancel_delete, name='boat-cancel-delete'),
]