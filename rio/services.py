import os
import threading
from datetime import datetime
from html import unescape
from io import BytesIO
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
from django.conf import settings
from django.template.loader import render_to_string
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from weasyprint import HTML
import pdfkit
from .utils import Mailing
from import_export import resources, fields
from .models import Applicant, Payments
# def services_checklist(service, service_name):
#     # return "/Services_Checklist"
#     # Paths to header and output directories
#     header_path = os.path.join(settings.BASE_DIR, 'static', 'checklist.pdf')
#     output_pdf_dir = os.path.join(settings.MEDIA_ROOT, 'Services_Checklist')
#     os.makedirs(output_pdf_dir, exist_ok=True)
#
#     output_pdf_path = os.path.join(output_pdf_dir, f'{service_name.replace(" ", "_")}_checklist.pdf')
#
#     # Create the content PDF from HTML
#     html_content = "<html><body>"
#     html_content += f"<div style='margin-top: 150px;'><center>Service Name: {service_name}</center></div>"
#     html_content += "<div style='display: flex; flex-wrap: wrap; margin-top: 20px; width: 100%;'>"
#     for checklist in service:
#         html_content += f'<div style="padding: 10px; margin: 5px; border: 1px solid;">{checklist.name}</div>'
#     html_content += "</div></body></html>"
#
#     content_pdf_path = os.path.join(output_pdf_dir, f'{service_name.replace(" ", "_")}_content.pdf')
#
#     # Use pdfkit to generate the content PDF
#     pdfkit.from_string(html_content, content_pdf_path)
#
#     # Open the header PDF and the generated content PDF
#     with open(header_path, 'rb') as header_pdf, open(content_pdf_path, 'rb') as content_pdf:
#         header_reader = PyPDF2.PdfReader(header_pdf)
#         content_reader = PyPDF2.PdfReader(content_pdf)
#
#         # Create a writer object to combine both PDFs
#         pdf_writer = PyPDF2.PdfWriter()
#
#         # Iterate through the pages and overlay content on the header pages
#         for header_page in header_reader.pages:
#             # Merge the first page of the content PDF onto the header page
#             content_page = content_reader.pages[0]  # Assuming only one page of content
#             header_page.merge_page(content_page)  # Overlay the content onto the header
#
#             # Add the merged page to the writer
#             pdf_writer.add_page(header_page)
#
#         # Write the combined PDF to the output file
#         with open(output_pdf_path, 'wb') as output_pdf:
#             pdf_writer.write(output_pdf)
#
#     if os.path.exists(content_pdf_path):
#         os.remove(content_pdf_path)
#
#     relative_output_pdf_path = os.path.relpath(output_pdf_path, settings.MEDIA_ROOT)
#     return relative_output_pdf_path



def services_checklist(service, service_name):
    # return "/Services_Checklist"
    # Paths to header and output directories
    header_path = os.path.join(settings.BASE_DIR, 'static', 'checklist.pdf')
    output_pdf_dir = os.path.join(settings.MEDIA_ROOT, 'Services_Checklist')
    os.makedirs(output_pdf_dir, exist_ok=True)

    output_pdf_path = os.path.join(output_pdf_dir, f'{service_name.replace(" ", "_")}_checklist.pdf')

    # Create the content PDF from HTML
    html_content = "<html><body>"
    html_content += f"<div style='margin-top: 150px;'><center>Service Name: {service_name}</center></div>"
    html_content += "<div style='display: flex; flex-wrap: wrap; margin-top: 20px; width: 100%;'>"
    for checklist in service:
        html_content += f'<div style="padding: 10px; margin: 5px; border: 1px solid;">{checklist.name}</div>'
    html_content += "</div></body></html>"

    pdf_file = BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_file.seek(0)

    # Save the generated content PDF to disk temporarily
    content_pdf_path = os.path.join(output_pdf_dir, f'{service_name.replace(" ", "_")}_content.pdf')
    with open(content_pdf_path, 'wb') as f:
        f.write(pdf_file.read())

    # Open the header PDF and the generated content PDF
    with open(header_path, 'rb') as header_pdf, open(content_pdf_path, 'rb') as content_pdf:
        header_reader = PyPDF2.PdfReader(header_pdf)
        content_reader = PyPDF2.PdfReader(content_pdf)

        # Create a writer object to combine both PDFs
        pdf_writer = PyPDF2.PdfWriter()

        # Iterate through the pages and overlay content on the header pages
        for header_page in header_reader.pages:
            # Merge the first page of the content PDF onto the header page
            content_page = content_reader.pages[0]  # Assuming only one page of content
            header_page.merge_page(content_page)  # Overlay the content onto the header

            # Add the merged page to the writer
            pdf_writer.add_page(header_page)

        # Write the combined PDF to the output file
        with open(output_pdf_path, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)

    if os.path.exists(content_pdf_path):
        os.remove(content_pdf_path)

    relative_output_pdf_path = os.path.relpath(output_pdf_path, settings.MEDIA_ROOT)
    return relative_output_pdf_path


