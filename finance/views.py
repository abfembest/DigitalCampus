from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import (
    login_required, 
    user_passes_test
)
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
import json
from django.core.paginator import Paginator

from eduweb.models import (
    ApplicationPayment, 
    Subscription, 
    SubscriptionPlan, 
    CourseApplication,
    StaffPayroll,
)

from .forms import (
    PaymentFilterForm, 
    RefundForm, 
    SubscriptionFilterForm, 
    DateRangeForm,
    InvoiceGenerateForm,
    PayrollCreateForm, PayrollFilterForm,PayrollStatusForm
)


def is_finance_manager(user):
    """Check if user is a finance manager"""
    return (
        user.is_authenticated and 
        hasattr(user, 'profile') and 
        user.profile.role == 'finance'
    )


@login_required
@user_passes_test(is_finance_manager)
def finance_dashboard(request):
    """Finance dashboard with analytics and reports"""
    
    # Get date range
    range_form = DateRangeForm(request.GET or None)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if range_form.is_valid():
        range_type = range_form.cleaned_data.get(
            'range_type', 
            'this_month'
        )
        
        if range_type == 'today':
            start_date = timezone.now().replace(
                hour=0, 
                minute=0, 
                second=0, 
                microsecond=0
            )
        elif range_type == 'yesterday':
            start_date = (
                timezone.now() - timedelta(days=1)
            ).replace(
                hour=0, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            end_date = start_date + timedelta(days=1)
        elif range_type == 'this_week':
            start_date = timezone.now() - timedelta(
                days=timezone.now().weekday()
            )
            start_date = start_date.replace(
                hour=0, 
                minute=0, 
                second=0, 
                microsecond=0
            )
        elif range_type == 'last_week':
            end_date = timezone.now() - timedelta(
                days=timezone.now().weekday()
            )
            start_date = end_date - timedelta(days=7)
        elif range_type == 'this_month':
            start_date = timezone.now().replace(
                day=1, 
                hour=0, 
                minute=0, 
                second=0, 
                microsecond=0
            )
        elif range_type == 'last_month':
            end_date = timezone.now().replace(
                day=1, 
                hour=0, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            start_date = (
                end_date - timedelta(days=1)
            ).replace(day=1)
        elif range_type == 'custom':
            if range_form.cleaned_data.get('start_date'):
                start_date = timezone.make_aware(
                    datetime.combine(
                        range_form.cleaned_data['start_date'], 
                        datetime.min.time()
                    )
                )
            if range_form.cleaned_data.get('end_date'):
                end_date = timezone.make_aware(
                    datetime.combine(
                        range_form.cleaned_data['end_date'], 
                        datetime.max.time()
                    )
                )
    
    # Filter payments by date range
    payments = ApplicationPayment.objects.filter(
        created_at__range=[start_date, end_date]
    )
    
    # Revenue metrics
    total_revenue = payments.filter(
        status='success'
    ).aggregate(
        Sum('amount')
    )['amount__sum'] or Decimal('0.00')
    
    pending_revenue = payments.filter(
        status='pending'
    ).aggregate(
        Sum('amount')
    )['amount__sum'] or Decimal('0.00')
    
    refunded_amount = payments.filter(
        status='refunded'
    ).aggregate(
        Sum('amount')
    )['amount__sum'] or Decimal('0.00')
    
    # Transaction metrics
    total_transactions = payments.count()
    successful_transactions = payments.filter(
        status='success'
    ).count()
    failed_transactions = payments.filter(
        status='failed'
    ).count()
    
    success_rate = (
        (successful_transactions / total_transactions * 100) 
        if total_transactions > 0 
        else 0
    )
    
    # Payment method breakdown
    payment_methods = payments.filter(
        status='success'
    ).values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Daily revenue for chart
    daily_revenue = []
    current_date = start_date
    while current_date <= end_date:
        day_revenue = payments.filter(
            status='success',
            created_at__date=current_date.date()
        ).aggregate(
            Sum('amount')
        )['amount__sum'] or Decimal('0.00')
        
        daily_revenue.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'revenue': float(day_revenue)
        })
        current_date += timedelta(days=1)
    
    # Top courses by revenue
    top_courses = CourseApplication.objects.filter(
        payment__status='success',
        payment__created_at__range=[start_date, end_date]
    ).values(
        'course__name'
    ).annotate(
        revenue=Sum('payment__amount'),
        applications=Count('id')
    ).order_by('-revenue')[:5]
    
    # Active subscriptions
    active_subscriptions = Subscription.objects.filter(
        status='active'
    ).count()
    
    # Subscription revenue (MRR calculation)
    active_subs = Subscription.objects.filter(
        status='active',
        start_date__range=[start_date, end_date]
    )
    subscription_revenue = sum([
        sub.plan.price for sub in active_subs
    ])
    
    # Recent transactions
    recent_transactions = payments.select_related(
        'application__user',
        'application__course'
    ).filter(
        application__isnull=False
    ).order_by('-created_at')[:10]
    
    context = {
        'range_form': range_form,
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'refunded_amount': refunded_amount,
        'total_transactions': total_transactions,
        'successful_transactions': successful_transactions,
        'failed_transactions': failed_transactions,
        'success_rate': round(success_rate, 2),
        'payment_methods': payment_methods,
        'daily_revenue': json.dumps(daily_revenue),
        'top_courses': top_courses,
        'active_subscriptions': active_subscriptions,
        'subscription_revenue': subscription_revenue,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'finance/dashboard.html', context)


