from django.urls import path

from . import views

urlpatterns = [
    path('charges', views.charges, name='charges'),
    path('division', views.division, name='division'),

    
    
]