def generate_agreement(applicant):
    # Define paths
    input_pdf_path = os.path.join(settings.BASE_DIR, 'static', 'Service.pdf')
    output_pdf_dir = os.path.join(settings.MEDIA_ROOT, 'agreements')
    os.makedirs(output_pdf_dir, exist_ok=True)

    output_pdf_path = os.path.join(output_pdf_dir, f'{applicant.client_id}_agreement.pdf')

    # Combine the applicant's names
    client_name = f"{applicant.f_name or ''} {applicant.m_name or ''} {applicant.l_name or ''}".strip()

    # Combine the representative's names
    rep_name = f"{applicant.r_f_name or ''} {applicant.r_m_name or ''} {applicant.r_l_name or ''}".strip()

    # Format the date of birth
    # dob_date = applicant.dob.strftime("%b %d, %Y") if applicant.dob else ''
    dob_date = ''
    if applicant.dob:
        if isinstance(applicant.dob, str):
            try:
                dob_date_obj = datetime.strptime(applicant.dob, "%Y-%m-%d")
                dob_date = dob_date_obj.strftime("%b %d, %Y")
            except ValueError:
                dob_date = applicant.dob  # If it's not a valid date string, leave it as is
        elif isinstance(applicant.dob, datetime):
            dob_date = applicant.dob.strftime("%b %d, %Y")
        else:
            dob_date = applicant.dob.strftime("%b %d, %Y")

    # Calculate the government fee (application_fee_amount + biometric_fee_amount)
    gov_fee = (applicant.application_fee_amount or 0) + (applicant.biometric_fee_amount or 0)
    fees = (applicant.client_retained_amount or 0) + (applicant.tax_amount or 0)
    # Dictionary of values to replace in the PDF
    replacements = {
        "{{client_name}}": client_name,
        "{{rep_name}}": rep_name,
        "{{address}}": applicant.address or '',
        "{{dob_date}}": dob_date,
        "{{prof_fee}}": f"${applicant.client_retained_amount or 0:.2f}",
        "{{other}}": '$0',
        "{{dummy}}": '',
        "{{app_tax}}": f"${applicant.tax_amount or 0:.2f}",
        # application_type
        "{{application_type}}": f"{applicant.application_type}",
        "{{gov_fee}}": f"${gov_fee:.2f}",
        "{{total_cost}}": f"${applicant.total_fee_amount or 0:.2f}",
        "{{deposit}}": f"${applicant.advance_amount or 0:.2f}",
        # fees
        "{{fees}}": f"CDN ${fees or 0:.2f}",
        # rcic_name
        "{{rcic_name}}": f"{applicant.rcic.first_name} {applicant.rcic.last_name}",
        # today
        "{{today}}": f"{datetime.today().strftime('%b %d, %Y')}",
        "{{balance}}": f"${applicant.balance_amount or 0:.2f}"
    }

    # Load the template PDF
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    # Iterate over each page of the PDF
    for i, page in enumerate(reader.pages):
        # Create an overlay specific to this page
        temp_overlay_path = os.path.join(output_pdf_dir, f'temp_overlay_page_{i}.pdf')
        create_overlay_pdf(temp_overlay_path, replacements, page_num=i)

        # Merge the overlay with the original page
        overlay_reader = PdfReader(temp_overlay_path)
        merger = PageMerge(page)
        merger.add(overlay_reader.pages[0]).render()

        writer.addpage(page)

        # Clean up the temporary overlay file
        os.remove(temp_overlay_path)

    # Write the final output to the file
    with open(output_pdf_path, 'wb') as f_out:
        writer.write(f_out)

    relative_output_pdf_path = os.path.relpath(output_pdf_path, settings.MEDIA_ROOT)
    return relative_output_pdf_path


