from django.urls import path
from . import views

urlpatterns = [
    path('status/<str:id_number>/', views.getStatus),
    path('data/<str:dv_no>/', views.getData),
]
