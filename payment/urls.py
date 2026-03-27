from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [

    # ── Static / named paths FIRST — must come before the catch-all ──────────

    # Transaction reports
    path(
        'reports/transactions/',
        views.transaction_reports,
        name='transaction_reports',
    ),

    # Invoice list page
    path(
        'invoices/',
        views.invoice_generation,
        name='invoice_generation',
    ),

    # Invoice PDF download
    path(
        'invoices/<str:payment_reference>/pdf/',
        views.generate_invoice_pdf,
        name='generate_invoice_pdf',
    ),

    path(
        '<str:payment_reference>/refund/',
        views.refund_payment,
        name='refund_payment',
    ),
]