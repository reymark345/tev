from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('view_stats_year', views.view_stats_year, name='view-stats-year'),
    path('profile', views.profile, name='profile'),
    path('tris', views.landing, name='landing'),
    path('admin/', include('admin.urls')),
    path('receive/', include('receive.urls')),
    path('tracking/', include('tracking.urls')),
    path('transaction/', include('transaction.urls')),
    path('libraries/', include('libraries.urls')),
    path('generate_accomplishment', views.generate_accomplishment, name='generate-accomplishment'),
    path('generate_accomplishment_admin', views.generate_accomplishment_admin, name='generate-accomplishment-admin'),
    path('mfa-verify', views.mfa_verify, name='mfa-verify'),
    path('mfa_update', views.mfa_update, name='mfa-update'),
]
