from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from simple_history.models import HistoricalRecords
from django.db.models import Sum
from django.utils import timezone


class BusinessInfo(models.Model):
    """Business information for invoices"""
    name = models.CharField(max_length=200, default='New Balance Immigration')
    address_line1 = models.CharField(max_length=200, default='Unit-08')
    address_line2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100, default='Mississauga')
    province = models.CharField(max_length=100, default='Ontario')
    postal_code = models.CharField(max_length=20, default='L5S 1T7')
    country = models.CharField(max_length=100, default='Canada')
    phone = models.CharField(max_length=20, default='9054629000')
    mobile = models.CharField(max_length=20, default='6476126722')
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True, default='www.newbalanceimmigration.com')
    logo = models.ImageField(upload_to='business/logo/', blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    # Invoice Settings
    default_due_days = models.IntegerField(default=30, help_text="Default number of days until invoice is due")
    default_footer = models.TextField(blank=True, null=True, help_text="Default footer text for invoices")
    default_notes_terms = models.TextField(blank=True, null=True, help_text="Default notes/terms for invoices")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Business Info'
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_current(cls):
        """Get the current business info, create if doesn't exist"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class TaxSlab(models.Model):
    """Tax slabs for invoices"""
    name = models.CharField(max_length=100, help_text="Tax name (e.g., GST, HST, PST)")
    rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], help_text="Tax rate percentage")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Default tax to use for new invoices")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.rate}%)"


class EmailTemplate(models.Model):
    """Email templates for invoices"""
    TEMPLATE_TYPE_CHOICES = [
        ('invoice_sent', 'Invoice Sent'),
        ('invoice_reminder', 'Invoice Reminder'),
        ('payment_received', 'Payment Received'),
    ]
    
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPE_CHOICES, unique=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.get_template_type_display()


class Account(models.Model):
    """Chart of Accounts"""
    ACCOUNT_TYPE_CHOICES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]
    
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    account_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    parent_account = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='sub_accounts')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['account_number', 'name']
    
    def __str__(self):
        return f"{self.account_number} - {self.name}" if self.account_number else self.name
    
    def get_balance(self):
        """Calculate account balance"""
        balance = Decimal('0.00')
        transactions = Transaction.objects.filter(account=self)
        for transaction in transactions:
            if transaction.transaction_type == 'deposit':
                balance += transaction.amount
            else:
                balance -= transaction.amount
        return balance


# Customer and ProductService models removed - using rio.Applicant and rio.Services directly


class Invoice(models.Model):
    """Invoices"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True)
    applicant = models.ForeignKey('rio.Applicant', on_delete=models.CASCADE, related_name='invoices')
    invoice_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    title = models.CharField(max_length=200, blank=True, null=True, default='Invoice')
    summary = models.TextField(blank=True, null=True, help_text="e.g. project name, description of invoice")
    po_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="P.O./S.O. number")
    # Invoice-level tax rate (percentage). In combination with per-line tax flags
    # this allows taxing only specific items (e.g. application fee) rather than
    # the whole subtotal.
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    footer = models.TextField(blank=True, null=True, help_text="e.g. tax information, thank you note")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invoices_created')
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-invoice_date', '-invoice_number']
    
    def __str__(self):
        applicant_name = f"{self.applicant.f_name or ''} {self.applicant.l_name or ''}".strip() or self.applicant.client_id
        return f"Invoice {self.invoice_number} - {applicant_name}"
  

    def get_paid_amount(self):
        """Get total amount paid for this invoice"""

        total = self.payments.aggregate(
            total_paid=Sum('amount')
        )['total_paid']

        return total or Decimal('0.00')


    def get_balance(self):
        """Get outstanding balance"""

        balance = self.total_amount - self.get_paid_amount()

        return balance if balance > 0 else Decimal('0.00')
    
    def calculate_totals(self):
        """
        Calculate invoice totals from line items.

        Business rules:
        - Subtotal is the sum of all line totals.
        - Discount is applied BEFORE tax and cannot exceed the subtotal.
        - Tax is applied ONLY on taxable line items (e.g. application fee or
          custom items explicitly marked taxable), not on biometric fees,
          client retained amounts, or other non-taxable items.
        """
        items = self.items.all()

        # Subtotal across all items
        self.subtotal = sum(item.line_total for item in items)

        # Normalise discount
        if self.discount_amount is None or self.discount_amount < 0:
            self.discount_amount = Decimal('0.00')

        if self.discount_amount > self.subtotal:
            self.discount_amount = self.subtotal

        # Effective discount ratio applied across all items
        discount_base = self.subtotal if self.subtotal > 0 else Decimal('0.00')
        if discount_base > 0:
            discount_ratio = (self.discount_amount / discount_base).quantize(
                Decimal('0.0001')
            )
        else:
            discount_ratio = Decimal('0.00')

        # Taxable amount is the discounted total of taxable line items only
        taxable_total_before_discount = sum(
            item.line_total for item in items if getattr(item, "is_taxable", False)
        )

        taxable_base = taxable_total_before_discount * (Decimal('1.00') - discount_ratio)
        if taxable_base < 0:
            taxable_base = Decimal('0.00')

        # Calculate tax based on discounted taxable base and invoice-level tax rate
        if self.tax_rate and self.tax_rate > 0 and taxable_base > 0:
            self.tax_amount = (taxable_base * self.tax_rate) / Decimal('100.00')
        else:
            self.tax_amount = Decimal('0.00')

        # Total = discounted subtotal + tax
        discounted_subtotal = self.subtotal - self.discount_amount
        if discounted_subtotal < 0:
            discounted_subtotal = Decimal('0.00')

        self.total_amount = discounted_subtotal + self.tax_amount
        self.save()
    
    

    def update_status(self):
        """Automatically update invoice status"""

        if self.status == 'cancelled':
            return

        paid_amount = self.get_paid_amount()
        balance = self.get_balance()

        # Fully paid
        if balance <= Decimal('0.00'):
            self.status = 'paid'

        # Partial payment
        elif paid_amount > Decimal('0.00'):
            self.status = 'partial'

        # Overdue
        elif timezone.now().date() > self.due_date:
            self.status = 'overdue'

        # Default
        else:
            self.status = 'sent'

        self.save(update_fields=['status'])


