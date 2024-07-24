from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.initial_register, name='register'),
    path('create-user/', views.create_user, name='create_user'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin_dash/', views.admin_dash, name='admin_dash'),
    path('manager_dash/', views.manager_dash, name='manager_dash'),
    path('accountant_dash/', views.accountant_dash, name='accountant_dash'),
    path('edit-user/<int:id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:id>/', views.delete_user, name='delete_user'),

    #AJAX
    path('filter-accountants/<int:id>/', views.filter_accountants, name='filter_accountants'),
    path('all-accountants/', views.all_accountants, name='all_accountants')
    
]