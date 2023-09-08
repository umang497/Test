from decimal import Decimal, ROUND_DOWN

from django.db import transaction

from loans.models import Loan, LoanRepayment, LoanRepaymentStatus
from utils.helpers import recurrence_date_generator


def create_loan_repayment_schedule(loan: Loan):
    installment = Decimal(loan.loan_amount / loan.term).quantize(Decimal('.00'), ROUND_DOWN)
    loan_repayments = []
    repayment_dates = recurrence_date_generator(loan.disbursement_date, loan.repayment_frequency)
    for t in range(1, loan.term):
        loan_repayments.append(
            LoanRepayment(
                loan=loan,
                amount=installment,
                due_date=next(repayment_dates),
            )
        )
    # Creating the last installment separately to adjust for loan amount indivisible by loan term.
    installment = loan.loan_amount - (installment * (loan.term - 1))
    loan_repayments.append(
        LoanRepayment(
            loan=loan,
            amount=installment,
            due_date=next(repayment_dates),
        )
    )
    LoanRepayment.objects.bulk_create(loan_repayments)


@transaction.atomic()
def rebalance_loan_repayment_schedule(loan: Loan):
    if not loan.amount_due:
        # create proper exception class.
        raise Exception('Why are we re-balancing if no balance is due?')
    pending_repayments = LoanRepayment.objects.filter(loan=loan, status=LoanRepaymentStatus.PENDING).order_by('due_date')
    new_installment = Decimal(loan.amount_due / pending_repayments.count()).quantize(Decimal('.00'), ROUND_DOWN)
    repayment = None
    for repayment in pending_repayments:
        repayment.amount = new_installment

    # Updating the last installment separately to adjust for due amount indivisible by remaining repayments.
    repayment.amount = loan.amount_due - (new_installment * (pending_repayments.count() - 1))
    LoanRepayment.objects.bulk_update(pending_repayments, ["amount", "modified"])