@login_required
@user_passes_test(is_finance_manager)
def payment_management(request):
    """Payment management with filtering and search"""
    
    filter_form = PaymentFilterForm(request.GET or None)
    
    # Base queryset
    payments = ApplicationPayment.objects.select_related(
        'application__course', 
        'application__user'
    ).order_by('-created_at')
    
    # Apply filters
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('status'):
            payments = payments.filter(
                status=filter_form.cleaned_data['status']
            )
        
        if filter_form.cleaned_data.get('payment_method'):
            payments = payments.filter(
                payment_method=filter_form.cleaned_data['payment_method']
            )
        
        if filter_form.cleaned_data.get('date_from'):
            payments = payments.filter(
                created_at__gte=filter_form.cleaned_data['date_from']
            )
        
        if filter_form.cleaned_data.get('date_to'):
            payments = payments.filter(
                created_at__lte=filter_form.cleaned_data['date_to']
            )
        
        if filter_form.cleaned_data.get('search'):
            search_term = filter_form.cleaned_data['search']
            payments = payments.filter(
                Q(payment_reference__icontains=search_term) |
                Q(application__user__username__icontains=search_term) |
                Q(application__user__email__icontains=search_term) |
                Q(application__user__first_name__icontains=search_term) |
                Q(application__user__last_name__icontains=search_term)
            )
    
    # Stats
    total_payments = payments.count()
    completed_payments = payments.filter(
        status='success'
    ).count()
    pending_payments = payments.filter(
        status='pending'
    ).count()
    failed_payments = payments.filter(
        status='failed'
    ).count()
    total_amount = payments.filter(
        status='success'
    ).aggregate(
        Sum('amount')
    )['amount__sum'] or Decimal('0.00')
    
    context = {
        'filter_form': filter_form,
        'payments': payments,
        'total_payments': total_payments,
        'completed_payments': completed_payments,
        'pending_payments': pending_payments,
        'failed_payments': failed_payments,
        'total_amount': total_amount,
    }
    
    return render(
        request, 
        'finance/payment_management.html', 
        context
    )


