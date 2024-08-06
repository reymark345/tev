from django.urls import path

from . import views

urlpatterns = [

    path('updateuser', views.updateuser, name='update-user'),
    path('users', views.users, name='users'),
    path('form_controls', views.form_controls, name='form_controls'),
    path('sms', views.sms, name='sms'),
    path('send_sms', views.send_sms, name='send-sms'),
    path('user_add', views.user_add, name='user-add'),
    path('user_edit', views.user_edit, name='user-edit'),
    path('role_edit', views.role_edit, name='role-edit'),
    path('role_update', views.role_update, name='role-update'),
    path('user_update', views.user_update, name='user-update'),
    path('update_password', views.update_password, name='update-password'),
    path('user_load', views.user_load, name='user-load'),
    path('date_actual_update', views.date_actual_update, name='date-actual-update'),
    path('transaction_logs', views.transaction_logs, name='transaction-logs'),
    path('logs_load', views.logs_load, name='logs-load'),
    path('chat', views.chat, name='chat'),
    path('chat_data', views.chat_data, name='chat-data'),
    path('chat_staff', views.chat_staff, name='chat-staff'),
    path('chat_data_staff', views.chat_data_staff, name='chat-data-staff'),
    path('send_chat', views.send_chat, name='send-chat'),
    path('', views.CreateRoom, name='create-room'),
    path('<str:room_name>/<str:username>/', views.MessageView, name='room'),

]
