from django.urls import path
from . import views


urlpatterns = [
    # path('', views.index, name = 'index'),
    path('', views.BoatListView.as_view(), name = 'boats'),
    path('traffic/', views.TrafficListView.as_view(), name = 'traffic'),
    path('update/<int:pk>', views.update, name = 'update'),
    path('delete_boat/<int:pk>', views.delete, name = 'delete'),
    path("traffic/create/", views.TrafficCreateView.as_view(), name="traffic-create"),  # POST target
    #path('traffic', views.traffic, name = 'traffic'),
]
#fotios11
