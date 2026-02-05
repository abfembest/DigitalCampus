from django import forms
from django.contrib.auth.models import User
from eduweb.models import ApplicationPayment, Subscription, SubscriptionPlan


class PaymentFilterForm(forms.Form):
    """Form for filtering payment records"""
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    METHOD_CHOICES = [
        ('', 'All Methods'),
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'aria-label': 'Filter by payment status'
        })
    )
    
    payment_method = forms.ChoiceField(
        choices=METHOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'aria-label': 'Filter by payment method'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'aria-label': 'Filter from date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'aria-label': 'Filter to date'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Search by reference or user...',
            'aria-label': 'Search payments'
        })
    )


class RefundForm(forms.Form):
    """Form for processing refunds"""
    REASON_CHOICES = [
        ('duplicate', 'Duplicate Payment'),
        ('fraud', 'Fraudulent Transaction'),
        ('request', 'Customer Request'),
        ('error', 'System Error'),
        ('other', 'Other'),
    ]
    
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'aria-label': 'Refund reason'
        })
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'rows': 3,
            'placeholder': 'Additional notes about the refund...',
            'aria-label': 'Refund notes'
        })
    )


class SubscriptionFilterForm(forms.Form):
    """Form for filtering subscriptions"""
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'aria-label': 'Filter by subscription status'
        })
    )
    
    plan = forms.ModelChoiceField(
        queryset=SubscriptionPlan.objects.filter(is_active=True),
        required=False,
        empty_label='All Plans',
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'aria-label': 'Filter by subscription plan'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Search by user...',
            'aria-label': 'Search subscriptions'
        })
    )


class DateRangeForm(forms.Form):
    """Form for selecting date ranges for reports"""
    RANGE_CHOICES = [
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_year', 'This Year'),
        ('custom', 'Custom Range'),
    ]
    
    range_type = forms.ChoiceField(
        choices=RANGE_CHOICES,
        initial='this_month',
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'id': 'rangeType',
            'aria-label': 'Select date range type'
        })
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'id': 'startDate',
            'aria-label': 'Start date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input rounded-lg border-gray-300 focus:ring-2 '
                     'focus:ring-primary-500 focus:border-primary-500',
            'id': 'endDate',
            'aria-label': 'End date'
        })
    )