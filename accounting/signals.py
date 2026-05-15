from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from rio.models import Applicant

from .models import Invoice, InvoiceItem, BusinessInfo


def _generate_next_invoice_number() -> str:
    """
    Generate the next invoice number using the same RI-prefixed sequence
    convention as the manual create view.
    """
    last_invoice = Invoice.objects.order_by("-id").first()
    if last_invoice and last_invoice.invoice_number:
        inv_num = last_invoice.invoice_number.strip().upper()
        try:
            if inv_num.startswith("RI"):
                last_num = int(inv_num[2:])
                return f"RI{last_num + 1:05d}"
            if inv_num.startswith("NB"):
                # Support legacy NB-prefixed invoices
                last_num = int(inv_num[2:])
                return f"RI{last_num + 1:05d}"
            # Fallback for formats like XXX-00001
            last_num = int(inv_num.split("-")[-1])
            return f"RI{last_num + 1:05d}"
        except Exception:
            pass
    return "RI000001"


@receiver(post_save, sender=Applicant)
def create_initial_invoice_for_applicant(sender, instance: Applicant, created: bool, **kwargs):
    """
    Automatically create an initial draft invoice when an Applicant is created
    manually and has fee data configured.

    The invoice:
    - Uses applicant fee fields (client_retained_amount, application_fee_amount,
      biometric_fee_amount) to seed line items.
    - Marks only the application fee line as taxable; other lines are non-taxable
      by default, keeping tax strictly on the application fee unless the user
      later opts in on custom items.
    """
    if not created:
        return

    # Avoid creating duplicate invoices for the same applicant
    if Invoice.objects.filter(applicant=instance).exists():
        return

    # Only create an invoice if there is at least some fee information
    has_fee_data = any(
        [
            getattr(instance, "application_fee_amount", None),
            getattr(instance, "biometric_fee_amount", None),
            getattr(instance, "client_retained_amount", None),
            getattr(instance, "total_fee_amount", None),
        ]
    )
    if not has_fee_data:
        return

    business = BusinessInfo.get_current()
    today = timezone.now().date()
    due_date = today + timezone.timedelta(days=business.default_due_days or 30)

    invoice = Invoice.objects.create(
        invoice_number=_generate_next_invoice_number(),
        applicant=instance,
        invoice_date=today,
        due_date=due_date,
        title="Invoice",
        summary=(
            f"Services for {getattr(instance, 'application_type', '') or 'application'}"
        ),
        status="draft",
    )

    # Build the same conceptual items as the AJAX endpoint, but as real lines.
    # Application Fee (taxable)
    if getattr(instance, "application_fee_amount", None):
        amount = Decimal(str(instance.application_fee_amount))
        if amount > 0:
            InvoiceItem.objects.create(
                invoice=invoice,
                description=f"Application fee for {getattr(instance, 'application_type', '') or 'service'}",
                quantity=Decimal("1.00"),
                unit_price=amount,
                tax_rate=Decimal("0.00"),
                is_taxable=True,  # ONLY application fee is taxable by default
            )

    # Biometric Fee (non-taxable)
    if getattr(instance, "biometric_fee_amount", None):
        amount = Decimal(str(instance.biometric_fee_amount))
        if amount > 0:
            InvoiceItem.objects.create(
                invoice=invoice,
                description="Biometric fee",
                quantity=Decimal("1.00"),
                unit_price=amount,
                tax_rate=Decimal("0.00"),
                is_taxable=False,
            )

    # Client Retained Amount / Service Fee (non-taxable)
    if getattr(instance, "client_retained_amount", None):
        amount = Decimal(str(instance.client_retained_amount))
        if amount > 0:
            InvoiceItem.objects.create(
                invoice=invoice,
                description=f"Service fee for {getattr(instance, 'application_type', '') or 'service'}",
                quantity=Decimal("1.00"),
                unit_price=amount,
                tax_rate=Decimal("0.00"),
                is_taxable=False,
            )

    # If no granular items were created but there is a total fee, fall back to a
    # single non-taxable "Total Service Fee" line. Admins can later split or
    # adjust items from the UI if needed.
    if not invoice.items.exists() and getattr(instance, "total_fee_amount", None):
        total_amount = Decimal(str(instance.total_fee_amount))
        if total_amount > 0:
            InvoiceItem.objects.create(
                invoice=invoice,
                description=f"Total service fee for {getattr(instance, 'application_type', '') or 'service'}",
                quantity=Decimal("1.00"),
                unit_price=total_amount,
                tax_rate=Decimal("0.00"),
                is_taxable=False,
            )

    # Initialise totals using the default tax settings; admins can override
    # slab/tax rate later from the invoice UI.
    invoice.discount_amount = Decimal("0.00")
    invoice.tax_rate = Decimal("0.00")
    invoice.calculate_totals()

