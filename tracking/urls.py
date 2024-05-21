from django.urls import path

from . import views

urlpatterns = [
    path('status', views.status, name='status'),
    path('travel_history', views.travel_history, name='travel-history'),
    path('travel_calendar', views.travel_calendar, name='travel-calendar'),
    path('status_load', views.status_load, name='status-load'),
    path('travel_history_load', views.travel_history_load, name='travel-history-load'),
    path('employee_details', views.employee_details, name='employee-details'),
    path('export_status', views.export_status, name='export-status'),
    
]
