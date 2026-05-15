from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    Account,
    Invoice,
    InvoiceItem,
    Transaction,
    Payment,
    Expense,
    BusinessInfo,
    EmailTemplate,
    TaxSlab,
)


@admin.register(Account)
class AccountAdmin(SimpleHistoryAdmin):
    list_display = ['account_number', 'name', 'account_type', 'parent_account', 'is_active', 'created_at']
    list_filter = ['account_type', 'is_active', 'created_at']
    search_fields = ['name', 'account_number', 'description']
    ordering = ['account_number', 'name']


# Customer and ProductService admin classes removed - using rio.Applicant and rio.Services directly now
# @admin.register(Customer)
# class CustomerAdmin(SimpleHistoryAdmin):
#     list_display = ['name', 'email', 'phone', 'city', 'is_active', 'created_at']
#     list_filter = ['is_active', 'created_at', 'country']
#     search_fields = ['name', 'email', 'phone', 'address']
#     ordering = ['name']


# @admin.register(ProductService)
# class ProductServiceAdmin(SimpleHistoryAdmin):
#     list_display = ['name', 'type', 'sku', 'price', 'cost', 'tax_rate', 'is_active', 'created_at']
#     list_filter = ['type', 'is_active', 'created_at']
#     search_fields = ['name', 'sku', 'description']
#     ordering = ['name']


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ['service', 'description', 'quantity', 'unit_price', 'tax_rate', 'line_total']
    readonly_fields = ['line_total']


@admin.register(Invoice)
class InvoiceAdmin(SimpleHistoryAdmin):
    list_display = ['invoice_number', 'applicant', 'invoice_date', 'due_date', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'invoice_date', 'created_at']
    search_fields = ['invoice_number', 'applicant__f_name', 'applicant__l_name', 'applicant__client_id', 'notes']
    readonly_fields = ['invoice_number', 'subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at']
    inlines = [InvoiceItemInline]
    ordering = ['-invoice_date', '-invoice_number']
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'applicant', 'invoice_date', 'due_date', 'status')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(SimpleHistoryAdmin):
    list_display = ['transaction_date', 'transaction_type', 'account', 'amount', 'description', 'created_at']
    list_filter = ['transaction_type', 'transaction_date', 'account', 'created_at']
    search_fields = ['description', 'reference_number']
    readonly_fields = ['created_at']
    ordering = ['-transaction_date', '-id']


@admin.register(Payment)
class PaymentAdmin(SimpleHistoryAdmin):
    list_display = ['payment_date', 'applicant', 'invoice', 'amount', 'payment_method', 'created_at']
    list_filter = ['payment_method', 'payment_date', 'created_at']
    search_fields = ['applicant__f_name', 'applicant__l_name', 'applicant__client_id', 'invoice__invoice_number', 'reference_number']
    readonly_fields = ['created_at']
    ordering = ['-payment_date', '-id']


@admin.register(Expense)
class ExpenseAdmin(SimpleHistoryAdmin):
    list_display = ['expense_date', 'vendor', 'amount', 'category', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'expense_date', 'category', 'created_at']
    search_fields = ['vendor', 'description', 'reference_number']
    readonly_fields = ['created_at']
    ordering = ['-expense_date', '-id']


@admin.register(BusinessInfo)
class BusinessInfoAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'city', 'province', 'country', 'phone', 'created_at']
    search_fields = ['name', 'city', 'province', 'country', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(SimpleHistoryAdmin):
    list_display = ['template_type', 'subject', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['subject', 'body']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TaxSlab)
class TaxSlabAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'rate', 'is_default', 'is_active', 'created_at']
    list_filter = ['is_default', 'is_active', 'created_at']
    search_fields = ['name']
