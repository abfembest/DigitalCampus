from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from django.core.paginator import Paginator
from django.http import JsonResponse
import json
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from django.views.decorators.http import require_POST

from eduweb.models import (
    ApplicationPayment,
    FeePayment,
    Subscription,
    CourseApplication,
    StaffPayroll,
    AllRequiredPayments,
)

from .forms import (
    SubscriptionFilterForm,
    DateRangeForm,
    PayrollCreateForm,
    PayrollFilterForm,
    PayrollStatusForm,
    PaymentFilterForm,
    RefundForm,
    RequiredPaymentForm,
    PayrollForm
)

app_name = 'finance'

def is_finance_manager(user):
    """Allow only authenticated finance-role users"""
    return (
        user.is_authenticated
        and hasattr(user, 'profile')
        and user.profile.role == 'finance'
    )


# ==================== DASHBOARD ====================

@login_required
@user_passes_test(is_finance_manager)
def finance_dashboard(request):
    """Finance dashboard — analytics and summary across all modules"""

    # ── Currency symbol from DB ──────────────────────────────────────────────
    try:
        currency_symbol = (
            ApplicationPayment.objects
            .filter(status='success')
            .values_list('currency', flat=True)
            .first() or '$'
        )
    except Exception:
        currency_symbol = '$'

    # ── Date range ──────────────────────────────────────────────────────────
    range_form = DateRangeForm(request.GET or None)
    end_date   = timezone.now()
    start_date = end_date - timedelta(days=30)

    if range_form.is_valid():
        range_type = range_form.cleaned_data.get('range_type', 'this_month')

        if range_type == 'today':
            start_date = timezone.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif range_type == 'yesterday':
            start_date = (
                timezone.now() - timedelta(days=1)
            ).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        elif range_type == 'this_week':
            start_date = (
                timezone.now() - timedelta(days=timezone.now().weekday())
            ).replace(hour=0, minute=0, second=0, microsecond=0)
        elif range_type == 'last_week':
            end_date   = (
                timezone.now() - timedelta(days=timezone.now().weekday())
            )
            start_date = end_date - timedelta(days=7)
        elif range_type == 'this_month':
            start_date = timezone.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
        elif range_type == 'last_month':
            end_date   = timezone.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            start_date = (end_date - timedelta(days=1)).replace(day=1)
        elif range_type == 'this_year':
            start_date = timezone.now().replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        elif range_type == 'custom':
            if range_form.cleaned_data.get('start_date'):
                start_date = timezone.make_aware(
                    datetime.combine(
                        range_form.cleaned_data['start_date'],
                        datetime.min.time(),
                    )
                )
            if range_form.cleaned_data.get('end_date'):
                end_date = timezone.make_aware(
                    datetime.combine(
                        range_form.cleaned_data['end_date'],
                        datetime.max.time(),
                    )
                )

    # ── Period-scoped querysets ──────────────────────────────────────────────
    app_payments = ApplicationPayment.objects.filter(
        created_at__range=[start_date, end_date]
    )
    fee_payments = FeePayment.objects.filter(
        created_at__range=[start_date, end_date]
    )

    # ── Revenue aggregations ─────────────────────────────────────────────────
    app_revenue = (
        app_payments.filter(status='success')
        .aggregate(Sum('amount'))['amount__sum']
        or Decimal('0.00')
    )
    fee_revenue = (
        fee_payments.filter(status='success')
        .aggregate(Sum('amount'))['amount__sum']
        or Decimal('0.00')
    )
    total_revenue = app_revenue + fee_revenue

    pending_revenue = (
        (
            app_payments.filter(status='pending')
            .aggregate(Sum('amount'))['amount__sum']
            or Decimal('0.00')
        ) + (
            fee_payments.filter(status='pending')
            .aggregate(Sum('amount'))['amount__sum']
            or Decimal('0.00')
        )
    )

    refunded_amount = (
        (
            app_payments.filter(status='refunded')
            .aggregate(Sum('amount'))['amount__sum']
            or Decimal('0.00')
        ) + (
            fee_payments.filter(status='refunded')
            .aggregate(Sum('amount'))['amount__sum']
            or Decimal('0.00')
        )
    )

    # ── Transaction counts ───────────────────────────────────────────────────
    total_transactions      = app_payments.count() + fee_payments.count()
    successful_transactions = (
        app_payments.filter(status='success').count()
        + fee_payments.filter(status='success').count()
    )
    failed_transactions     = (
        app_payments.filter(status='failed').count()
        + fee_payments.filter(status='failed').count()
    )
    pending_count           = (
        app_payments.filter(status='pending').count()
        + fee_payments.filter(status='pending').count()
    )

    success_rate = (
        round(successful_transactions / total_transactions * 100, 2)
        if total_transactions > 0
        else 0
    )

    # ── Payment methods breakdown (doughnut chart) ───────────────────────────
    payment_methods = (
        app_payments.filter(status='success')
        .values('payment_method')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )

    # ── Daily revenue series (line chart) ────────────────────────────────────
    daily_revenue = []
    current = start_date
    while current <= end_date:
        app_day = (
            app_payments.filter(status='success', created_at__date=current.date())
            .aggregate(Sum('amount'))['amount__sum']
            or Decimal('0.00')
        )
        fee_day = (
            fee_payments.filter(status='success', created_at__date=current.date())
            .aggregate(Sum('amount'))['amount__sum']
            or Decimal('0.00')
        )
        daily_revenue.append({
            'date':    current.strftime('%Y-%m-%d'),
            'revenue': float(app_day + fee_day),
        })
        current += timedelta(days=1)

    # ── Top programs by revenue ──────────────────────────────────────────────
    top_courses = (
        CourseApplication.objects.filter(
            payment__status='success',
            payment__created_at__range=[start_date, end_date],
        )
        .values('program__name')
        .annotate(revenue=Sum('payment__amount'), applications=Count('id'))
        .order_by('-revenue')[:5]
    )

    # ── Subscriptions ────────────────────────────────────────────────────────
    active_subscriptions = Subscription.objects.filter(status='active').count()

    active_subs = Subscription.objects.filter(
        status='active',
        start_date__range=[start_date, end_date],
    )
    subscription_revenue = sum(
        (sub.plan.price for sub in active_subs), Decimal('0.00')
    )

    # ── Today's date (used in template for overdue comparisons) ──────────────
    today = timezone.now().date()

    # ── ALL REQUIRED PAYMENTS ────────────────────────────────────────────────
    # Only fetch fields that actually exist on AllRequiredPayments:
    #   program (FK), course (FK, nullable), academic_session (FK, nullable),
    #   semester, purpose, who_to_pay, amount, due_date, created_at, is_active
    #
    # Ordered: overdue records first (due_date in the past), then upcoming by
    # due_date ascending. Only active records are shown.
    all_required_payments = (
        AllRequiredPayments.objects
        .filter(is_active=True)
        .select_related('program', 'course', 'academic_session')
        .order_by('due_date')
    )

    # Aggregate totals for the KPI card — uses the real 'amount' field only
    req_agg = all_required_payments.aggregate(
        total=Sum('amount'),
        count=Count('id'),
    )
    required_payments_total = req_agg['total'] or Decimal('0.00')
    required_payments_count = req_agg['count'] or 0

    # Count genuinely overdue records (due_date is in the past)
    overdue_required_count = all_required_payments.filter(
        due_date__lt=today
    ).count()

    # ── Recent transactions (for the summary tables) ─────────────────────────
    recent_app_payments = (
        app_payments
        .select_related('application__user', 'application__program')
        .filter(application__isnull=False)
        .order_by('-created_at')[:15]
    )
    recent_fee_payments = (
        fee_payments
        .select_related('user', 'fee__program')
        .order_by('-created_at')[:15]
    )

    context = {
        'range_form':              range_form,
        'start_date':              start_date,
        'end_date':                end_date,
        # currency
        'currency_symbol':         currency_symbol,
        # revenue
        'total_revenue':           total_revenue,
        'app_revenue':             app_revenue,
        'fee_revenue':             fee_revenue,
        'pending_revenue':         pending_revenue,
        'refunded_amount':         refunded_amount,
        # transaction counts
        'total_transactions':      total_transactions,
        'successful_transactions': successful_transactions,
        'failed_transactions':     failed_transactions,
        'pending_count':           pending_count,
        'success_rate':            success_rate,
        # charts
        'payment_methods':         payment_methods,
        'daily_revenue':           json.dumps(daily_revenue),
        # required / pending payments
        'all_required_payments':   all_required_payments,
        'required_payments_total': required_payments_total,
        'required_payments_count': required_payments_count,
        'overdue_required_count':  overdue_required_count,
        # today — used in template to detect overdue rows without a model property
        'today':                   today,
        # lists / tables
        'top_courses':             top_courses,
        'active_subscriptions':    active_subscriptions,
        'subscription_revenue':    subscription_revenue,
        'recent_app_payments':     recent_app_payments,
        'recent_fee_payments':     recent_fee_payments,
    }

    return render(request, 'finance/dashboard.html', context)