@login_required
@user_passes_test(is_finance_manager)
def payment_detail(request, payment_reference):
    """View payment details using payment_reference (slug)"""
    
    payment = get_object_or_404(
        ApplicationPayment.objects.select_related(
            'application__user',
            'application__course'
        ),
        payment_reference=payment_reference
    )
    
    refund_form = RefundForm()
    
    if request.method == 'POST':
        refund_form = RefundForm(request.POST)
        
        if refund_form.is_valid() and payment.status == 'success':
            payment.status = 'refunded'
            reason = refund_form.cleaned_data['reason']
            notes = refund_form.cleaned_data.get('notes', '')
            
            payment.failure_reason = (
                f"Refunded: {reason}. {notes}"
            )
            payment.save()
            
            messages.success(
                request, 
                'Payment refunded successfully.'
            )
            return redirect(
                'finance:payment_detail', 
                payment_reference=payment.payment_reference
            )
    
    context = {
        'payment': payment,
        'refund_form': refund_form,
    }
    
    return render(
        request, 
        'finance/payment_detail.html', 
        context
    )


@login_required
@user_passes_test(is_finance_manager)
def subscription_list(request):
    """List all subscriptions with filtering"""
    
    filter_form = SubscriptionFilterForm(request.GET or None)
    
    # Base queryset
    subscriptions = Subscription.objects.select_related(
        'user',
        'plan'
    ).order_by('-start_date')
    
    # Apply filters
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('status'):
            subscriptions = subscriptions.filter(
                status=filter_form.cleaned_data['status']
            )
        
        if filter_form.cleaned_data.get('plan'):
            subscriptions = subscriptions.filter(
                plan=filter_form.cleaned_data['plan']
            )
        
        if filter_form.cleaned_data.get('search'):
            search_term = filter_form.cleaned_data['search']
            subscriptions = subscriptions.filter(
                Q(user__username__icontains=search_term) |
                Q(user__email__icontains=search_term) |
                Q(user__first_name__icontains=search_term) |
                Q(user__last_name__icontains=search_term)
            )
    
    # Stats
    total_subscriptions = subscriptions.count()
    active_subscriptions = subscriptions.filter(
        status='active'
    ).count()
    cancelled_subscriptions = subscriptions.filter(
        status='cancelled'
    ).count()
    expired_subscriptions = subscriptions.filter(
        status='expired'
    ).count()
    
    # Calculate MRR
    active_subs = subscriptions.filter(status='active')
    mrr = sum([sub.plan.price for sub in active_subs])
    
    context = {
        'filter_form': filter_form,
        'subscriptions': subscriptions,
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'cancelled_subscriptions': cancelled_subscriptions,
        'expired_subscriptions': expired_subscriptions,
        'mrr': mrr,
    }
    
    return render(
        request, 
        'finance/subscription_list.html', 
        context
    )


@login_required
@user_passes_test(is_finance_manager)
def invoice_generation(request):
    """Generate invoices for payments"""
    
    invoice_form = InvoiceGenerateForm(request.GET or None)
    
    # Get recent successful payments
    recent_payments = ApplicationPayment.objects.select_related(
        'application', 
        'application__user'
    ).filter(
        application__isnull=False,
        application__user__isnull=False
    )[:10]
    
    context = {
        'invoice_form': invoice_form,
        'recent_payments': recent_payments,
    }
    
    return render(
        request, 
        'finance/invoice_generation.html', 
        context
    )