def create_overlay_pdf(overlay_path, replacements, page_num):
    """Create a PDF overlay with the replacement text for a specific page."""
    c = canvas.Canvas(overlay_path, pagesize=letter)

    # Example positions for the text for different pages
    if page_num == 0:  # First page
        positions = {
            "{{client_name}}": (128, 630),
            "{{rep_name}}": (195, 606),
            "{{address}}": (145, 554),
            "{{dob_date}}": (185, 519),
            "{{application_type}}": (260, 345),
        }
    elif page_num == 2:
        positions = {
            "{{fees}}": (210, 319),
            "{{prof_fee}}": (400, 185),
            "{{other}}": (400, 150),
            "{{app_tax}}": (400, 110),
        }
    elif page_num == 3:
        positions = {
            "{{gov_fee}}": (400, 670),
            "{{total_cost}}": (400, 640),
            "{{deposit}}": (400, 535),
            "{{balance}}": (400, 515)
        }
    elif page_num == 8:
        positions = {
            "{{rcic_name}}": (120, 335),
            "{{today}}": (440, 335)
        }
    else:
        positions = {"{{dummy}}": (100, 610)}

    # Draw the text on the overlay at the specified positions
    for key, value in replacements.items():
        if key in positions:
            x, y = positions[key]
            if key == "{{application_type}}":
                c.setFont('Helvetica-BoldOblique', 12)
            c.drawString(x, y, value)

    c.save()


class NotificationService:

    @staticmethod
    def send_email_notification(subject, body, recipients):
        def send_email():
            email_body = render_to_string('notifications/base_email_template.html', {"body": body})
            mail_body = unescape(email_body)
            Mailing.send_mail(
                subject=subject,
                message="",
                recipients=recipients,
                html_message=mail_body,
                from_email=settings.EMAIL_HOST_USER,
            )

        # Create a thread for the send_email function
        email_thread = threading.Thread(target=send_email)
        email_thread.start()


class ApplicantResource(resources.ModelResource):
    adjustment = fields.Field(column_name='adjustment')

    def dehydrate_adjustment(self, applicant):
        adjustment_payments = Payments.objects.filter(applicant=applicant, payment_method="Adjustment")
        total_adjustment = sum(payment.amount for payment in adjustment_payments)
        return total_adjustment or 0

    class Meta:
        model = Applicant
        fields = (
            'client_id', 'f_name', 'm_name', 'l_name', 'email', 'phone', 'address',
            'dob', 'application_type', 'client_retained_amount', 'tax_amount',
            'application_fee_amount', 'biometric_fee_amount', 'total_fee_amount',
            'balance_amount', 'submitted', 'payment_completed', 'status',
            'is_approved', 'is_rejected', 'added_by__username', 'r_f_name',
            'r_m_name', 'r_l_name', 'rcic__username', 'added_at',
            'is_backedout', 'uci_number',
            'application_number', 'application_expiry', 'biometrics_request',
            'medical_request', 'service_agreement_check', 'adjustment'
        )
        export_order = fields