# ==================== PAYMENT MANAGEMENT ====================
 
@login_required
@user_passes_test(is_finance_manager)
def payment_management(request):
    """List all ApplicationPayment and FeePayment records with filtering."""
 
    filter_form = PaymentFilterForm(request.GET or None)
 
    # ── Base querysets ────────────────────────────────────────────────────
    # ApplicationPayment:
    #   - application (OneToOne → CourseApplication)
    #     CourseApplication has: first_name, last_name, email, program (FK), get_full_name()
    #   - amount, currency, status, payment_method, payment_reference, created_at, paid_at
    app_payments = ApplicationPayment.objects.select_related(
        'application',
        'application__program',
        'application__program__department',
    ).order_by('-created_at')
 
    # FeePayment:
    #   - user (FK → User)
    #   - fee (FK → AllRequiredPayments: purpose, amount, program, academic_session, semester)
    #   - amount, currency, status, payment_method, payment_reference, created_at, paid_at
    fee_payments = FeePayment.objects.select_related(
        'user',
        'user__profile',
        'fee',
        'fee__program',
        'fee__academic_session',
    ).order_by('-created_at')
 
    # ── Apply filters ─────────────────────────────────────────────────────
    if filter_form.is_valid():
        cd = filter_form.cleaned_data
 
        if cd.get('status'):
            app_payments = app_payments.filter(status=cd['status'])
            fee_payments = fee_payments.filter(status=cd['status'])
 
        if cd.get('search'):
            term = cd['search']
            # ApplicationPayment: search by reference OR applicant name/email
            # (first_name, last_name, email are direct fields on CourseApplication)
            app_payments = app_payments.filter(
                Q(payment_reference__icontains=term)
                | Q(application__first_name__icontains=term)
                | Q(application__last_name__icontains=term)
                | Q(application__email__icontains=term)
            )
            # FeePayment: search by reference OR user name/email (Django User fields)
            fee_payments = fee_payments.filter(
                Q(payment_reference__icontains=term)
                | Q(user__first_name__icontains=term)
                | Q(user__last_name__icontains=term)
                | Q(user__email__icontains=term)
                | Q(fee__purpose__icontains=term)
            )
 
        if cd.get('date_from'):
            app_payments = app_payments.filter(created_at__date__gte=cd['date_from'])
            fee_payments = fee_payments.filter(created_at__date__gte=cd['date_from'])
 
        if cd.get('date_to'):
            app_payments = app_payments.filter(created_at__date__lte=cd['date_to'])
            fee_payments = fee_payments.filter(created_at__date__lte=cd['date_to'])
 
    # ── Summary stats (unfiltered totals for the KPI cards) ──────────────
    total_app = ApplicationPayment.objects.count()
    total_fee = FeePayment.objects.count()
 
    success_app = ApplicationPayment.objects.filter(status='success').aggregate(
        count=Count('id'), total=Sum('amount')
    )
    success_fee = FeePayment.objects.filter(status='success').aggregate(
        count=Count('id'), total=Sum('amount')
    )
 
    pending_count = (
        ApplicationPayment.objects.filter(status='pending').count()
        + FeePayment.objects.filter(status='pending').count()
    )
    refunded_count = (
        ApplicationPayment.objects.filter(status='refunded').count()
        + FeePayment.objects.filter(status='refunded').count()
    )
 
    total_revenue = (
        (success_app['total'] or Decimal('0'))
        + (success_fee['total'] or Decimal('0'))
    )
 
    # ── Currency: read from first successful payment record ───────────────
    # Prefer ApplicationPayment first, fall back to FeePayment, then default '$'
    currency_symbol = (
        ApplicationPayment.objects
        .filter(status='success')
        .values_list('currency', flat=True)
        .first()
        or FeePayment.objects
        .filter(status='success')
        .values_list('currency', flat=True)
        .first()
        or 'USD'
    )
 
    # ── Paginate each table independently ────────────────────────────────
    app_paginator = Paginator(app_payments, 15)
    fee_paginator = Paginator(fee_payments, 15)
 
    app_page = app_paginator.get_page(request.GET.get('app_page'))
    fee_page = fee_paginator.get_page(request.GET.get('fee_page'))
 
    context = {
        'filter_form':       filter_form,
        'app_page':          app_page,
        'fee_page':          fee_page,
        # KPI cards
        'total_payments':    total_app + total_fee,
        'total_app_payments': total_app,
        'total_fee_payments': total_fee,
        'total_revenue':     total_revenue,
        'pending_count':     pending_count,
        'refunded_count':    refunded_count,
        'success_count':     (success_app['count'] or 0) + (success_fee['count'] or 0),
        # currency — dynamic from DB, NOT hardcoded
        'currency_symbol':   currency_symbol,
    }
 
    return render(request, 'finance/payment_management.html', context)
 
