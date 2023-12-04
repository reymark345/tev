from django.urls import path

from . import views

urlpatterns = [

    path('division', views.division, name='division'),
    path('division_load', views.division_load, name='division-load'),  
    path('division_add', views.division_add, name='division-add'),
    path('division_update', views.division_update, name='division-update'),
    path('division_edit', views.division_edit, name='division-edit'),
    
    path('charges', views.charges, name='charges'),
    path('charges_load', views.charges_load, name='charges-load'),  
    path('charges_add', views.charges_add, name='charges-add'),
    path('charges_update', views.charges_update, name='charges-update'),
    path('charges_edit', views.charges_edit, name='charges-edit'),

    path('remarks', views.remarks, name='remarks'),
    path('remarks_load', views.remarks_load, name='remarks-load'),  
    path('remarks_add', views.remarks_add, name='remarks-add'),
    path('remarks_update', views.remarks_update, name='remarks-update'),
    path('remarks_edit', views.remarks_edit, name='remarks-edit'),
]