class InvoiceItem(models.Model):
    """Invoice Line Items"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey('rio.Services', on_delete=models.CASCADE, related_name='invoice_items', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'), validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    # Line-level tax rate is kept for future extensibility but tax is normally
    # driven by invoice-level tax_rate plus this is_taxable flag.
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    # Whether this line should be included in the taxable base when computing
    # invoice tax. Application fee lines will typically be taxable; biometric
    # and client-retained lines will not, and custom items can opt-in.
    is_taxable = models.BooleanField(default=False)
    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        service_name = self.service.name if self.service else "Custom Item"
        return f"{service_name} - {self.invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
        """Calculate line total on save"""
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Recalculate invoice totals
        self.invoice.calculate_totals()


class Payment(models.Model):
    """Payments received for invoices"""

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('other', 'Other'),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments',
        blank=True,
        null=True
    )

    applicant = models.ForeignKey(
        'rio.Applicant',
        on_delete=models.CASCADE,
        related_name='accounting_payments'
    )

    payment_date = models.DateField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash'
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    notes = models.TextField(blank=True, null=True)

    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments_created'
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ['-payment_date', '-id']

    def __str__(self):
        applicant_name = (
            f"{self.applicant.f_name or ''} "
            f"{self.applicant.l_name or ''}"
        ).strip() or self.applicant.client_id

        return f"Payment {self.amount} - {applicant_name}"

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        # Auto update invoice status
        if self.invoice:
            self.invoice.update_status()


class Transaction(models.Model):
    """Financial Transactions (Deposits and Withdrawals)"""
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
    ]
    
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.TextField()
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    category = models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True, related_name='transaction_categories')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='transactions_created')
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-transaction_date', '-id']
    
    def __str__(self):
        return f"{self.transaction_type.title()} - {self.amount} - {self.account.name}"


class Expense(models.Model):
    """Expense tracking"""
    EXPENSE_CATEGORY_CHOICES = [
        ('office_supplies', 'Office Supplies'),
        ('utilities', 'Utilities'),
        ('rent', 'Rent'),
        ('salaries', 'Salaries'),
        ('marketing', 'Marketing'),
        ('travel', 'Travel'),
        ('professional_services', 'Professional Services'),
        ('insurance', 'Insurance'),
        ('taxes', 'Taxes'),
        ('other', 'Other'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
    ]
    
    expense_date = models.DateField()
    vendor = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    category = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='expenses')
    payment_method = models.CharField(max_length=20, choices=Payment.PAYMENT_METHOD_CHOICES, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    receipt = models.FileField(upload_to='expenses/receipts/', blank=True, null=True)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='expense_accounts')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='expenses_created')
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-expense_date', '-id']
    
    def __str__(self):
        return f"Expense - {self.vendor} - {self.amount}"
