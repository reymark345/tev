from django.urls import path
from . import views

# urlpatterns = [
#     path('', views.getData),
#     path('/data', views.getStatus),
# ]


urlpatterns = [
    path('status/<str:id_number>/', views.getStatus),
    path('data/<str:dv_no>/', views.getData),
]
