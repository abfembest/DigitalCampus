from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from eduweb.models import (
    ApplicationPayment,
    FeePayment,
    Subscription,
    SubscriptionPlan,
    CourseApplication,
    StaffPayroll,
)
from decimal import Decimal


# ─── shared Tailwind widget classes ────────────────────────────────────────
_SELECT = (
    'w-full px-4 py-2.5 border border-gray-300 rounded-lg '
    'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white text-sm'
)
_INPUT = (
    'w-full px-4 py-2.5 border border-gray-300 rounded-lg '
    'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm'
)
_DATE = _INPUT
_TEXTAREA = (
    'w-full px-4 py-2.5 border border-gray-300 rounded-lg '
    'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm'
)


# ==================== PAYMENT FORMS ====================

class PaymentFilterForm(forms.Form):
    """Filter form for payment management (covers both ApplicationPayment & FeePayment)"""

    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Successful'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': _SELECT})
    )

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': _INPUT,
            'placeholder': 'Search by reference, name or email…',
        })
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': _DATE, 'type': 'date'})
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': _DATE, 'type': 'date'})
    )


class RefundForm(forms.Form):
    """Form for processing refunds"""

    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': _TEXTAREA,
            'rows': 3,
            'placeholder': 'Reason for refund…',
        })
    )

    refund_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': _INPUT,
            'placeholder': 'Refund amount',
            'step': '0.01',
        })
    )

    def __init__(self, *args, payment=None, **kwargs):
        super().__init__(*args, **kwargs)
        if payment:
            self.fields['refund_amount'].initial = payment.amount
            self.fields['refund_amount'].widget.attrs['max'] = float(payment.amount)


# ==================== SUBSCRIPTION FORMS ====================

class SubscriptionFilterForm(forms.Form):
    """Filter form for subscriptions"""

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
        widget=forms.Select(attrs={'class': _SELECT})
    )

    plan = forms.ModelChoiceField(
        queryset=SubscriptionPlan.objects.filter(is_active=True).order_by('display_order', 'name'),
        required=False,
        empty_label='All Plans',
        widget=forms.Select(attrs={'class': _SELECT})
    )

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': _INPUT,
            'placeholder': 'Search by user name or email…',
        })
    )


# ==================== DATE RANGE FORM ====================

class DateRangeForm(forms.Form):
    """Date range filter for the dashboard"""

    RANGE_CHOICES = [
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('custom', 'Custom Range'),
    ]

    range_type = forms.ChoiceField(
        choices=RANGE_CHOICES,
        required=False,
        initial='this_month',
        widget=forms.Select(attrs={'class': _SELECT})
    )

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': _DATE, 'type': 'date'})
    )

    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': _DATE, 'type': 'date'})
    )


# ==================== INVOICE FORMS ====================

class InvoiceGenerateForm(forms.Form):
    """Form to select a successful application payment for invoice generation"""

    payment = forms.ModelChoiceField(
        queryset=ApplicationPayment.objects.filter(
            status='success'
        ).select_related(
            'application__user',
            'application__program',
        ),
        widget=forms.Select(attrs={'class': _SELECT}),
        empty_label='Select a payment…'
    )


# ==================== PAYROLL FORMS ====================

