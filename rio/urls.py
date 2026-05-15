from django.urls import path

from .decorators import role_required
from .views import *

urlpatterns = [
    path('', welcome),
    path('login', login, name='login'),
    path('logout', logout, name='logout'),

    path('dashboard', dashboard, name='dashboard'),
    path('frontdesk-dashboard', role_required('frontdesk')(frontdesk_dashboard), name='frontdesk_dashboard'),
    path('caseworker-dashboard', role_required('caseworker')(caseworker_dashboard), name='caseworker_dashboard'),
    path('manager-dashboard', role_required('manager')(manager_dashboard), name='manager_dashboard'),
    path('accountant-dashboard', role_required('accountant')(accountant_dashboard), name='accountant_dashboard'),
    path('admin-dashboard', role_required('admin')(admin_dashboard), name='admin_dashboard'),

    path('add-applicant', role_required('admin', 'manager', 'frontdesk')(add_applicant), name="add_applicant"),
    path('check-email', check_email, name="check_email"),
    path('check-phone', check_phone, name="check_phone"),

    path('users', role_required('admin')(users), name="users"),

    path('settings', settings, name="settings"),
    path('my-applications', role_required('admin', 'caseworker', 'manager')(my_applications), name="my_applications"),

    path('ready-for-review', role_required('admin', 'manager')(ready_for_review), name="ready_for_review"),
    path('pending-applications', role_required('admin', 'manager', 'caseworker')(pending_applications), name="pending_applications"),
    path('submitted-applications', role_required('admin', 'manager', 'caseworker')(submitted_applications),
         name='submitted_applications'),
    path('unassigned-applications', role_required('admin', 'manager')(unassigned_applications), name='unassigned_applications'),
    path('assign-caseworker', role_required('admin', 'manager')(assign_caseworker), name='assign_caseworker'),
    path('completed-applications', role_required('admin', 'caseworker', 'manager')(completed_applications), name="completed_applications"),
    path('accepted-applications', role_required('admin', 'manager')(accepted_applications), name="accepted_applications"),
    path('rejected-applications', role_required('admin', 'manager')(rejected_applications), name="rejected_applications"),
    path('search-applications', search_applications, name="search_applications"),

    path('services', services, name="services"),
    path('get-service-checklist/', get_service_checklist, name='get_service_checklist'),

    path('check-list', role_required('admin', 'manager')(check_list), name="check_list"),
    path('deactivate-service', role_required('admin')(deactivate_service), name="deactivate_service"),

    path('applicant/<int:id>', view_applicant, name="view_applicant"),
    path('applicant/<int:id>/edit', role_required('admin', 'caseworker', 'manager')(edit_applicant), name="edit_applicant"),
    path('delete-applicant', role_required('admin')(delete_applicant), name="delete_applicant"),
    path('add-payment', role_required('admin', 'manager')(add_payment),
         name="add_payment"),

    path('reports', role_required('admin', 'manager')(reports), name="reports"),
    path('export-applicants', role_required('admin', 'manager')(export_applicants_csv), name='export_applicants'),

    # Accounting Urls
    path('', role_required('accountant', 'admin', 'manager')(accountant_dashboard), name='accountant_dashboard'),

]
