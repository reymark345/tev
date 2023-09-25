from django.urls import path

from . import views

urlpatterns = [
    path('tracking_list', views.tracking_list, name='tracking-list'),
    path('travel_history', views.travel_history, name='travel-history'),
    path('tracking_load', views.tracking_load, name='tracking-load'),
    path('travel_history_load', views.travel_history_load, name='travel-history-load'),
    
]