class PayrollCreateForm(forms.ModelForm):
    """
    Form for creating payroll with integrated file uploads.
    Supports up to 5 attachments.
    """

    _file_widget = forms.FileInput(attrs={
        'class': (
            'block w-full text-sm text-gray-900 border border-gray-300 '
            'rounded-lg cursor-pointer bg-gray-50 focus:outline-none '
            'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 '
            'file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 '
            'file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 '
            'hover:file:bg-indigo-100'
        ),
        'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png',
    })

    attachment_file_1 = forms.FileField(
        required=False,
        label='Attachment 1',
        help_text='Salary slip, contract, etc.',
        widget=forms.FileInput(attrs={
            'class': (
                'block w-full text-sm text-gray-900 border border-gray-300 '
                'rounded-lg cursor-pointer bg-gray-50 focus:outline-none '
                'focus:ring-2 focus:ring-indigo-500 '
                'file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 '
                'file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 '
                'hover:file:bg-indigo-100'
            ),
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png',
        })
    )
    attachment_name_1 = forms.CharField(
        required=False, max_length=255, label='Document Name 1',
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Document name (optional)'})
    )

    attachment_file_2 = forms.FileField(
        required=False, label='Attachment 2',
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png',
        })
    )
    attachment_name_2 = forms.CharField(
        required=False, max_length=255, label='Document Name 2',
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Document name (optional)'})
    )

    attachment_file_3 = forms.FileField(
        required=False, label='Attachment 3',
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png',
        })
    )
    attachment_name_3 = forms.CharField(
        required=False, max_length=255, label='Document Name 3',
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Document name (optional)'})
    )

    attachment_file_4 = forms.FileField(
        required=False, label='Attachment 4',
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png',
        })
    )
    attachment_name_4 = forms.CharField(
        required=False, max_length=255, label='Document Name 4',
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Document name (optional)'})
    )

    attachment_file_5 = forms.FileField(
        required=False, label='Attachment 5',
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png',
        })
    )
    attachment_name_5 = forms.CharField(
        required=False, max_length=255, label='Document Name 5',
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Document name (optional)'})
    )

    class Meta:
        model = StaffPayroll
        fields = [
            'staff', 'month', 'year',
            'base_salary', 'allowances', 'bonuses',
            'tax_deduction', 'other_deductions',
            'payment_method', 'bank_name', 'account_number',
            'notes',
        ]
        widgets = {
            'staff':            forms.Select(attrs={'class': _SELECT}),
            'month':            forms.Select(attrs={'class': _SELECT}),
            'year':             forms.NumberInput(attrs={'class': _INPUT, 'placeholder': '2025', 'min': '2020', 'max': '2030'}),
            'base_salary':      forms.NumberInput(attrs={'class': _INPUT, 'placeholder': '0.00', 'step': '0.01'}),
            'allowances':       forms.NumberInput(attrs={'class': _INPUT, 'placeholder': '0.00', 'step': '0.01'}),
            'bonuses':          forms.NumberInput(attrs={'class': _INPUT, 'placeholder': '0.00', 'step': '0.01'}),
            'tax_deduction':    forms.NumberInput(attrs={'class': _INPUT, 'placeholder': '0.00', 'step': '0.01'}),
            'other_deductions': forms.NumberInput(attrs={'class': _INPUT, 'placeholder': '0.00', 'step': '0.01'}),
            'payment_method':   forms.Select(attrs={'class': _SELECT}),
            'bank_name':        forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Bank name'}),
            'account_number':   forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Account number'}),
            'notes':            forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3, 'placeholder': 'Additional notes…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['staff'].queryset = (
            self.fields['staff'].queryset
            .select_related('profile')
            .order_by('first_name', 'last_name', 'username')
        )
        self.fields['staff'].label_from_instance = (
            lambda obj: (
                f"{obj.get_full_name() or obj.username} — "
                f"{obj.profile.get_role_display()}"
                if hasattr(obj, 'profile')
                else obj.username
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        base_salary      = cleaned_data.get('base_salary', Decimal('0')) or Decimal('0')
        allowances       = cleaned_data.get('allowances', Decimal('0')) or Decimal('0')
        bonuses          = cleaned_data.get('bonuses', Decimal('0')) or Decimal('0')
        tax              = cleaned_data.get('tax_deduction', Decimal('0')) or Decimal('0')
        other_deductions = cleaned_data.get('other_deductions', Decimal('0')) or Decimal('0')

        gross = base_salary + allowances + bonuses
        net   = gross - tax - other_deductions

        if net < 0:
            raise ValidationError('Total deductions cannot exceed gross salary.')
        return cleaned_data


class PayrollFilterForm(forms.Form):
    """Filter form for payroll list"""

    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('on_hold', 'On Hold'),
    ]

    MONTH_CHOICES = [('', 'All Months')] + [(str(i), f'{i:02d}') for i in range(1, 13)]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES, required=False,
        widget=forms.Select(attrs={'class': _SELECT})
    )
    month = forms.ChoiceField(
        choices=MONTH_CHOICES, required=False,
        widget=forms.Select(attrs={'class': _SELECT})
    )
    year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': _INPUT, 'placeholder': 'Year'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': _INPUT,
            'placeholder': 'Search by staff name or reference…',
        })
    )


class PayrollStatusForm(forms.ModelForm):
    """Form for updating payroll status"""

    class Meta:
        model = StaffPayroll
        fields = ['payment_status', 'payment_date']
        widgets = {
            'payment_status': forms.Select(attrs={'class': _SELECT}),
            'payment_date':   forms.DateInput(attrs={'class': _DATE, 'type': 'date'}),
        }