@login_required
@user_passes_test(is_finance_manager)
def generate_invoice_pdf(request, payment_reference):
    """Generate PDF invoice using xhtml2pdf (alternative to weasyprint)"""
    
    try:
        from xhtml2pdf import pisa
    except ImportError:
        messages.error(
            request,
            'PDF generation library not installed. '
            'Please install xhtml2pdf.'
        )
        return redirect('finance:invoice_generation')
    
    payment = get_object_or_404(
        ApplicationPayment.objects.select_related(
            'application__user',
            'application__course'
        ),
        payment_reference=payment_reference,
        status='success'
    )
    
    # Prepare invoice context
    invoice_data = {
        'payment': payment,
        'invoice_number': f"INV-{payment.payment_reference}",
        'invoice_date': timezone.now(),
        'company_name': 'MIU Education',
        'company_address': '123 Education Street',
        'company_city': 'Learning City, LC 12345',
        'company_email': 'billing@miuedu.com',
        'company_phone': '+1 (555) 123-4567',
    }
    
    # Render HTML template
    html_string = render_to_string(
        'finance/invoice.html', 
        invoice_data
    )
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; '
        f'filename="invoice_{payment.payment_reference}.pdf"'
    )
    
    # Generate PDF from HTML
    pisa_status = pisa.CreatePDF(
        html_string, 
        dest=response
    )
    
    if pisa_status.err:
        messages.error(
            request,
            'Error generating PDF invoice.'
        )
        return redirect('finance:invoice_generation')
    
    return response


