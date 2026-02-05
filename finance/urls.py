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
    path(
        'payments/<int:payment_id>/', 
        views.payment_detail, 
        name='payment_detail'
    ),
    
    # Subscription Management
    path(
        'subscriptions/', 
        views.subscription_list, 
        name='subscription_list'
    ),
]