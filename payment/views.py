import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone

from eduweb.models import ApplicationPayment, StaffPayroll

from .forms import (
    InvoiceGenerateForm,
    PaymentFilterForm,
    RefundForm,
)

User = get_user_model()


# ──────────────────────────────────────────────────────────────────────────────
# PERMISSION GUARD
# ──────────────────────────────────────────────────────────────────────────────

def is_finance_manager(user):
    """Allow only authenticated users with the 'finance' role."""
    return (
        user.is_authenticated
        and hasattr(user, 'profile')
        and user.profile.role == 'finance'
    )


# ──────────────────────────────────────────────────────────────────────────────
# REFUND
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_finance_manager)
def refund_payment(request, payment_reference):
    """
    Process a refund for a successful payment.
    GET  → render refund form.
    POST → validate, optionally call Stripe, update record status to 'refunded'.
    """
    payment = get_object_or_404(ApplicationPayment, payment_reference=payment_reference)

    if request.method == 'GET':
        form = RefundForm(payment=payment)
        return render(request, 'finance/refund.html', {
            'payment': payment,
            'application': getattr(payment, 'application', None),
            'form': form,
        })

    # ── POST ──
    if payment.status != 'success':
        messages.error(
            request,
            f'Payment {payment_reference} cannot be refunded '
            f'(status: "{payment.get_status_display()}").',
        )
        return redirect('finance:payment_detail', payment_reference=payment_reference)

    form = RefundForm(request.POST, payment=payment)

    if form.is_valid():
        reason        = form.cleaned_data['reason']
        notes         = form.cleaned_data.get('notes', '')
        refund_amount = form.cleaned_data['refund_amount']

        # Stripe refund (only when a gateway ID is present)
        if payment.gateway_payment_id:
            try:
                import stripe
                from django.conf import settings
                stripe.api_key = settings.STRIPE_SECRET_KEY
                stripe.Refund.create(
                    payment_intent=payment.gateway_payment_id,
                    amount=int(refund_amount * 100),  # Stripe uses cents
                )
            except Exception as exc:
                messages.error(request, f'Stripe refund failed: {exc}. Record not updated.')
                return redirect('finance:payment_detail', payment_reference=payment_reference)

        payment.status = 'refunded'
        payment.failure_reason = (
            f'Refunded ${refund_amount} — Reason: {reason}'
            + (f' | Notes: {notes}' if notes else '')
            + f' | By: {request.user.username}'
            + f' | At: {timezone.now().strftime("%Y-%m-%d %H:%M")}'
        )
        payment.save(update_fields=['status', 'failure_reason'])

        messages.success(
            request,
            f'Refund of ${refund_amount} processed for {payment_reference}.',
        )
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')

    return redirect('finance:payment_detail', payment_reference=payment_reference)


# ──────────────────────────────────────────────────────────────────────────────
# TRANSACTION REPORTS
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_finance_manager)
def transaction_reports(request):
    """
    All-payments report with per-currency revenue breakdown.
    DataTables handles search/filter/sort/pagination on the client.
    """
    payments_qs = (
        ApplicationPayment.objects
        .select_related('application__user', 'application__program')
        .order_by('-created_at')
    )

    total_count      = payments_qs.count()
    successful_count = payments_qs.filter(status='success').count()
    failed_count     = payments_qs.filter(status='failed').count()
    pending_count    = payments_qs.filter(status='pending').count()

    revenue_by_currency = (
        payments_qs
        .filter(status='success')
        .values('currency')
        .annotate(total=Sum('amount'))
        .order_by('currency')
    )

    total_revenue = (
        payments_qs.filter(status='success')
        .aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    success_rate = (
        round(successful_count / total_count * 100, 2)
        if total_count > 0 else 0
    )

    return render(request, 'finance/transaction_reports.html', {
        'payments':            payments_qs,
        'total_count':         total_count,
        'successful_count':    successful_count,
        'failed_count':        failed_count,
        'pending_count':       pending_count,
        'total_revenue':       total_revenue,
        'revenue_by_currency': revenue_by_currency,
        'success_rate':        success_rate,
    })


# ──────────────────────────────────────────────────────────────────────────────
# INVOICES
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_finance_manager)
def invoice_generation(request):
    """
    Invoice selection page.
    Lists recent successful payments for PDF generation.
    """
    recent_payments = (
        ApplicationPayment.objects
        .select_related('application__user', 'application__program')
        .filter(status='success', application__isnull=False)
        .order_by('-created_at')[:50]
    )

    now = timezone.now()

    total_invoiceable = ApplicationPayment.objects.filter(status='success').count()

    this_month_count = (
        ApplicationPayment.objects
        .filter(status='success', paid_at__year=now.year, paid_at__month=now.month)
        .count()
    )

    total_value = (
        ApplicationPayment.objects
        .filter(status='success')
        .aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    return render(request, 'finance/invoice_generation.html', {
        'recent_payments':   recent_payments,
        'total_invoiceable': total_invoiceable,
        'this_month_count':  this_month_count,
        'total_value':       total_value,
    })


@login_required
@user_passes_test(is_finance_manager)
def generate_invoice_pdf(request, payment_reference):
    """Stream a PDF invoice for a successful payment."""
    try:
        from xhtml2pdf import pisa
    except ImportError:
        messages.error(request, 'PDF library not installed. Run: pip install xhtml2pdf')
        return redirect('payments:invoice_generation')

    payment = get_object_or_404(
        ApplicationPayment.objects.select_related(
            'application__user', 'application__program'
        ),
        payment_reference=payment_reference,
        status='success',
    )

    site = None
    try:
        from eduweb.models import SiteConfig
        site = SiteConfig.get()
    except Exception:
        pass

    html = render_to_string('finance/invoice.html', {
        'payment':         payment,
        'invoice_number':  f'INV-{payment.payment_reference}',
        'invoice_date':    timezone.now(),
        'company_name':    getattr(site, 'school_name', 'MIU Education'),
        'company_address': getattr(site, 'address_usa',  '123 Education Street'),
        'company_city':    '',
        'company_email':   getattr(site, 'email',         'billing@miuedu.com'),
        'company_phone':   getattr(site, 'phone_primary',  '+1 (555) 123-4567'),
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="invoice_{payment.payment_reference}.pdf"'
    )

    result = pisa.CreatePDF(html, dest=response)
    if result.err:
        messages.error(request, 'Error generating PDF invoice.')
        return redirect('payments:invoice_generation')

    return response