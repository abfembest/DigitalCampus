from django import forms
from django.contrib.auth.models import User
from eduweb.models import (
    ApplicationPayment, 
    Subscription, 
    SubscriptionPlan
)


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
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm'
            )
        })
    )

    payment_method = forms.ChoiceField(
        choices=METHOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm'
            )
        })
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm'
            )
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm'
            )
        })
    )

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm'
            ),
            'placeholder': 'Search by reference or user...'
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
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm'
            ),
            'aria-label': 'Refund reason'
        })
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm resize-none'
            ),
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
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm'
            ),
            'aria-label': 'Filter by subscription status'
        })
    )
    
    plan = forms.ModelChoiceField(
        queryset=SubscriptionPlan.objects.filter(is_active=True),
        required=False,
        empty_label='All Plans',
        widget=forms.Select(attrs={
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm'
            ),
            'aria-label': 'Filter by subscription plan'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm'
            ),
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
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm'
            ),
            'id': 'rangeType',
            'aria-label': 'Select date range type'
        })
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm'
            ),
            'id': 'startDate',
            'aria-label': 'Start date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm'
            ),
            'id': 'endDate',
            'aria-label': 'End date'
        })
    )


class InvoiceGenerateForm(forms.Form):
    """
    Form for generating invoices
    Note: This form is not actually used for submission.
    The template manually creates the select dropdown to use 
    payment_reference as the value instead of payment ID.
    """
    
    include_details = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': (
                'rounded border-gray-300 text-primary-600 '
                'focus:ring-primary-500 w-4 h-4'
            ),
            'aria-label': 'Include payment details'
        })
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': (
                'w-full px-4 py-2.5 border border-gray-300 '
                'rounded-lg focus:ring-2 focus:ring-primary-500 '
                'focus:border-primary-500 bg-white text-gray-900 '
                'transition-colors text-sm resize-none'
            ),
            'rows': 3,
            'placeholder': 'Additional notes for invoice...',
            'aria-label': 'Invoice notes'
        })
    )