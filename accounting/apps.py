from django.apps import AppConfig


class AccountingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounting'

    def ready(self):
        # Import signal handlers to wire up automatic behaviours such as
        # creating an initial invoice when a new Applicant is created.
        from . import signals  # noqa: F401

