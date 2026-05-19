from datetime import datetime, date, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.db.models.functions import TruncDate
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.db.models import Sum, Count, Q

from .models import Services, Payments, Comments, Profile, CheckList, \
    CheckListAssignment, Applicant, CaseWorkerAssignment
from .services import NotificationService, generate_agreement, services_checklist, ApplicantResource


def welcome(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return render(request, 'login.html')


def login(request):
    auth_logout(request)
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('/dashboard')
        else:
            messages.error(request, 'Invalid email or password')
            return redirect('/')
    return render(request, 'login.html')


@login_required
def logout(request):
    auth_logout(request)
    return redirect('/')


@login_required
def services(request):
    if request.method == 'POST':
        service_name = request.POST.get('service_name')
        application_fee = request.POST.get('application_fee')
        biometric_fee = request.POST.get('biometric_fee')
        selected_checklists = request.POST.getlist('checklists')
        print(selected_checklists)
        if 'service_id' in request.POST:
            service_id = request.POST.get('service_id')
            service = get_object_or_404(Services, id=service_id)
            service.name = service_name
            service.application_fee = application_fee
            service.bio_metric_fee = biometric_fee
            service.save()
            messages.success(request, 'Service Updated Successfully')

            # Update checklist associations
            service.checklist_items.clear()
            for checklist_id in selected_checklists:
                checklist_item = get_object_or_404(CheckList, id=checklist_id)
                service.checklist_items.add(checklist_item)
        else:
            service = Services(name=service_name, application_fee=application_fee, bio_metric_fee=biometric_fee)
            service.save()
            messages.success(request, 'Service Added Successfully')

            # Assign selected checklist items to the service
            for checklist_id in selected_checklists:
                checklist_item = get_object_or_404(CheckList, id=checklist_id)
                service.checklist_items.add(checklist_item)

        checklists = CheckList.objects.filter(services=service, is_active=True)
        check_list_file = services_checklist(checklists, service.name)
        service.check_list = check_list_file
        service.save()
        return redirect('/services')

    all_services = Services.objects.filter(is_active=True)
    all_checklists = CheckList.objects.filter(is_active=True)  # Get active checklists
    return render(request, 'services.html', {
        'services': all_services,
        'checklists': all_checklists
    })


@login_required
def get_service_checklist(request):
    service_id = request.GET.get('service_id')
    service = get_object_or_404(Services, id=service_id)
    assigned_checklists = CheckList.objects.filter(services=service).values_list('id', flat=True)
    return JsonResponse({'assigned_checklists': list(assigned_checklists)})


@login_required
def check_list(request):
    if request.method == 'POST':
        check_list_name = request.POST.get('check_list_name')

        new_item = CheckList(name=check_list_name, added_by=request.user)
        new_item.save()
        return redirect('/check-list')

    all_items = CheckList.objects.filter(is_active=True)
    return render(request, 'check_list.html', {'check_list': all_items})


@login_required
def deactivate_service(request):
    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        service = get_object_or_404(Services, id=service_id)
        service.is_active = False
        service.save()
        messages.success(request, 'Service Deactivated Successfully')
    return redirect('/services')


@login_required
def search_applications(request):
    filter_dict = {}
    search_client_id = request.GET.get('search_client_id')
    search_phone = request.GET.get('search_phone')
    search_email = request.GET.get('search_email')
    search_application_status = request.GET.get('search_application_status')
    search_start_date = request.GET.get('search_start_date')
    search_end_date = request.GET.get('search_end_date')
    search_payment_status = request.GET.get('search_payment_status')
    search_uci_number = request.GET.get('search_uci_number')

    if search_client_id:
        filter_dict['client_id__icontains'] = search_client_id

    if search_uci_number:
        filter_dict['uci_number__icontains'] = search_uci_number

    if search_phone:
        filter_dict['phone__icontains'] = search_phone

    if search_email:
        filter_dict['email__icontains'] = search_email

    if search_application_status:
        if search_application_status == 'pending':
            filter_dict['ready_to_submit'] = False
            filter_dict['submitted'] = False
            filter_dict['is_approved'] = False
            filter_dict['is_rejected'] = False
            filter_dict['is_backedout'] = False
        elif search_application_status == 'ready':
            filter_dict['ready_to_submit'] = True
            filter_dict['submitted'] = False
            filter_dict['is_backedout'] = False
        elif search_application_status == 'submitted':
            filter_dict['submitted'] = True
            filter_dict['is_backedout'] = False
        elif search_application_status == 'approved':
            filter_dict['is_approved'] = True
            filter_dict['is_backedout'] = False
        elif search_application_status == 'rejected':
            filter_dict['is_rejected'] = True
            filter_dict['is_backedout'] = False
        elif search_application_status == 'backedout':
            filter_dict['is_backedout'] = True
    else:
        filter_dict['is_backedout'] = False

    if search_start_date:
        start_datetime = datetime.strptime(search_start_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        filter_dict['added_at__gte'] = start_datetime

    if search_end_date:
        end_datetime = datetime.strptime(search_end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
        filter_dict['added_at__lte'] = end_datetime

    if search_payment_status:
        if search_payment_status == 'pending':
            filter_dict['payment_completed'] = False
            filter_dict['is_backedout'] = False
        elif search_payment_status == 'full_paid':
            filter_dict['payment_completed'] = True
            filter_dict['is_backedout'] = False
    if filter_dict:
        if request.user.profile.role == "caseworker":
            assigned = CaseWorkerAssignment.objects.filter(caseworker=request.user).values_list('applicant_id',
                                                                                                flat=True)
            filter_dict['id__in'] = assigned
        applicants = Applicant.objects.filter(**filter_dict)
    else:
        applicants = {}
    today = date.today().isoformat()
    context = {
        'applicants': applicants,
        'today': today,
    }
    return render(request, 'search_applications.html', context)


@login_required
def rejected_applications(request):
    rejected_applicants = Applicant.objects.filter(is_rejected=True)
    if request.user.profile.role in ["admin", "manager"]:
        caseworker_assignments = rejected_applicants.prefetch_related(
            'assignments',
            'assignments__caseworker'
        )
    else:
        caseworker_assignments = CaseWorkerAssignment.objects.filter(
            applicant__in=rejected_applicants,
            caseworker=request.user
        ).select_related('applicant', 'caseworker')

    context = {
        "type": "Rejected Applications",
        "caseworker_assignments": caseworker_assignments,
        "is_staff": request.user.profile.role in ["admin", "manager"]
    }
    return render(request, 'applications.html', context)



@login_required
def accepted_applications(request):
    accepted_applicants = Applicant.objects.filter(is_approved=True)
    if request.user.profile.role in ["admin", "manager"]:
        caseworker_assignments = accepted_applicants.prefetch_related(
            'assignments',
            'assignments__caseworker'
        )
    else:
        caseworker_assignments = CaseWorkerAssignment.objects.filter(
            applicant__in=accepted_applicants,
            caseworker=request.user
        ).select_related('applicant', 'caseworker')

    context = {
        "type": "Accepted Applications",
        "caseworker_assignments": caseworker_assignments,
        "is_staff": request.user.profile.role in ["admin", "manager"]
    }
    return render(request, 'applications.html', context)




@login_required
def unassigned_applications(request):
    unassigned_applicants = Applicant.objects.filter(assignments__isnull=True)
    caseworkers = Profile.objects.filter(role__in=['caseworker', 'manager', 'admin'])
    context = {
        "type": "Unassigned Applications",
        "unassigned_applicants": unassigned_applicants,
        "caseworkers": caseworkers
    }
    return render(request, 'unassigned_applications.html', context)


@login_required
def assign_caseworker(request):
    if request.method == 'POST':
        applicant_id = request.POST.get('applicant_id')
        caseworker_id = request.POST.get('caseworker_id')

        applicant = get_object_or_404(Applicant, id=applicant_id)
        caseworker = get_object_or_404(User, id=caseworker_id)

        # Assign the caseworker to the applicant
        CaseWorkerAssignment.objects.create(applicant=applicant, caseworker=caseworker, assigned_by=request.user)
        recipients_email = [caseworker.email, applicant.rcic.email]
        managers_email = list(
            Profile.objects.filter(role__in=["manager", "admin"]).values_list('user__email', flat=True))
        recipients_email += managers_email
        recipients_email = list(set(recipients_email))
        if request.user.email in recipients_email:
            recipients_email.remove(request.user.email)
        email_body = f"""
        This is to inform you that the caseworker {caseworker} has been assigned for the following applicant:
        <br><br>
        <b>Client ID</b>: {applicant.client_id}<br>
        <b>Applicant Name</b>: {applicant.f_name} {applicant.m_name} {applicant.l_name}<br>
        <b>Email</b>: {applicant.email}<br>
        <b>Phone</b>: {applicant.phone}<br>
        <b>Date of Birth</b>: {applicant.dob}<br>
        <b>Address</b>: {applicant.address}<br>
        <br><br>
        Please log in to the system to view the applicant's details and proceed with the necessary actions.<br><br>
        """
        NotificationService.send_email_notification(f"Applicant {applicant.client_id} Assigned to {caseworker}",
                                                    email_body,
                                                    recipients_email)
        email_to_client = f"""
        <p>Dear {applicant.f_name},
        <br><br>
        We are writing to inform you that your ({applicant.application_type}) application has been assigned to Case Worker and is now under review. Below are the key details of your case:
        <br><br>
        <b>Application Type: {applicant.application_type}</b><br>
        <b>Case ID/Application Number: {applicant.client_id}</b> - RIO Dashboard Case Number
        <br><br>
        Your assigned caseworker will review your application and reach out to you if any additional information or documents are required. Please ensure your contact details are up-to-date and regularly check your email for updates regarding your application.
        <br><br>
        If you have any urgent questions or concerns, you can reach out to your caseworker for any further details.
        <br><br>
        Thank you for choosing Rio Immigration for your immigration needs. We are committed to supporting you throughout the process.
        <br><br>
        Best regards,<br>
        Rio Immigration Consultancy Group<br>
        Website: <a href="https://rioimm.ca">www.rioimm.ca</a>
        </p>
        """
        NotificationService.send_email_notification(f"Update on Your Immigration Application: [{applicant.application_type}/{applicant.client_id}]",
                                                    email_to_client,
                                                    [applicant.email])
        messages.success(request,
                         f'Caseworker {caseworker.username} has been assigned to {applicant}.')
        return redirect('unassigned_applications')


@login_required
def completed_applications(request):
    filters = {"submitted": True, "payment_completed": True}
    completed_applicants = Applicant.objects.filter(**filters)

    if request.user.profile.role in ["admin", "manager"]:
        caseworker_assignments = completed_applicants.prefetch_related(
            'assignments',
            'assignments__caseworker'
        )
    else:
        caseworker_assignments = CaseWorkerAssignment.objects.filter(
            applicant__in=completed_applicants,
            caseworker=request.user
        ).select_related('applicant', 'caseworker')

    context = {
        "type": "Completed Applications",
        "caseworker_assignments": caseworker_assignments,
        "is_staff": request.user.profile.role in ["admin", "manager"]
    }
    return render(request, 'applications.html', context)


@login_required
def submitted_applications(request):
    submitted_applicants = Applicant.objects.filter(submitted=True, is_approved=False, is_rejected=False)
    if request.user.profile.role in ["admin", "manager"]:
        caseworker_assignments = submitted_applicants.prefetch_related(
            'assignments',
            'assignments__caseworker'
        )
    else:
        caseworker_assignments = CaseWorkerAssignment.objects.filter(
            applicant__in=submitted_applicants,
            caseworker=request.user
        ).select_related('applicant', 'caseworker')

    context = {
        "type": "Submitted Applications",
        "caseworker_assignments": caseworker_assignments,
        "is_staff": request.user.profile.role in ["admin", "manager"]
    }
    return render(request, 'applications.html', context)


@login_required
def pending_applications(request):
    pending_applicants = Applicant.objects.filter(submitted=False, is_backedout=False)
    if request.user.profile.role in ["admin", "manager"]:
        caseworker_assignments = pending_applicants.prefetch_related(
            'assignments',
            'assignments__caseworker'
        )
    else:
        caseworker_assignments = CaseWorkerAssignment.objects.filter(
            applicant__in=pending_applicants,
            caseworker=request.user
        ).select_related('applicant', 'caseworker')

    context = {
        "type": "Pending Applications",
        "caseworker_assignments": caseworker_assignments,
        "is_staff": request.user.profile.role in ["admin", "manager"]
    }
    return render(request, 'applications.html', context)


@login_required
def my_applications(request):
    user = request.user
    assigned_applicants = CaseWorkerAssignment.objects.filter(caseworker=user).select_related('applicant', 'caseworker')

    context = {
        'assigned_applicants': assigned_applicants
    }
    return render(request, 'my_applications.html', context)


@login_required
def ready_for_review(request):
    pending_applicants = Applicant.objects.filter(ready_to_review=True, ready_to_submit=False, submitted=False)
    if request.user.profile.role in ["admin", "manager"]:
        caseworker_assignments = pending_applicants.prefetch_related(
            'assignments',
            'assignments__caseworker'
        )
    else:
        caseworker_assignments = CaseWorkerAssignment.objects.filter(
            applicant__in=pending_applicants,
            caseworker=request.user
        ).select_related('applicant', 'caseworker')

    context = {
        "type": "Ready for Review Applications",
        "caseworker_assignments": caseworker_assignments,
        "is_staff": request.user.profile.role in ["admin", "manager"]
    }
    return render(request, 'applications.html', context)


@login_required
def settings(request):
    form = PasswordChangeForm(request.user)
    data = {'form': form}
    return render(request, 'settings.html', data)


@login_required
def users(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_name = request.POST.get('user_name')
        user_email = request.POST.get('user_email')
        user_role = request.POST.get('user_role')
        user_password = request.POST.get('user_password')
        is_rcic = request.POST.get('is_rcic')
        if is_rcic == "yes":
            is_rcic = True
        else:
            is_rcic = False

        first_name, *last_name = user_name.split(' ')
        last_name = ' '.join(last_name)

        if user_id:
            # Editing existing user
            user = get_object_or_404(User, id=user_id)
            user.first_name = first_name
            user.last_name = last_name
            user.email = user_email
            if user_password:
                user.set_password(user_password)
            user.save()
            user.profile.role = user_role
            user.profile.is_rcic = is_rcic
            user.profile.save()
            messages.success(request, 'User updated successfully.')
        else:
            # Adding new user
            user = User.objects.create_user(username=user_email, email=user_email, password=user_password,
                                            first_name=first_name, last_name=last_name)
            Profile.objects.create(user=user, role=user_role, is_rcic=is_rcic)
            messages.success(request, 'User added successfully.')
        return redirect('users')

    else:
        roles = Profile.ROLE_CHOICES
        users = User.objects.filter(is_staff=False)
        context = {
            'roles': roles,
            'users': users,
        }
        return render(request, 'users.html', context)


@login_required
def check_email(request):
    email = request.GET.get('email')
    if Applicant.objects.filter(email=email).exists():
        applicant = Applicant.objects.filter(email=email)
        return JsonResponse({'exists': True, 'client_id': [i.client_id for i in applicant]})
    return JsonResponse({'exists': False})


@login_required
def check_phone(request):
    phone = request.GET.get('phone')
    if Applicant.objects.filter(phone=phone).exists():
        applicant = Applicant.objects.filter(phone=phone)
        return JsonResponse({'exists': True, 'client_id': [i.client_id for i in applicant]})
    return JsonResponse({'exists': False})


@login_required
def add_applicant(request):
    if request.method == 'POST':
        f_name = request.POST.get('f_name')
        m_name = request.POST.get('m_name')
        l_name = request.POST.get('l_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        dob = request.POST.get('dob')
        application_type_id = request.POST.get('application_type')
        application_fee_amount = float(request.POST.get('application_fee'))
        biometric_fee_amount = float(request.POST.get('biometric_fee'))
        client_retained_amount = float(request.POST.get('amount_retained', 0))
        tax_amount = float(request.POST.get('taxes', 0))
        total_fee_amount = float(request.POST.get('total_fee', 0))
        balance_amount = float(request.POST.get('balance', 0))
        advance_amount = float(request.POST.get('advance', 0))
        r_f_name = request.POST.get('r_f_name')
        r_m_name = request.POST.get('r_m_name')
        r_l_name = request.POST.get('r_l_name')
        rcic_id = request.POST.get('rcic')

        application_type = Services.objects.get(id=application_type_id)
        rcic = Profile.objects.get(user__id=rcic_id).user

        now = datetime.now()
        timestamp = int(datetime.timestamp(now))
        client_id = f'R{timestamp}'

        new_applicant = Applicant(
            address=address,
            added_by=request.user,
            client_id=client_id,
            f_name=f_name,
            m_name=m_name,
            l_name=l_name,
            email=email,
            phone=phone,
            dob=dob,
            application_type=application_type.name,
            application_fee_amount=application_fee_amount,
            biometric_fee_amount=biometric_fee_amount,
            client_retained_amount=client_retained_amount,
            tax_amount=tax_amount,
            total_fee_amount=total_fee_amount,
            balance_amount=balance_amount,
            advance_amount=advance_amount,
            status="Pending",
            r_f_name=r_f_name,
            r_m_name=r_m_name,
            r_l_name=r_l_name,
            rcic=rcic
        )
        new_applicant.save()
        agreement = generate_agreement(new_applicant)
        new_applicant.service_agreement = agreement
        new_applicant.save()
        if advance_amount > 0:
            payment = Payments(
                applicant=new_applicant,
                added_by=request.user,
                amount=advance_amount
            )
            payment.save()

        if new_applicant.balance_amount == 0:
            new_applicant.payment_completed = True
            new_applicant.save()

        try:
            from decimal import Decimal
            from rio_imm.accounting.models import (
                Invoice as AccountingInvoice,
                InvoiceItem as AccountingInvoiceItem,
                TaxSlab,
                BusinessInfo,
            )

            business = BusinessInfo.get_current()
            today = date.today()
            due_date = today + timedelta(days=business.default_due_days)

            last_invoice = AccountingInvoice.objects.order_by('-id').first()
            if last_invoice and last_invoice.invoice_number:
                try:
                    inv_num = last_invoice.invoice_number
                    if inv_num.upper().startswith('RI'):
                        last_num = int(inv_num[3:])
                        invoice_number = f"RI{last_num + 1:05d}"
                    elif inv_num.upper().startswith('NB'):
                        last_num = int(inv_num[2:])
                        invoice_number = f"RI{last_num + 1:05d}"
                    else:
                        last_num = int(inv_num.split('-')[-1])
                        invoice_number = f"RI{last_num + 1:05d}"
                except Exception:
                    invoice_number = "RI000001"
            else:
                invoice_number = "RI000001"

            default_slab = TaxSlab.objects.filter(is_active=True, is_default=True).first()
            if default_slab:
                tax_rate = default_slab.rate
            elif new_applicant.application_fee_amount and new_applicant.tax_amount:
                try:
                    tax_rate = (
                        Decimal(str(new_applicant.tax_amount)) * Decimal('100.00')
                    ) / Decimal(str(new_applicant.application_fee_amount))
                except Exception:
                    tax_rate = Decimal('0.00')
            else:
                tax_rate = Decimal('0.00')

            auto_invoice = AccountingInvoice.objects.create(
                invoice_number=invoice_number,
                applicant=new_applicant,
                invoice_date=today,
                due_date=due_date,
                title='Invoice',
                summary=f'Initial invoice for {new_applicant.application_type or "application"}',
                po_number='',
                notes='',
                terms='',
                footer=getattr(business, 'default_footer', '') or '',
                tax_rate=tax_rate,
                created_by=request.user,
            )

            if new_applicant.application_fee_amount and new_applicant.application_fee_amount > 0:
                AccountingInvoiceItem.objects.create(
                    invoice=auto_invoice,
                    service=None,
                    description=f'Application fee for {new_applicant.application_type or "service"}',
                    quantity=Decimal('1.00'),
                    unit_price=Decimal(str(new_applicant.application_fee_amount)),
                    tax_rate=Decimal('0.00'),
                    is_taxable=True,
                )

            if new_applicant.biometric_fee_amount and new_applicant.biometric_fee_amount > 0:
                AccountingInvoiceItem.objects.create(
                    invoice=auto_invoice,
                    service=None,
                    description='Biometric fee',
                    quantity=Decimal('1.00'),
                    unit_price=Decimal(str(new_applicant.biometric_fee_amount)),
                    tax_rate=Decimal('0.00'),
                    is_taxable=False,
                )

            if new_applicant.client_retained_amount and new_applicant.client_retained_amount > 0:
                AccountingInvoiceItem.objects.create(
                    invoice=auto_invoice,
                    service=None,
                    description=f'Service fee for {new_applicant.application_type or "service"}',
                    quantity=Decimal('1.00'),
                    unit_price=Decimal(str(new_applicant.client_retained_amount)),
                    tax_rate=Decimal('0.00'),
                    is_taxable=False,
                )

            auto_invoice.discount_amount = Decimal('0.00')
            auto_invoice.calculate_totals()
        except Exception:
            pass

        checklists = CheckList.objects.filter(services=application_type)
        for checklist in checklists:
            CheckListAssignment.objects.create(
                item=checklist,
                applicant=new_applicant,
                assigned_by=request.user
            )

        messages.success(request,
                         f'Applicant added successfully. Client ID is {new_applicant.client_id}.')
        return redirect('add_applicant')

    rcic = Profile.objects.filter(is_rcic=True)
    services_type = Services.objects.filter(is_active=True)
    return render(request, 'add_applicant.html', {'services': services_type, 'rcic': rcic})

@login_required
def view_applicant(request, id):
    applicant = get_object_or_404(Applicant, id=id)
    payments = Payments.objects.filter(applicant=applicant)
    comments = Comments.objects.filter(applicant=applicant)
    services = Services.objects.all()

    checklist_assignments = CheckListAssignment.objects.filter(applicant=applicant)


    applicant_fields = [
        {"label": "First Name", "value": applicant.f_name, "type": "text"},
        {"label": "Middle Name", "value": applicant.m_name, "type": "text"},
        {"label": "Last Name", "value": applicant.l_name, "type": "text"},
        {"label": "Email", "value": applicant.email, "type": "email"},
        {"label": "Phone Number", "value": applicant.phone, "type": "tel"},
        {"label": "Address", "value": applicant.address, "type": "textarea"},
        {"label": "Date of Birth", "value": applicant.dob, "type": "text"},
        {"label": "Application Type", "value": applicant.application_type, "type": "text"},
        {"label": "Amount Client Retained At (CAD)", "value": applicant.client_retained_amount, "type": "number"},
        {"label": "Taxes 13%", "value": applicant.tax_amount, "type": "number"},
        {"label": "Application Fee", "value": applicant.application_fee_amount, "type": "number"},
        {"label": "Biometric Fee", "value": applicant.biometric_fee_amount, "type": "number"},
        {"label": "Total Fee", "value": applicant.total_fee_amount, "type": "number"},
        {"label": "Advance Collected", "value": applicant.advance_amount, "type": "number"},
        {"label": "Balance Amount", "value": applicant.balance_amount, "type": "number"},
        {"label": "Status", "value": applicant.status, "type": "text"}
    ]
    if applicant.uci_number:
        applicant_fields.append({"label": "UCI Number", "value": applicant.uci_number, "type": "text"})
    if applicant.application_number:
        applicant_fields.append({"label": "Application Number", "value": applicant.application_number, "type": "text"})
    if applicant.application_expiry:
        applicant_fields.append({"label": "Application/Visa Expiry", "value": applicant.application_expiry, "type": "text"})

    select_fields = [
        {
            "label": "Biometrics",
            "name": "biometrics_request",
            "value": applicant.biometrics_request,
            "options": [
                {"value": "Letter sent", "display": "Request Letter sent to client"},
                {"value": "Completed", "display": "Biometrics Completed"}
            ]
        },
        {
            "label": "Medical",
            "name": "medical_request",
            "value": applicant.medical_request,
            "options": [
                {"value": "Letter sent", "display": "Request Letter sent to client"},
                {"value": "Completed", "display": "Medical Completed"}
            ]
        }
    ]

    context = {
        'applicant': applicant,
        'payments': payments,
        'comments': comments,
        'services': services,
        'checklist_assignments': checklist_assignments,
        'applicant_fields': applicant_fields,
        'select_fields': select_fields,
    }
    return render(request, 'view_applicant.html', context)

@login_required
def delete_applicant(request):
    if request.method == "POST":
        id = request.POST['id']
        applicant = get_object_or_404(Applicant, id=id)
        if applicant:
            applicant.delete()
            messages.success(request, "Application deleted Successfully!")
        else:
            messages.success(request, "Something went wrong :)")
    return redirect(request.META.get('HTTP_REFERER') or dashboard)


@login_required
def edit_applicant(request, id):
    applicant = get_object_or_404(Applicant, id=id)
    comments = Comments.objects.filter(applicant=applicant)
    checklist_assignments = CheckListAssignment.objects.filter(applicant=applicant)

    if request.method == 'POST':
        # Update checklist assignments
        selected_checklists = request.POST.getlist('checklists')
        for assignment in checklist_assignments:
            if str(assignment.id) in selected_checklists:
                assignment.completed = True
            else:
                assignment.completed = False
            assignment.save()

        # Add a new comment if provided
        comment_text = request.POST.get('add_comment')
        if comment_text:
            Comments.objects.create(
                applicant=applicant,
                added_by=request.user,
                comment=comment_text
            )

        # Handle status updates in priority order
        if request.POST.get('approval') == 'approved':
            applicant.is_approved = True
            applicant.status = "Approved"
            send_status_notification(applicant, "Approved", request.user)

        elif request.POST.get('approval') == 'rejected':
            applicant.is_rejected = True
            applicant.status = "Rejected"
            send_status_notification(applicant, "Rejected", request.user)

        elif request.POST.get('submitted'):
            applicant.submitted = True
            applicant.status = "Submitted"
            send_status_notification(applicant, "Submitted", request.user)

        elif request.POST.get('ready_to_submit'):
            applicant.ready_to_submit = True
            applicant.status = "Ready To Submit"
            send_status_notification(applicant, "Application Ready to submit", request.user)

        elif request.POST.get('ready_to_review'):
            applicant.ready_to_review = True
            applicant.status = "Ready For Review"
            send_status_notification(applicant, "Ready for Review", request.user)

        elif applicant.ready_to_review and not request.POST.get('ready_to_review'):
            applicant.ready_to_review = False
            applicant.status = "Changes Required"
            send_status_notification(applicant, "Changes Required", request.user)

        elif request.POST.get('backed_out'):
            applicant.is_backedout = True
            applicant.status = "Backed out"

        # Update biometrics and medical-related statuses only if explicitly changed
        biometrics_request = request.POST.get('biometrics_request')
        if biometrics_request and biometrics_request != applicant.biometrics_request:
            applicant.biometrics_request = biometrics_request
            if biometrics_request == "Letter sent":
                applicant.status = "Biometrics Letter sent to client"
            elif biometrics_request == "Completed":
                applicant.status = "Biometrics Completed"

        medical_request = request.POST.get('medical_request')
        if medical_request and medical_request != applicant.medical_request:
            applicant.medical_request = medical_request
            if medical_request == "Letter sent":
                applicant.status = "Medical Letter sent to client"
            elif medical_request == "Completed":
                applicant.status = "Medical Completed"

        # Update other fields
        if request.POST.get('application_number'):
            applicant.application_number = request.POST.get('application_number')
        if request.POST.get('uci_number'):
            applicant.uci_number = request.POST.get('uci_number')
        if request.POST.get('application_expiry'):
            applicant.application_expiry = request.POST.get('application_expiry')

        applicant.service_agreement_check = bool(request.POST.get('service_agreement_check'))
        applicant.save()

        return redirect('edit_applicant', id=applicant.id)

    applicant_fields = [
        {"label": "First Name", "value": applicant.f_name, "type": "text"},
        {"label": "Middle Name", "value": applicant.m_name, "type": "text"},
        {"label": "Last Name", "value": applicant.l_name, "type": "text"},
        {"label": "Email", "value": applicant.email, "type": "email"},
        {"label": "Phone Number", "value": applicant.phone, "type": "tel"},
        {"label": "Address", "value": applicant.address, "type": "textarea"},
        {"label": "Date of Birth", "value": applicant.dob, "type": "text"},
        {"label": "Application Type", "value": applicant.application_type, "type": "text"},
        {"label": "Amount Client Retained At (CAD)", "value": applicant.client_retained_amount, "type": "number"},
        {"label": "Taxes 13%", "value": applicant.tax_amount, "type": "number"},
        {"label": "Application Fee", "value": applicant.application_fee_amount, "type": "number"},
        {"label": "Biometric Fee", "value": applicant.biometric_fee_amount, "type": "number"},
        {"label": "Total Fee", "value": applicant.total_fee_amount, "type": "number"},
        {"label": "Advance Collected", "value": applicant.advance_amount, "type": "number"},
        {"label": "Balance Amount", "value": applicant.balance_amount, "type": "number"},
        {"label": "Status", "value": applicant.status, "type": "text"}
    ]
    if applicant.uci_number:
        applicant_fields.append({"label": "UCI Number", "value": applicant.uci_number, "type": "text"})
    if applicant.application_number:
        applicant_fields.append({"label": "Application Number", "value": applicant.application_number, "type": "text"})
    if applicant.application_expiry:
        applicant_fields.append({"label": "Application/Visa Expiry", "value": applicant.application_expiry, "type": "text"})

    select_fields = [
        {
            "label": "Biometrics",
            "name": "biometrics_request",
            "value": applicant.biometrics_request,
            "options": [
                {"value": "Letter sent", "display": "Request Letter sent to client"},
                {"value": "Completed", "display": "Biometrics Completed"}
            ]
        },
        {
            "label": "Medical",
            "name": "medical_request",
            "value": applicant.medical_request,
            "options": [
                {"value": "Letter sent", "display": "Request Letter sent to client"},
                {"value": "Completed", "display": "Medical Completed"}
            ]
        }
    ]

    context = {
        'applicant': applicant,
        'comments': comments,
        'checklist_assignments': checklist_assignments,
        'applicant_fields': applicant_fields,
        'select_fields': select_fields,
    }
    return render(request, 'edit_applicant.html', context)


def send_status_notification(applicant, status, current_user):
    """Helper function to send email notifications for status changes"""
    recipients_email = [applicant.rcic.email]

    # Add caseworker email for certain statuses
    if status in ["Changes Required", "Ready To Submit", "Submitted", "Approved", "Rejected"]:
        caseworker_email = CaseWorkerAssignment.objects.get(applicant=applicant).caseworker.email
        recipients_email.append(caseworker_email)

    # Add manager emails
    managers_email = list(
        Profile.objects.filter(role__in=["manager", "admin"]).values_list('user__email', flat=True)
    )
    recipients_email.extend(managers_email)

    # Remove current user's email if present
    if current_user.email in recipients_email:
        recipients_email.remove(current_user.email)

    email_body = f"""
    The following applicant's status has been updated to <b>{status}</b>:<br><br>
    <b>Client ID:</b> {applicant.client_id}<br>
    <b>Applicant Name:</b> {applicant.f_name} {applicant.m_name} {applicant.l_name}<br>
    <b>Email:</b> {applicant.email}<br>
    <b>Phone:</b> {applicant.phone}<br>
    <b>Date of Birth:</b> {applicant.dob}<br>
    <b>Address:</b> {applicant.address}<br><br>

    Please log in to the system to review the details and proceed with the necessary actions.<br><br>
    """

    NotificationService.send_email_notification(f"{status} - {applicant}", email_body, recipients_email)


@login_required
def add_payment(request):
    if request.method == 'POST':
        # Get the current URL
        current_url = request.get_full_path()

        applicant_id = request.POST.get('applicant_id')
        amount = float(request.POST.get('amount'))
        adjustment = float(request.POST.get('adjustAmount'))
        # Fetch the applicant and validate the amount
        applicant = get_object_or_404(Applicant, id=applicant_id)
        balance = applicant.balance_amount

        if amount > balance:
            messages.error(request, 'Payment amount cannot be greater than the balance.')
            return redirect(current_url)  # Redirect back to the current page

        # If the amount is valid, create a new payment record
        if amount > 0:
            payment = Payments.objects.create(
                applicant=applicant,
                added_by=request.user,
                amount=amount,
            )

        if adjustment > 0:
            applicant.balance_amount -= adjustment
            applicant.total_fee_amount -= adjustment
            applicant.save()
            payment = Payments.objects.create(
                applicant=applicant,
                added_by=request.user,
                amount=(-adjustment),
                payment_method="Adjustment"
            )


        # Update the applicant's balance
        applicant.balance_amount -= amount

        # If the balance is now 0, mark the payment as completed
        if applicant.balance_amount <= 0:
            applicant.payment_completed = True

        # Save the updated applicant record
        applicant.save()

        messages.success(request, 'Payment added successfully.')
        return redirect(current_url)  # Redirect back to the current page

    return redirect('dashboard')


@login_required
def dashboard(request):
    if request.user.profile.role == 'frontdesk':
        return redirect('/frontdesk-dashboard')
    elif request.user.profile.role == 'caseworker':
        return redirect('/caseworker-dashboard')
    elif request.user.profile.role == 'manager':
        return redirect('/manager-dashboard')
    elif request.user.profile.role == 'accountant':
        return redirect('/accountant-dashboard')
    elif request.user.profile.role == 'admin':
        return redirect('/admin-dashboard')


@login_required
def frontdesk_dashboard(request):
    applicants = Applicant.objects.filter(submitted=False)
    context = {
        'applications': applicants
    }
    return render(request, 'dashboards/frontdesk_dashboard.html', context)


@login_required
def caseworker_dashboard(request):
    assigned_list = CaseWorkerAssignment.objects.filter(caseworker=request.user).values_list('applicant_id', flat=True)
    applicants = Applicant.objects.filter(id__in=assigned_list)
    total_applicants = applicants.count()
    pending_applicants = applicants.filter(submitted=False)
    today_date = date.today()
    today_applicants = applicants.annotate(added_at_date=TruncDate('added_at')).filter(added_at_date=today_date).count()
    context = {
        'pending_applicants': pending_applicants.count(),
        'total_applicants': total_applicants,
        'today_applicants': today_applicants,
        'applications': pending_applicants
    }
    return render(request, 'dashboards/caseworker_dashboard.html', context)


@login_required
def manager_dashboard(request):
    applicants = Applicant.objects.all()
    total_applicants = applicants.count()
    today_date = date.today()
    today_applicants = applicants.annotate(added_at_date=TruncDate('added_at')).filter(added_at_date=today_date).count()
    pending_applicants = Applicant.objects.filter(submitted=False)
    unassigned_applicants = Applicant.objects.filter(assignments__isnull=True)
    caseworkers = Profile.objects.filter(role__in=['caseworker', 'manager', 'admin'])

    context = {
        'pending_applicants_count': pending_applicants.count(),
        'total_applicants': total_applicants,
        'today_applicants': today_applicants,
        "pending_applicants": pending_applicants,
        "unassigned_applicants": unassigned_applicants,
        "caseworkers": caseworkers
    }

    return render(request, 'dashboards/admin_dashboard.html', context)


@login_required
def accountant_dashboard(request):
    return render(request, 'dashboards/admin_dashboard.html')


@login_required
def admin_dashboard(request):
    # checklists = CheckList.objects.filter(services__id=1)
    # check_list_file = services_checklist(checklists, "service.name")
    applicants = Applicant.objects.all()
    total_applicants = applicants.count()
    today_date = date.today()
    today_applicants = applicants.annotate(added_at_date=TruncDate('added_at')).filter(added_at_date=today_date).count()
    pending_applicants = Applicant.objects.filter(submitted=False)
    unassigned_applicants = Applicant.objects.filter(assignments__isnull=True)
    caseworkers = Profile.objects.filter(role__in=['caseworker', 'manager', 'admin'])

    context = {
        'pending_applicants_count': pending_applicants.count(),
        'total_applicants': total_applicants,
        'today_applicants': today_applicants,
        "pending_applicants": pending_applicants,
        "unassigned_applicants": unassigned_applicants,
        "caseworkers": caseworkers
    }

    return render(request, 'dashboards/admin_dashboard.html', context)


@login_required
def reports(request):
    # Extracting filters from GET request
    start_date = request.GET.get('report_start_date')
    end_date = request.GET.get('report_end_date')
    caseworker_id = request.GET.get('report_caseworker')
    application_status = request.GET.get('search_application_status')

    # Initialize query filters
    filters = Q(is_backedout=False)

    # Date range filter
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            filters &= Q(added_at__date__range=[start_date, end_date])
        except ValueError:
            # Handle invalid date formats
            pass

    # Application status filter
    if application_status == 'pending':
        filters &= Q(submitted=False)
    elif application_status == 'submitted':
        filters &= Q(submitted=True)

    # Caseworker filter
    if caseworker_id:
        filters &= Q(assignments__caseworker__id=caseworker_id)

    # Query for reports
    total_applications = Applicant.objects.filter(filters).count()
    completed_applications = Applicant.objects.filter(filters, submitted=True).count()
    pending_applications = Applicant.objects.filter(filters, submitted=False).count()
    total_amount = Applicant.objects.filter(filters).aggregate(total_amount=Sum('total_fee_amount'))['total_amount']
    pending_balance = Applicant.objects.filter(filters).aggregate(pending_balance=Sum('balance_amount'))['pending_balance']
    backed_out = Applicant.objects.filter(is_backedout=True).count()
    adjustment_amount = Payments.objects.filter(payment_method="Adjustment", applicant__is_backedout=False).aggregate(adjustment_amount=Sum('amount'))['adjustment_amount']
    # Fetch all caseworkers for the dropdown list
    caseworkers = Profile.objects.filter(role__in=['caseworker', 'admin', 'manager'])

    context = {
        'total_applications': total_applications,
        'completed_applications': completed_applications,
        'pending_applications': pending_applications,
        'total_amount': total_amount,
        'pending_balance': pending_balance,
        'caseworkers': caseworkers,  # Pass caseworkers to template
        'today': datetime.today().strftime('%Y-%m-%d'),
        'backed_out': backed_out,
        'adjustment_amount': abs(adjustment_amount or 0),
    }

    return render(request, 'reports.html', context)


@login_required
def export_applicants_csv(request):
    if request.method == "POST":
        start_date = request.POST.get('report_start_date')
        end_date = request.POST.get('report_end_date')
        caseworker_id = request.POST.get('report_caseworker')
        application_status = request.POST.get('search_application_status')

        # Initialize query filters
        filters = Q()

        # Date range filter
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                filters &= Q(added_at__date__range=[start_date, end_date])
            except ValueError:
                # Handle invalid date formats
                pass

        # Application status filter
        if application_status == 'pending':
            filters &= Q(submitted=False)
        elif application_status == 'submitted':
            filters &= Q(submitted=True)

        # Caseworker filter
        if caseworker_id:
            filters &= Q(assignments__caseworker__id=caseworker_id)

        queryset = Applicant.objects.filter(filters)
        dataset = ApplicantResource().export(queryset)

        # Create an HttpResponse for CSV
        response = HttpResponse(dataset.csv, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="applicants.csv"'

        return response

    caseworkers = Profile.objects.filter(role__in=['caseworker', 'admin', 'manager'])

    context = {
        'caseworkers': caseworkers,
        'today': datetime.today().strftime('%Y-%m-%d'),
    }

    return render(request, 'export.html', context)

