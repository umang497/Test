from django.conf.urls import url

from loans.views import create_loan_request, make_repayment, get_user_loans, get_loan_details, get_pending_loans, \
    submit_loan_evaluation, get_repayment_schedule

urlpatterns = [
    url(r'request/$', create_loan_request, name='create_loan_request'),
    url(r'list/$', get_user_loans, name='get_user_loans'),
    url(r'list/pending/$', get_pending_loans, name='get_pending_loans'),
    url(r'evaluate/$', submit_loan_evaluation, name='submit_loan_evaluation'),
    url(r'repay/$', make_repayment, name='make_repayment'),
    url(r'(?P<loan_id>[-a-zA-Z0-9]+)/$', get_loan_details, name='get_loan_details'),
    url(r'(?P<loan_id>[-a-zA-Z0-9]+)/repayment-schedule/$', get_repayment_schedule, name='get_repayment_schedule'),
]
