from django.urls import path

from . import views

urlpatterns = [
    path('create-company/', views.create_company, name='create_company'),
    path('create-receipt/<str:company_name>/', views.create_receipt, name='create_receipt'),
    path('create-payment/<str:company_name>/', views.create_payment, name='create_payment'),
    path('create-big-receipt/<str:company_name>/', views.create_big_receipt, name='create_big_receipt'),
    path('create-big-payment/<str:company_name>/', views.create_big_payment, name='create_big_payment'),
    path('create-category/', views.create_category, name='create_category'),
    path('create-subcategory/', views.create_subcategory, name='create_subcategory'),
    path('edit-category/<int:id>/', views.edit_category, name='edit_category'),
    path('edit-subcategory/<int:id>/', views.edit_subcategory, name='edit_subcategory'),
    path('delete-category/<int:id>/', views.delete_category, name='delete_category'),
    path('delete-subcategory/<int:id>/', views.delete_subcategory, name='delete_subcategory'),
    path('receipt-template-download/', views.receipt_template_download, name='receipt_template_download'),
    path('payment-template-downlaod/',  views.payment_template_download, name='payment_template_download'),
    path('receipt-excel-upload/', views.receipt_excel_upload, name='receipt_excel_upload'),
    path('payment-excel-upload/', views.payment_excel_upload, name='payment_excel_upload'),
    path('edit-company/<int:id>/', views.edit_company, name='edit_company'),
    path('edit-receipt/<int:id>/', views.edit_receipt, name='edit_receipt'),
    path('edit-payment/<int:id>/', views.edit_payment, name='edit_payment'),
    path('resubmit-entry/<int:id>/', views.resubmit_entry, name='resubmit_entry'),
    path('delete-entry/<int:id>/', views.delete_entry, name='delete_entry'),
    path('delete-company/<int:id>', views.delete_company, name='delete_company'),
    path('reject-entry/<int:id>/', views.reject_entry, name='reject_entry'),
    path('reject-irregular-entry/<int:id>/', views.reject_irregular_entry, name='reject_irregular_entry'),
    path('approve-irregular-entry/<int:id>/', views.approve_irregular_entry, name='approve_irregular_entry'),
    path('approve-entry/<int:id>/', views.approve_entry, name='approve_entry'),
    path('manager-request-edit/<int:id>/', views.manager_request_edit, name='manager_request_edit'),
    path('approve-manager-review/<int:id>/', views.approve_manager_review, name='approve_manager_review'),
    path('reject-manager-review/<int:id>/', views.reject_manager_review, name='reject_manager_review'),

    #AJAX
    path('filter-approved-entries/', views.filter_approved_entries, name='manager_approved_entries'),
    path('filter-pending-entries/', views.filter_pending_entries, name='filter_pending_entries'),
    path('filter-pending-entries-manager/', views.filter_pending_entries_manager, name='filter_pending_entries_manager'),
    path('filter-rejected-entries/', views.filter_rejected_entries, name='filter_rejected_entries'),
    path('filter-irregular-entries/', views.filter_irregular_entries, name='filter_irregular_entries'),
    path('filter-manager-entries/', views.filter_manager_entries, name='filter_manager_entries'),
    path('filter-entries-admin/', views.filter_entries_admin, name='filter_entries_admin'),
    path('load-subcategories/', views.load_subcategories, name='load_subcategories')



]


