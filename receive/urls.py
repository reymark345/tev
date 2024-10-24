from django.urls import path

from . import views

urlpatterns = [
    path('travel_list', views.travel_list, name='travel-list'),
    path('list', views.list, name='receive-list'),
    path('addtev', views.addtev, name='add-tev'),
    path('addtevdetails', views.addtevdetails, name='add-tev-details'),
    path('updatetevdetails', views.updatetevdetails, name='update-tev-details'),
    path('updatetevamount', views.updatetevamount, name='update-tev-amount'),
    path('tevemployee', views.tevemployee, name='tev-employee'),
    
    path('travel_load', views.travel_load, name='travel-load'),
    path('item_load', views.item_load, name='item-load'),
    path('checking_load', views.checking_load, name='checking-load'),
    path('item_edit', views.item_edit, name='item-edit'),
    path('preview_received', views.preview_received, name='preview-received'),
    path('item_update', views.item_update, name='item-update'),
    path('item_rod_update', views.item_rod_update, name='item-rod-update'),
    path('item_add', views.item_add, name='item-add'),
    path('item_returned', views.item_returned, name='item-returned'),
    
    path('out_pending_tev', views.out_pending_tev, name='out-pending-tev'),
    path('out_checking_tev', views.out_checking_tev, name='out-checking-tev'),
    path('tev_details', views.tev_details, name='tev-details'),
    path('review_details', views.review_details, name='review-details'),

    path('checking', views.checking, name='receive-checking'),
    path('api', views.api, name='receive-api'),
    path('search_list', views.search_list, name='search-list'),
    path('upload_tev', views.upload_tev, name='upload-tev'),

    path('delete_entry', views.delete_entry, name='delete-entry'),

    
]