@login_required
@user_passes_test(is_finance_manager)
def payment_detail(request, payment_reference):
    payment      = None
    payment_type = None
 
    # ── Lookup: try ApplicationPayment first, then FeePayment ────────────────
    try:
        payment = (
            ApplicationPayment.objects
            .select_related('application__user', 'application__program')
            .get(payment_reference=payment_reference)
        )
        payment_type = 'application'
    except ApplicationPayment.DoesNotExist:
        payment = get_object_or_404(
            FeePayment.objects.select_related('user', 'fee__program', 'fee__academic_session'),
            payment_reference=payment_reference,
        )
        payment_type = 'fee'
 
    can_refund = payment.status == 'success'
 
    # ── POST — process refund ─────────────────────────────────────────────────
    if request.method == 'POST' and request.POST.get('action') == 'refund':
        form = RefundForm(request.POST, payment=payment)
        if form.is_valid():
            cd             = form.cleaned_data
            refund_amount  = cd['refund_amount']
            reason         = cd['reason']
 
            if refund_amount > payment.amount:
                messages.error(request, 'Refund amount cannot exceed the original payment.')
            elif not can_refund:
                messages.error(request, 'This payment cannot be refunded.')
            else:
                payment.status = 'refunded'
                # Store reason in failure_reason field (re-used for audit trail)
                payment.failure_reason = f'Refund ({refund_amount}): {reason}'
                payment.save(update_fields=['status', 'failure_reason'])
                messages.success(
                    request,
                    f'Refund of ${refund_amount} processed for {payment_reference}.',
                )
                return redirect('finance:payment_detail', payment_reference=payment_reference)
    else:
        form = RefundForm(payment=payment)
 
    context = {
        'payment':      payment,
        'payment_type': payment_type,
        'form':         form,
        'can_refund':   can_refund,
    }
    return render(request, 'finance/payment_detail.html', context)


