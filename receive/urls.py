from django.urls import path

from . import views

urlpatterns = [
    path('list', views.list, name='receive-list'),
    path('addtev', views.addtev, name='add-tev'),
    path('addtevdetails', views.addtevdetails, name='add-tev-details'),
    path('tevemployee', views.tevemployee, name='tev-employee'),
    path('tracking', views.tracking, name='receive-tracking'),
    
    path('item_load', views.item_load, name='item-load'),
    path('item_edit', views.item_edit, name='item-edit'),
    path('item_update', views.item_update, name='item-update'),
    path('item_add', views.item_add, name='item-add'),
    path('item_returned', views.item_returned, name='item-returned'),
    
    path('out_pending_tev', views.out_pending_tev, name='out-pending-tev'),
    path('tev_details', views.tev_details, name='tev-details'),

    path('checking', views.checking, name='receive-checking'),
    path('api', views.api, name='receive-api'),
    
    
]
