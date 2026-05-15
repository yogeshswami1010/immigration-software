from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Applicant, Payments, Comments, Services, Profile, CaseWorkerAssignment, CheckList, \
    CheckListAssignment
from import_export.admin import ExportMixin

class ApplicantAdmin(ExportMixin, SimpleHistoryAdmin):
    list_display = ('client_id', 'id', 'f_name', 'm_name', 'l_name', 'email', 'phone', 'dob', 'application_type', 'ready_to_submit', 'submitted', 'payment_completed', 'status')
    search_fields = ('client_id', 'f_name', 'l_name', 'email', 'phone', 'application_type', 'status')
    list_filter = ('ready_to_submit', 'submitted', 'payment_completed', 'status')

    def save_model(self, request, obj, form, change):
        obj._history_user = request.user
        super().save_model(request, obj, form, change)


class PaymentsAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'id', 'added_by', 'added_at', 'amount')
    search_fields = ('applicant__client_id', 'applicant__f_name', 'applicant__l_name', 'added_by__username')
    list_filter = ('added_at',)


class CommentsAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'id', 'added_by', 'added_at', 'comment')
    search_fields = ('applicant__client_id', 'applicant__f_name', 'applicant__l_name', 'added_by__username', 'comment')
    list_filter = ('added_at',)


class ServicesAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'application_fee', 'bio_metric_fee')
    search_fields = ('name',)
    list_filter = ('application_fee', 'bio_metric_fee')


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'id', 'role', 'is_rcic')
    search_fields = ('user',)
    list_filter = ('role',)


class CheckListAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'added_at', 'added_by', )
    search_fields = ('name',)
    list_filter = ('services',)


class CheckListAssignmentAdmin(admin.ModelAdmin):
    list_display = ('item', 'applicant', 'id', 'assigned_by', 'added_at', 'completed')
    search_fields = ('item', 'applicant')


class CaseWorkerAssignmentAdmin(admin.ModelAdmin):
    list_display = ('caseworker', 'id', 'applicant', 'assigned_by', 'assigned_at')
    search_fields = ('caseworker', 'applicant')
    list_filter = ('caseworker',)


admin.site.register(Applicant, ApplicantAdmin)
admin.site.register(Payments, PaymentsAdmin)
admin.site.register(Comments, CommentsAdmin)
admin.site.register(Services, ServicesAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(CaseWorkerAssignment, CaseWorkerAssignmentAdmin)
admin.site.register(CheckList, CheckListAdmin)
admin.site.register(CheckListAssignment, CheckListAssignmentAdmin)