class RequiredPaymentForm(forms.ModelForm):
    """
    Create / edit AllRequiredPayments records.
    Switched to ModelForm so .save() works directly and field labels
    come from the model automatically.
 
    Notes
    -----
    - `is_active` uses required=False (standard for checkboxes).
    - The 'program' hidden PK comes from the datalist combo-box in the
      template; similarly for 'course' and 'academic_session'.
    - Querysets deferred to __init__ to avoid import-time DB hits.
    """
 
    class Meta:
        from eduweb.models import AllRequiredPayments  # noqa: local import for Meta
        model  = AllRequiredPayments
        fields = [
            'purpose',
            'program',
            'course',
            'academic_session',
            'semester',
            'who_to_pay',
            'amount',
            'due_date',
            'is_active',
        ]
        widgets = {
            'purpose':          forms.TextInput(attrs={
                'class':       _INPUT,
                'placeholder': 'e.g., School Fees, Library Fees',
                'autocomplete': 'off',
                'maxlength':   '255',
            }),
            # Programme / course / session are rendered as datalist combos in
            # the template.  The form only receives the hidden PK values, so
            # we keep plain widgets here (they are never rendered by Django).
            'program':          forms.HiddenInput(),
            'course':           forms.HiddenInput(),
            'academic_session': forms.HiddenInput(),
            'semester':         forms.Select(attrs={'class': _SELECT}),
            'who_to_pay':       forms.Select(attrs={'class': _SELECT}),
            'amount':           forms.NumberInput(attrs={
                'class':       _INPUT,
                'step':        '0.01',
                'placeholder': '0.00',
                'min':         '0.01',
            }),
            'due_date':         forms.DateInput(attrs={
                'class': _DATE,
                'type':  'date',
            }),
            'is_active':        forms.CheckboxInput(),
        }
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from eduweb.models import Program, Course, AcademicSession
 
        # Limit FK choices to active records only
        self.fields['program'].queryset = (
            Program.objects.filter(is_active=True).order_by('name')
        )
        self.fields['course'].queryset = (
            Course.objects
            .filter(is_active=True)
            .select_related('program')
            .order_by('name')
        )
        self.fields['academic_session'].queryset = (
            AcademicSession.objects.order_by('-name')
        )
 
        # Make non-required fields explicitly optional
        self.fields['course'].required           = False
        self.fields['academic_session'].required = False
        self.fields['is_active'].required        = False
 
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount
 
    def clean_course(self):
        """Ensure the chosen course belongs to the chosen programme."""
        course  = self.cleaned_data.get('course')
        program = self.cleaned_data.get('program')
        if course and program and course.program_id != program.pk:
            raise forms.ValidationError(
                'The selected course does not belong to the chosen programme.'
            )
        return course
    
# ==================== PAYROLL FORM ====================
from django.contrib.auth import get_user_model
from eduweb.models import StaffPayroll
from decimal import Decimal

User = get_user_model()
 
_FILE_WIDGET_CLS = (
    'block w-full text-sm text-gray-900 border border-gray-300 '
    'rounded-lg cursor-pointer bg-gray-50 focus:outline-none '
    'focus:ring-2 focus:ring-indigo-500 '
    'file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 '
    'file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 '
    'hover:file:bg-indigo-100'
)
_ACCEPT = '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png'
 
