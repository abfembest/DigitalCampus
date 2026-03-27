from django.urls import path, include
from . import views

app_name = 'finance'

urlpatterns = [

    # Dashboard
    path('', views.finance_dashboard, name='dashboard'),

    # Payments — list
    path('payments/', views.payment_management, name='payment_management'),

    path(
        'payments/<str:payment_reference>/',
        views.payment_detail,
        name='payment_detail',
    ),

    # Subscriptions
    path(
        'subscriptions/',
        views.subscription_list,
        name='subscription_list',
    ),

    # Payroll
    path('payroll/', views.payroll_management, name='payroll_management'),
    path(
        'payroll/<str:payroll_reference>/',
        views.payroll_detail,
        name='payroll_detail',
    ),
    path(
        'payroll/<str:payroll_reference>/delete/',
        views.payroll_delete,
        name='payroll_delete',
    ),
    path(
        'payroll/<str:payroll_reference>/attachment/'
        '<int:attachment_number>/delete/',
        views.payroll_attachment_delete,
        name='payroll_attachment_delete',
    ),

    path(
        'required-payments/',
        views.required_payments_list,
        name='required_payments_list',
    ),
    path(
        'required-payments/create/',
        views.required_payment_create,
        name='required_payment_create',
    ),
    path(
        'required-payments/<int:pk>/update/',
        views.required_payment_update,
        name='required_payment_update',
    ),
    path(
        'required-payments/<int:pk>/delete/',
        views.required_payment_delete,
        name='required_payment_delete',
    ),
    path(
        'required-payments/<int:pk>/toggle/',
        views.required_payment_toggle,
        name='required_payment_toggle',
    ),
]