@login_required
@user_passes_test(is_finance_manager)
def transaction_reports(request):
    """
    Unified transaction reports view
    All filtering and exporting handled client-side via DataTables
    """
    
    # Get all payments with related data
    payments = ApplicationPayment.objects.select_related(
        'application',
        'application__user',
        'application__course'
    ).order_by('-created_at')
    
    # Calculate statistics
    total_count = payments.count()
    successful_count = payments.filter(
        Q(status='completed') | Q(status='success')
    ).count()
    
    total_revenue = payments.filter(
        Q(status='completed') | Q(status='success')
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    success_rate = (
        (successful_count / total_count * 100) 
        if total_count > 0 
        else 0
    )
    
    context = {
        'payments': payments,
        'total_count': total_count,
        'successful_count': successful_count,
        'total_revenue': total_revenue,
        'success_rate': success_rate,
    }
    
    return render(
        request, 
        'finance/transaction_reports.html', 
        context
    )

# ==================== PAYROLL VIEWS ====================

@login_required
@user_passes_test(is_finance_manager)
def payroll_management(request):
    """
    Main payroll management page
    List view with create modal
    """
    
    # Handle form submission (Create new payroll)
    if request.method == 'POST':
        form = PayrollCreateForm(
            request.POST,
            request.FILES
        )
        if form.is_valid():
            payroll = form.save(commit=False)
            payroll.created_by = request.user
            payroll.save()
            
            # Handle file attachments (1-5)
            for i in range(1, 6):
                file_key = f'attachment_file_{i}'
                name_key = f'attachment_name_{i}'
                
                file_data = request.FILES.get(file_key)
                name_data = request.POST.get(name_key, '')
                
                if file_data:
                    setattr(payroll, f'attachment_{i}', file_data)
                    if name_data:
                        setattr(
                            payroll,
                            f'attachment_{i}_name',
                            name_data
                        )
            
            payroll.save()
            
            messages.success(
                request,
                f'Payroll created successfully: '
                f'{payroll.payroll_reference}'
            )
            return redirect('finance:payroll_management')
    else:
        form = PayrollCreateForm()
    
    # Get filter parameters
    filter_form = PayrollFilterForm(request.GET or None)
    
    # Base queryset
    payrolls = StaffPayroll.objects.select_related(
        'staff',
        'created_by',
        'approved_by'
    ).order_by('-year', '-month', 'staff__username')
    
    # Apply filters
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        month = filter_form.cleaned_data.get('month')
        year = filter_form.cleaned_data.get('year')
        search = filter_form.cleaned_data.get('search')
        
        if status:
            payrolls = payrolls.filter(payment_status=status)
        
        if month:
            payrolls = payrolls.filter(month=int(month))
        
        if year:
            payrolls = payrolls.filter(year=year)
        
        if search:
            payrolls = payrolls.filter(
                Q(payroll_reference__icontains=search) |
                Q(staff__username__icontains=search) |
                Q(staff__first_name__icontains=search) |
                Q(staff__last_name__icontains=search)
            )
    
    # Pagination
    paginator = Paginator(payrolls, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_payrolls = payrolls.count()
    pending_count = payrolls.filter(
        payment_status='pending'
    ).count()
    paid_count = payrolls.filter(
        payment_status='paid'
    ).count()
    
    total_amount = payrolls.aggregate(
        total=Sum('net_salary')
    )['total'] or Decimal('0')
    
    paid_amount = payrolls.filter(
        payment_status='paid'
    ).aggregate(
        total=Sum('net_salary')
    )['total'] or Decimal('0')
    
    context = {
        'form': form,
        'filter_form': filter_form,
        'page_obj': page_obj,
        'payrolls': page_obj.object_list,
        'total_payrolls': total_payrolls,
        'pending_count': pending_count,
        'paid_count': paid_count,
        'total_amount': total_amount,
        'paid_amount': paid_amount,
    }
    
    return render(
        request,
        'finance/payroll_management.html',
        context
    )


@login_required
@user_passes_test(is_finance_manager)
def payroll_detail(request, payroll_reference):
    """
    Detail view for a specific payroll
    View and update payroll information
    """
    
    payroll = get_object_or_404(
        StaffPayroll.objects.select_related(
            'staff',
            'created_by',
            'approved_by'
        ),
        payroll_reference=payroll_reference
    )
    
    # Handle status update form
    if request.method == 'POST':
        status_form = PayrollStatusForm(
            request.POST,
            instance=payroll
        )
        if status_form.is_valid():
            updated_payroll = status_form.save(commit=False)
            
            # If marking as paid, set approval info
            if (updated_payroll.payment_status == 'paid' and
                payroll.payment_status != 'paid'):
                updated_payroll.approved_by = request.user
                updated_payroll.approved_at = timezone.now()
            
            updated_payroll.save()
            
            messages.success(
                request,
                'Payroll status updated successfully'
            )
            return redirect(
                'finance:payroll_detail',
                payroll_reference=payroll_reference
            )
    else:
        status_form = PayrollStatusForm(instance=payroll)
    
    # Get attachments
    attachments = payroll.get_attachments()
    
    context = {
        'payroll': payroll,
        'status_form': status_form,
        'attachments': attachments,
    }
    
    return render(
        request,
        'finance/payroll_detail.html',
        context
    )


@login_required
@user_passes_test(is_finance_manager)
def payroll_delete(request, payroll_reference):
    """Delete a payroll record"""
    
    payroll = get_object_or_404(
        StaffPayroll,
        payroll_reference=payroll_reference
    )
    
    # Check if can be deleted
    if not payroll.can_delete():
        messages.error(
            request,
            'Cannot delete a paid payroll record'
        )
        return redirect(
            'finance:payroll_detail',
            payroll_reference=payroll_reference
        )
    
    if request.method == 'POST':
        # Delete all attachments
        for i in range(1, 6):
            file_field = getattr(payroll, f'attachment_{i}')
            if file_field:
                file_field.delete(save=False)
        
        payroll.delete()
        
        messages.success(
            request,
            f'Payroll {payroll_reference} deleted successfully'
        )
        return redirect('finance:payroll_management')
    
    return redirect(
        'finance:payroll_detail',
        payroll_reference=payroll_reference
    )


@login_required
@user_passes_test(is_finance_manager)
def payroll_attachment_delete(
    request,
    payroll_reference,
    attachment_number
):
    """Delete a specific attachment from payroll"""
    
    payroll = get_object_or_404(
        StaffPayroll,
        payroll_reference=payroll_reference
    )
    
    if request.method == 'POST':
        if payroll.delete_attachment(attachment_number):
            messages.success(
                request,
                f'Attachment {attachment_number} deleted successfully'
            )
        else:
            messages.error(
                request,
                'Failed to delete attachment'
            )
    
    return redirect(
        'finance:payroll_detail',
        payroll_reference=payroll_reference
    )