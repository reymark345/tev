from django.urls import path

from . import views

urlpatterns = [

    path('updateuser', views.updateuser, name='update-user'),
    path('users', views.users, name='users'),
    path('user_add', views.user_add, name='user-add'),
    path('user_edit', views.user_edit, name='user-edit'),
    path('role_edit', views.role_edit, name='role-edit'),
    path('role_update', views.role_update, name='role-update'),
    path('user_update', views.user_update, name='user-update'),
    path('update_password', views.update_password, name='update-password'),
    path('user_load', views.user_load, name='user-load'),

]