_FIELD_CLS = (
    'w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm '
    'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
)
 
 
class PayrollForm(forms.ModelForm): 
    # ── Attachment fields (file + name pairs, 1-5) ────────────────────────────
    attachment_1      = forms.FileField(required=False, label='File 1',
        widget=forms.FileInput(attrs={'class': _FILE_WIDGET_CLS, 'accept': _ACCEPT}))
    attachment_1_name = forms.CharField(required=False, max_length=255, label='Name 1',
        widget=forms.TextInput(attrs={'class': _FIELD_CLS, 'placeholder': 'Document name'}))
 
    attachment_2      = forms.FileField(required=False, label='File 2',
        widget=forms.FileInput(attrs={'class': _FILE_WIDGET_CLS, 'accept': _ACCEPT}))
    attachment_2_name = forms.CharField(required=False, max_length=255, label='Name 2',
        widget=forms.TextInput(attrs={'class': _FIELD_CLS, 'placeholder': 'Document name'}))
 
    attachment_3      = forms.FileField(required=False, label='File 3',
        widget=forms.FileInput(attrs={'class': _FILE_WIDGET_CLS, 'accept': _ACCEPT}))
    attachment_3_name = forms.CharField(required=False, max_length=255, label='Name 3',
        widget=forms.TextInput(attrs={'class': _FIELD_CLS, 'placeholder': 'Document name'}))
 
    attachment_4      = forms.FileField(required=False, label='File 4',
        widget=forms.FileInput(attrs={'class': _FILE_WIDGET_CLS, 'accept': _ACCEPT}))
    attachment_4_name = forms.CharField(required=False, max_length=255, label='Name 4',
        widget=forms.TextInput(attrs={'class': _FIELD_CLS, 'placeholder': 'Document name'}))
 
    attachment_5      = forms.FileField(required=False, label='File 5',
        widget=forms.FileInput(attrs={'class': _FILE_WIDGET_CLS, 'accept': _ACCEPT}))
    attachment_5_name = forms.CharField(required=False, max_length=255, label='Name 5',
        widget=forms.TextInput(attrs={'class': _FIELD_CLS, 'placeholder': 'Document name'}))
 
    class Meta:
        model  = StaffPayroll
        fields = [
            'staff', 'month', 'year',
            'base_salary', 'allowances', 'bonuses',
            'tax_deduction', 'other_deductions',
            'payment_status', 'payment_method', 'payment_date',
            'bank_name', 'account_number', 'notes',
            'attachment_1', 'attachment_1_name',
            'attachment_2', 'attachment_2_name',
            'attachment_3', 'attachment_3_name',
            'attachment_4', 'attachment_4_name',
            'attachment_5', 'attachment_5_name',
        ]
        widgets = {
            # Hidden — value injected via datalist JS in template
            'staff':          forms.Select(attrs={'class': 'hidden', 'id': 'id_staff'}),
            'month':          forms.Select(attrs={'class': 'hidden', 'id': 'id_month'}),
            'year':           forms.NumberInput(attrs={'class': 'hidden', 'id': 'id_year'}),
            'payment_method': forms.Select(attrs={'class': 'hidden', 'id': 'id_payment_method'}),
            # Standard inputs
            'base_salary':      forms.NumberInput(attrs={'class': _FIELD_CLS, 'step': '0.01', 'min': '0'}),
            'allowances':       forms.NumberInput(attrs={'class': _FIELD_CLS, 'step': '0.01', 'min': '0'}),
            'bonuses':          forms.NumberInput(attrs={'class': _FIELD_CLS, 'step': '0.01', 'min': '0'}),
            'tax_deduction':    forms.NumberInput(attrs={'class': _FIELD_CLS, 'step': '0.01', 'min': '0'}),
            'other_deductions': forms.NumberInput(attrs={'class': _FIELD_CLS, 'step': '0.01', 'min': '0'}),
            'payment_status':   forms.Select(attrs={'class': _FIELD_CLS}),
            'payment_date':     forms.DateInput(attrs={'class': _FIELD_CLS, 'type': 'date'}),
            'bank_name':        forms.TextInput(attrs={'class': _FIELD_CLS}),
            'account_number':   forms.TextInput(attrs={'class': _FIELD_CLS}),
            'notes':            forms.Textarea(attrs={'class': _FIELD_CLS, 'rows': 3}),
        }
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['staff'].queryset = (
            User.objects
            .filter(profile__role__in=['instructor', 'support', 'admin', 'content_manager', 'finance'])
            .order_by('first_name', 'last_name')
        )
        self.fields['staff'].empty_label = 'Select staff member…'
        # Make non-required fields explicit
        for f in ['allowances', 'bonuses', 'tax_deduction', 'other_deductions',
                  'payment_date', 'bank_name', 'account_number', 'notes',
                  'payment_status']:
            if f in self.fields:
                self.fields[f].required = False
 
    def clean(self):
        cleaned = super().clean()
        base    = cleaned.get('base_salary') or Decimal('0')
        allow   = cleaned.get('allowances')  or Decimal('0')
        bonus   = cleaned.get('bonuses')     or Decimal('0')
        tax     = cleaned.get('tax_deduction')    or Decimal('0')
        other   = cleaned.get('other_deductions') or Decimal('0')
        net = (base + allow + bonus) - tax - other
        if net < 0:
            raise forms.ValidationError('Total deductions cannot exceed gross salary.')
        return cleaned
 
    @property
    def salary_fields(self):
        return [
            ('Base Salary',      self['base_salary'],      'Required'),
            ('Allowances',       self['allowances'],       'Housing, transport etc.'),
            ('Bonuses',          self['bonuses'],          ''),
            ('Tax Deduction',    self['tax_deduction'],    ''),
            ('Other Deductions', self['other_deductions'], 'Insurance, loans etc.'),
        ]