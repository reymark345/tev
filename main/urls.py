from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('admin/', include('admin.urls')),
    path('receive/', include('receive.urls')),
    path('transaction/', include('transaction.urls')),

]