# ==================== SUBSCRIPTIONS ====================

@login_required
@user_passes_test(is_finance_manager)
def subscription_list(request):
    """List all subscriptions with filtering"""

    filter_form = SubscriptionFilterForm(request.GET or None)

    subscriptions = Subscription.objects.select_related(
        'user', 'plan'
    ).order_by('-start_date')

    if filter_form.is_valid():
        cd = filter_form.cleaned_data

        if cd.get('status'):
            subscriptions = subscriptions.filter(status=cd['status'])

        if cd.get('plan'):
            subscriptions = subscriptions.filter(plan=cd['plan'])

        if cd.get('search'):
            term = cd['search']
            subscriptions = subscriptions.filter(
                Q(user__username__icontains=term)
                | Q(user__email__icontains=term)
                | Q(user__first_name__icontains=term)
                | Q(user__last_name__icontains=term)
            )

    active_subs = subscriptions.filter(status='active')
    mrr = sum(sub.plan.price for sub in active_subs)

    context = {
        'filter_form': filter_form,
        'subscriptions': subscriptions,
        'total_subscriptions': subscriptions.count(),
        'active_subscriptions': active_subs.count(),
        'cancelled_subscriptions': subscriptions.filter(
            status='cancelled'
        ).count(),
        'expired_subscriptions': subscriptions.filter(
            status='expired'
        ).count(),
        'mrr': mrr,
    }

    return render(request, 'finance/subscription_list.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# PAYROLL — helpers
# ──────────────────────────────────────────────────────────────────────────────

def _payroll_stats(qs):
    """Return aggregate summary dict for a StaffPayroll queryset."""
    agg = qs.aggregate(
        total_amount=Sum('gross_salary'),
        paid_amount=Sum('net_salary'),
        total_tax=Sum('tax_deduction'),
        total_other=Sum('other_deductions'),
    )
    total_deductions = (
        (agg['total_tax'] or Decimal('0.00')) +
        (agg['total_other'] or Decimal('0.00'))
    )
    return {
        'total_amount':    agg['total_amount'] or Decimal('0.00'),
        'paid_amount':     agg['paid_amount'] or Decimal('0.00'),
        'total_deductions': total_deductions,
    }

def _available_years():
    current = timezone.now().year
    return list(range(current + 1, 2019, -1))

@login_required
@user_passes_test(is_finance_manager)
def payroll_management(request):
    if request.method == 'POST':
        form = PayrollForm(request.POST, request.FILES)
        if form.is_valid():
            payroll = form.save(commit=False)
            payroll.created_by = request.user
            payroll.save()
            messages.success(request, f'Payroll record {payroll.payroll_reference} created successfully.')
            return redirect('finance:payroll_management')
    else:
        form = PayrollForm()

    payrolls = StaffPayroll.objects.select_related('staff__profile').order_by('-year', '-month')
    stats = _payroll_stats(payrolls)

    return render(request, 'finance/payroll_management.html', {
        'payrolls': payrolls,
        'form': form,
        'available_years': _available_years(),
        'total_payrolls': payrolls.count(),
        **stats,
    })

@login_required
@user_passes_test(is_finance_manager)
def payroll_detail(request, payroll_reference):
    payroll = get_object_or_404(
        StaffPayroll.objects.select_related('staff__profile', 'created_by'),
        payroll_reference=payroll_reference
    )

    if request.method == 'POST':
        form = PayrollForm(request.POST, request.FILES, instance=payroll)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payroll record updated successfully.')
            return redirect('finance:payroll_detail', payroll_reference=payroll_reference)
    else:
        form = PayrollForm(instance=payroll)

    return render(request, 'finance/payroll_detail.html', {
        'payroll': payroll,
        'form': form,
        'available_years': _available_years(),
        'attachments': payroll.get_attachments(),
    })


# ──────────────────────────────────────────────────────────────────────────────
# PAYROLL — delete
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_finance_manager)
def payroll_delete(request, payroll_reference):
    """
    Delete a payroll record.
    POST only — paid records are protected and cannot be deleted.
    GET requests are silently redirected to the detail page.
    """
    payroll = get_object_or_404(StaffPayroll, payroll_reference=payroll_reference)

    if not payroll.can_delete():
        messages.error(
            request,
            f'Cannot delete {payroll_reference} — status is "Paid".',
        )
        return redirect('finance:payroll_detail', payroll_reference=payroll_reference)

    if request.method == 'POST':
        payroll.delete()
        messages.success(request, f'Payroll record {payroll_reference} deleted.')
        return redirect('finance:payroll_management')

    # Redirect stray GET requests back to detail
    return redirect('finance:payroll_detail', payroll_reference=payroll_reference)


