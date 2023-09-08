from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from loans.models import Loan, LoanRepayment


@admin.register(Loan)
class LoansAdmin(CompareVersionAdmin):
    pass


@admin.register(LoanRepayment)
class LoanRepaymentsAdmin(CompareVersionAdmin):
    pass
