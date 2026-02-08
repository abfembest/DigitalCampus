from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Dashboard
    path(
        '', 
        views.finance_dashboard, 
        name='dashboard'
    ),
    
    # Payment Management
    path(
        'payments/', 
        views.payment_management, 
        name='payment_management'
    ),
    
    # Payment Detail - Using payment_reference (slug)
    path(
        'payments/<str:payment_reference>/', 
        views.payment_detail, 
        name='payment_detail'
    ),
    
    # Subscription Management
    path(
        'subscriptions/', 
        views.subscription_list, 
        name='subscription_list'
    ),

    # Invoice Generation
    path(
        'invoices/', 
        views.invoice_generation, 
        name='invoice_generation'
    ),
    path(
        'invoices/generate/<str:payment_reference>/', 
        views.generate_invoice_pdf, 
        name='generate_invoice_pdf'
    ),
    
    path(
        'reports/transactions/', 
        views.transaction_reports, 
        name='transaction_reports'
    ),
]