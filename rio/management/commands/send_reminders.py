import logging
from datetime import timedelta, date
from django.core.management.base import BaseCommand
from rio.models import Applicant, Profile
from rio.services import NotificationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send reminder emails for permit renewal'

    def handle(self, *args, **kwargs):
        try:
            today = date.today()
            self.stdout.write(f"Starting reminders for {today}.")
            reminders = [90, 60, 30, 7]

            for reminder in reminders:
                try:
                    reminder_date = today + timedelta(days=reminder)
                    applicants = Applicant.objects.filter(application_expiry=reminder_date)
                    for applicant in applicants:
                        try:
                            if reminder == 7:
                                try:
                                    subject = f'Action Required: Status Expiration in {reminder} Days'
                                    email_recipients = [applicant.rcic.email]
                                    managers_emails = [i.user.email for i in
                                                       Profile.objects.filter(role__in=["admin", "manager"])]
                                    email_recipients.extend(managers_emails)
                                    email_recipients = list(set(email_recipients))
                                    logger.info(f"Sending 7-day reminder to: {email_recipients}")
                                    email_to_company = f"""
                                    This is to inform you that the Application: {applicant.client_id} Status is Expiration in {reminder} Days:
                                    <br><br>
                                    <b>Client ID</b>: {applicant.client_id}<br>
                                    <b>Application Type</b>: {applicant.application_type}<br>
                                    <b>Applicant Name</b>: {applicant.f_name} {applicant.m_name or ""} {applicant.l_name}<br>
                                    <b>Email</b>: {applicant.email}<br>
                                    <b>Phone</b>: {applicant.phone}<br>
                                    <b>Date of Birth</b>: {applicant.dob}<br>
                                    <b>Address</b>: {applicant.address}<br>
                                    <br><br>
                                    Please log in to the system to view the applicant's details and proceed with the necessary actions.<br><br>
                                    """
                                    NotificationService.send_email_notification(
                                        subject,
                                        email_to_company,
                                        email_recipients)
                                except Exception as e:
                                    logger.error(
                                        f"Error sending 7-day reminder for applicant {applicant.client_id}: {str(e)}")
                                    self.stdout.write(self.style.ERROR(
                                        f"Failed to send 7-day reminder for applicant {applicant.client_id}"))

                            else:
                                if applicant.email:
                                    try:
                                        subject = f'Action Required: Status Expiration in {reminder} Days'
                                        email_to_client = f"""
                                        <p>Dear {applicant.f_name},
                                        <br><br>
                                        We hope this message finds you well. We are reaching out to remind you that your {applicant.application_type} is set to expire on <b>{applicant.application_expiry}</b>, which is {reminder} days from now.
                                        <br><br>
                                        This is a great time to start planning for your extension or transition to a new status to ensure uninterrupted residency in Canada. Our team is here to help guide you through the process.
                                        <br><br>
                                        To get started, please reply to this email or contact us at <b>905-462-9000</b> to discuss your options. Starting early will give you ample time to prepare and avoid any last-minute issues.
                                        <br><br>
                                        We look forward to assisting you!
                                        <br><br>
                                        Best regards,<br>
                                        Rio Immigration Consultancy Group<br>
                                        Website: <a href="https://rioimm.ca">www.rioimm.ca</a>
                                        </p>
                                        """
                                        NotificationService.send_email_notification(
                                            subject,
                                            email_to_client,
                                            [applicant.email])
                                        self.stdout.write(
                                            f"Reminder email sent to {applicant.email} for permit expiry on {applicant.application_expiry}.")
                                        logger.info(
                                            f"Reminder email sent to {applicant.email} for permit expiry on {applicant.application_expiry}")
                                    except Exception as e:
                                        logger.error(f"Error sending reminder email to {applicant.email}: {str(e)}")
                                        self.stdout.write(
                                            self.style.ERROR(f"Failed to send reminder email to {applicant.email}"))
                                else:
                                    logger.warning(f"Applicant {applicant.client_id} does not have an email address")
                                    self.stdout.write(
                                        f"Applicant {applicant.client_id} does not have an email address.")

                        except Exception as e:
                            logger.error(f"Error processing applicant {applicant.client_id}: {str(e)}")
                            self.stdout.write(self.style.ERROR(f"Error processing applicant {applicant.client_id}"))
                            continue

                except Exception as e:
                    logger.error(f"Error processing {reminder}-day reminders: {str(e)}")
                    self.stdout.write(self.style.ERROR(f"Error processing {reminder}-day reminders"))
                    continue

        except Exception as e:
            logger.error(f"Fatal error in reminder command: {str(e)}")
            self.stdout.write(self.style.ERROR("Fatal error in reminder command"))
            raise
