from django.db import models
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import User


class UserProxy(User):
    class Meta:
        proxy = True

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROLE_CHOICES = [
        ('frontdesk', 'Front Desk'),
        ('caseworker', 'Caseworker'),
        ('manager', 'Manager'),
        ('accountant', 'Accountant'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_rcic = models.BooleanField(default=False)


class Applicant(models.Model):
    client_id = models.CharField(max_length=100, unique=True)
    f_name = models.CharField(max_length=100, blank=True, null=True)
    m_name = models.CharField(max_length=100, blank=True, null=True)
    l_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.BigIntegerField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    application_type = models.CharField(max_length=100, blank=True, null=True)
    client_retained_amount = models.FloatField(blank=True, null=True)
    tax_amount = models.FloatField(blank=True, null=True)
    application_fee_amount = models.FloatField(blank=True, null=True)
    biometric_fee_amount = models.FloatField(blank=True, null=True)
    total_fee_amount = models.FloatField(blank=True, null=True)
    balance_amount = models.FloatField(blank=True, null=True)
    advance_amount = models.FloatField(blank=True, null=True)
    ready_to_submit = models.BooleanField(default=False)
    ready_to_review = models.BooleanField(default=False)
    submitted = models.BooleanField(default=False)
    payment_completed = models.BooleanField(default=False)
    status = models.CharField(max_length=100, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applicant')
    r_f_name = models.CharField(max_length=100, blank=True, null=True)
    r_m_name = models.CharField(max_length=100, blank=True, null=True)
    r_l_name = models.CharField(max_length=100, blank=True, null=True)
    rcic = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rcic')
    added_at = models.DateTimeField(auto_now_add=True)
    service_agreement = models.FileField(upload_to='agreements/', blank=True, null=True)
    is_backedout = models.BooleanField(default=False)
    uci_number = models.CharField(max_length=100, blank=True, null=True)
    application_number = models.CharField(max_length=100, blank=True, null=True)
    application_expiry = models.DateField(blank=True, null=True)
    biometrics_request = models.CharField(max_length=100, blank=True, null=True)
    medical_request = models.CharField(max_length=100, blank=True, null=True)
    service_agreement_check = models.BooleanField(default=False)
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.f_name} ({self.client_id})'


class CaseWorkerAssignment(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='assignments')
    caseworker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments_assigned')
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.caseworker} assigned to {self.applicant}'


class Payments(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='payments')
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    added_at = models.DateTimeField(auto_now_add=True)
    amount = models.FloatField()
    payment_method = models.CharField(max_length=100, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paid_date = models.DateTimeField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)


class Comments(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='comments')
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    added_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)


class Services(models.Model):
    name = models.CharField(max_length=100)
    application_fee = models.FloatField()
    bio_metric_fee = models.FloatField()
    is_active = models.BooleanField(default=True)
    check_list = models.FileField(upload_to='Services_Checklist/', blank=True, null=True)

    def __str__(self):
        return self.name


class CheckList(models.Model):
    name = models.CharField(max_length=100)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='check_list')
    services = models.ManyToManyField(Services, related_name='checklist_items')
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class CheckListAssignment(models.Model):
    item = models.ForeignKey(CheckList, on_delete=models.CASCADE, related_name='check_list_item')
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='check_list_assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='check_list_assignment')
    added_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)  # Track if the checklist item is completed

    def __str__(self):
        return f'{self.item.name} for {self.applicant.client_id}'
