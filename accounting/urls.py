from django.urls import path
from rio.decorators import role_required
from .views import *

urlpatterns = [
    # Invoices
    path('invoices', role_required('accountant', 'admin', 'manager')(invoices), name='accounting_invoices'),
    path('invoices/create', role_required('accountant', 'admin', 'manager')(create_invoice), name='accounting_invoice_create'),
    path('invoices/<int:invoice_id>', role_required('accountant', 'admin', 'manager')(view_invoice), name='accounting_invoice_view'),
    path('invoices/<int:invoice_id>/edit', role_required('accountant', 'admin', 'manager')(edit_invoice), name='accounting_invoice_edit'),
    path('invoices/<int:invoice_id>/delete', role_required('accountant', 'admin', 'manager')(delete_invoice), name='accounting_invoice_delete'),
    path('invoices/<int:invoice_id>/change-status', role_required('accountant', 'admin', 'manager')(change_invoice_status), name='accounting_invoice_change_status'),
    path('invoices/<int:invoice_id>/send', role_required('accountant', 'admin', 'manager')(send_invoice), name='accounting_invoice_send'),
    
    # Customers - COMMENTED OUT: Using rio.Applicant directly now
    # path('customers', role_required('accountant', 'admin', 'manager')(customers), name='accounting_customers'),
    # path('customers/create', role_required('accountant', 'admin', 'manager')(create_customer), name='accounting_customer_create'),
    # path('customers/<int:customer_id>/edit', role_required('accountant', 'admin', 'manager')(edit_customer), name='accounting_customer_edit'),
    path('customers/statements', role_required('accountant', 'admin', 'manager')(customer_statements), name='accounting_customer_statements'),
    
    # Products & Services - COMMENTED OUT: Using rio.Services directly now
    # path('products-services', role_required('accountant', 'admin', 'manager')(products_services), name='accounting_products_services'),
    # path('products-services/create', role_required('accountant', 'admin', 'manager')(create_product_service), name='accounting_product_service_create'),
    # path('products-services/<int:product_id>/edit', role_required('accountant', 'admin', 'manager')(edit_product_service), name='accounting_product_service_edit'),
    
    # Transactions
    path('transactions', role_required('accountant', 'admin', 'manager')(transactions), name='accounting_transactions'),
    path('transactions/create', role_required('accountant', 'admin', 'manager')(create_transaction), name='accounting_transaction_create'),
    path('transactions/<int:transaction_id>/delete', role_required('accountant', 'admin', 'manager')(delete_transaction), name='accounting_transaction_delete'),
    path('transactions/bulk-delete', role_required('accountant', 'admin', 'manager')(bulk_delete_transactions), name='accounting_transactions_bulk_delete'),
    path('transactions/bulk-categorize', role_required('accountant', 'admin', 'manager')(bulk_categorize_transactions), name='accounting_transactions_bulk_categorize'),
    
    # Chart of Accounts
    path('chart-of-accounts', role_required('accountant', 'admin', 'manager')(chart_of_accounts), name='accounting_chart_of_accounts'),
    path('chart-of-accounts/create', role_required('accountant', 'admin', 'manager')(create_account), name='accounting_account_create'),
    path('chart-of-accounts/<int:account_id>/edit', role_required('accountant', 'admin', 'manager')(edit_account), name='accounting_account_edit'),
    
    # Expenses
    path('expenses', role_required('accountant', 'admin', 'manager')(expenses), name='accounting_expenses'),
    path('expenses/create', role_required('accountant', 'admin', 'manager')(create_expense), name='accounting_expense_create'),
    
    # Payments
    path('payments', role_required('accountant', 'admin', 'manager')(payments), name='accounting_payments'),
    path('payments/create', role_required('accountant', 'admin', 'manager')(create_payment), name='accounting_payment_create'),
    
    # Reports
    path('reports', role_required('accountant', 'admin', 'manager')(reports), name='accounting_reports'),
    path('reports/profit-loss', role_required('accountant', 'admin', 'manager')(profit_loss_report), name='accounting_profit_loss'),
    path('reports/balance-sheet', role_required('accountant', 'admin', 'manager')(balance_sheet_report), name='accounting_balance_sheet'),
    
    # Business Info & Settings
    path('business-info', role_required('accountant', 'admin', 'manager')(business_info), name='accounting_business_info'),
    path('email-templates', role_required('accountant', 'admin', 'manager')(email_templates), name='accounting_email_templates'),
    path('settings', role_required('accountant', 'admin', 'manager')(invoice_settings), name='accounting_invoice_settings'),
    
    # Invoice Preview
    path('invoices/<int:invoice_id>/preview', role_required('accountant', 'admin', 'manager')(invoice_preview), name='accounting_invoice_preview'),
    
    # AJAX endpoints
    # Service details endpoint (legacy ProductService-based API kept disabled)
    # path('api/service/<int:service_id>', role_required('accountant', 'admin', 'manager')(get_service_details), name='accounting_api_service'),
    path(
        'api/applicant/<int:applicant_id>/invoices',
        role_required('accountant', 'admin', 'manager')(get_applicant_invoices),
        name='accounting_api_applicant_invoices',
    ),
    path(
        'api/applicant/<int:applicant_id>/data',
        role_required('accountant', 'admin', 'manager')(get_applicant_data),
        name='accounting_api_applicant_data',
    ),
    path('api/invoice-number', role_required('accountant', 'admin', 'manager')(get_invoice_number), name='accounting_api_invoice_number'),
    
    # DataTables AJAX endpoints
    path('api/datatable/transactions', role_required('accountant', 'admin', 'manager')(datatable_transactions), name='accounting_datatable_transactions'),
    path('api/datatable/customers', role_required('accountant', 'admin', 'manager')(datatable_customers), name='accounting_datatable_customers'),
    path('api/datatable/expenses', role_required('accountant', 'admin', 'manager')(datatable_expenses), name='accounting_datatable_expenses'),
    path('api/datatable/products', role_required('accountant', 'admin', 'manager')(datatable_products), name='accounting_datatable_products'),
    path('api/datatable/invoices', role_required('accountant', 'admin', 'manager')(datatable_invoices), name='accounting_datatable_invoices'),
    path('api/datatable/payments', role_required('accountant', 'admin', 'manager')(datatable_payments), name='accounting_datatable_payments'),
]
