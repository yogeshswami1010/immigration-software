from django.core.mail import send_mail


class Mailing:
    @staticmethod
    def send_mail(subject, message, recipients, html_message, from_email):
        sent = send_mail(
            subject=subject,
            message=message,
            recipient_list=recipients,
            html_message=html_message,
            from_email=from_email,
        )

        return sent