# ──────────────────────────────────────────────────────────────────────────────
# PAYROLL — attachment delete
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_finance_manager)
def payroll_attachment_delete(request, payroll_reference, attachment_number):
    """
    Delete one numbered attachment (1–5) from a payroll record.
    POST only — GET requests redirect back to detail.
    """
    payroll = get_object_or_404(StaffPayroll, payroll_reference=payroll_reference)

    if request.method == 'POST':
        if 1 <= attachment_number <= 5:
            payroll.delete_attachment(attachment_number)
            messages.success(
                request,
                f'Attachment {attachment_number} removed from {payroll_reference}.',
            )
        else:
            messages.error(request, 'Invalid attachment number.')

    return redirect('finance:payroll_detail', payroll_reference=payroll_reference)

@login_required
@user_passes_test(is_finance_manager)
def required_payments_list(request):
    """
    Single-page management for AllRequiredPayments.
    DataTables handles all client-side filtering, sorting and pagination.
    """
    from eduweb.models import Program, Course, AcademicSession
 
    today = timezone.now().date()
 
    payments = (
        AllRequiredPayments.objects
        .select_related('program', 'course', 'academic_session')
        .order_by('due_date')
    )
 
    # Aggregate KPI counts in a single pass
    total_count   = payments.count()
    active_qs     = payments.filter(is_active=True)
    active_count  = active_qs.count()
    overdue_count = active_qs.filter(due_date__lt=today).count()
    total_value   = active_qs.aggregate(v=Sum('amount'))['v'] or Decimal('0.00')
 
    # Distinct existing purposes for datalist autocomplete (max 50)
    suggestions = (
        AllRequiredPayments.objects
        .order_by('purpose')
        .values_list('purpose', flat=True)
        .distinct()[:50]
    )
 
    context = {
        'payments':      payments,
        # all_programs and all_sessions are used by the modal datalists
        'all_programs':  Program.objects.filter(is_active=True).order_by('name'),
        # Include program FK so JS can assign data-program-pk per course option
        'all_courses': (
            Course.objects
            .filter(is_active=True)
            .select_related('program')
            .order_by('name')
        ),
        'all_sessions':  AcademicSession.objects.order_by('-name'),
        'suggestions':   suggestions,
        'today':         today,
        'total_count':   total_count,
        'active_count':  active_count,
        'overdue_count': overdue_count,
        'total_value':   total_value,
    }
    return render(request, 'finance/required_payments.html', context)
 
 
@login_required
@user_passes_test(is_finance_manager)
def required_payment_create(request):
    """Create a new AllRequiredPayments record (modal POST)."""
    if request.method == 'POST':
        form = RequiredPaymentForm(request.POST)
        if form.is_valid():
            form.save()
            cd = form.cleaned_data
            messages.success(request, f'Required payment "{cd["purpose"]}" created.')
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    label = form.fields[field].label or field
                    messages.error(request, f'{label}: {err}')
    return redirect('finance:required_payments_list')
 
 
@login_required
@user_passes_test(is_finance_manager)
def required_payment_update(request, pk):
    """Update an existing AllRequiredPayments record (modal POST)."""
    payment = get_object_or_404(AllRequiredPayments, pk=pk)
    if request.method == 'POST':
        form = RequiredPaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Payment "{payment.purpose}" updated.')
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    label = form.fields[field].label or field
                    messages.error(request, f'{label}: {err}')
    return redirect('finance:required_payments_list')
 
 
@login_required
@user_passes_test(is_finance_manager)
@require_POST                          # ← security: reject GET/HEAD silently
def required_payment_delete(request, pk):
    """Delete an AllRequiredPayments record (POST only)."""
    payment = get_object_or_404(AllRequiredPayments, pk=pk)
    name = payment.purpose
    payment.delete()
    messages.success(request, f'Payment "{name}" deleted.')
    return redirect('finance:required_payments_list')
 
 
@login_required
@user_passes_test(is_finance_manager)
@require_POST
def required_payment_toggle(request, pk):
    """Toggle is_active on an AllRequiredPayments record (POST only)."""
    payment = get_object_or_404(AllRequiredPayments, pk=pk)
    payment.is_active = not payment.is_active
    payment.save(update_fields=['is_active'])
    state = 'activated' if payment.is_active else 'deactivated'
    messages.success(request, f'Payment "{payment.purpose}" {state}.')
    return redirect('finance:required_payments_list')