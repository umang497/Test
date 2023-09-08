from datetime import datetime
from typing import Optional

from django.db import models, transaction
from reversion import revisions as reversion

from userman.models import User
from utils.models import BaseUUIDModel, RecurrenceFrequency
from utils.validators import validate_positive, validate_non_negative


class LoanCurrency(models.TextChoices):
    INR = ("INR", "Indian Rupee")


class LoanApprovalStatus(models.TextChoices):
    PENDING = ("PENDING", "PENDING")
    APPROVED = ("APPROVED", "APPROVED")
    REJECTED = ("REJECTED", "REJECTED")


class Loan(BaseUUIDModel):
    customer = models.ForeignKey(User, on_delete=models.PROTECT)
    # The internal team member who approved or rejected the loan application.
    evaluated_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='+')

    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[validate_non_negative])
    # How much money is left to be repaid. Until the loan is paid, this amount is 0.
    amount_due = models.DecimalField(default=0, max_digits=12, decimal_places=2, validators=[validate_positive])

    currency = models.CharField(max_length=3, choices=LoanCurrency.choices, default=LoanCurrency.INR)

    # Some checkpoints in the Loan's lifecycle
    evaluation_date = models.DateTimeField(blank=True, null=True)
    disbursement_date = models.DateTimeField(blank=True, null=True)
    closure_date = models.DateTimeField(blank=True, null=True)  # Date when the loan was Paid Out

    term = models.PositiveSmallIntegerField()
    repayment_frequency = models.PositiveSmallIntegerField(
        choices=RecurrenceFrequency.choices, default=RecurrenceFrequency.WEEKLY)

    approval_status = models.CharField(
        max_length=20, choices=LoanApprovalStatus.choices, default=LoanApprovalStatus.PENDING)

    def has_been_paid_back(self) -> bool:
        if self.amount_due == 0:
            return True
        return False

    @transaction.atomic()
    def approve(self, approved_by):
        self.evaluated_by = approved_by
        self.approval_status = LoanApprovalStatus.APPROVED
        self.evaluation_date = datetime.now()
        self.amount_due = self.loan_amount
        # For now, keeping the disbursal and approval_date same.
        self.disbursement_date = self.evaluation_date
        self.save(update_fields=
                  ["approval_status", "evaluated_by", "evaluation_date", "disbursement_date", "modified", "amount_due"]
                  )
        from loans.helpers import create_loan_repayment_schedule
        create_loan_repayment_schedule(loan=self)

    def reject(self, rejected_by):
        self.evaluated_by = rejected_by
        self.approval_status = LoanApprovalStatus.REJECTED
        self.evaluation_date = datetime.now()
        self.save(update_fields=["approval_status", "evaluated_by", "evaluation_date", "modified"])

    @property
    def upcoming_repayment(self) -> Optional['LoanRepayment']:
        if self.has_been_paid_back():
            return None
        return self.loanrepayment_set.filter(status=LoanRepaymentStatus.PENDING).order_by('due_date').first()

    def update_amount_due(self, paid_amount):
        self.amount_due = self.amount_due - paid_amount
        if self.has_been_paid_back():
            self.closure_date = datetime.now()
        self.save()


reversion.register(Loan)


class LoanRepaymentStatus(models.TextChoices):
    PENDING = ("PENDING", "PENDING")
    PAID = ("PAID", "PAID")
    CANCELLED = ("CANCELLED", "CANCELLED")
    PREPAID = ("PREPAID", "PREPAID")


class LoanRepayment(BaseUUIDModel):
    loan = models.ForeignKey(Loan, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[validate_non_negative])

    due_date = models.DateTimeField(blank=True, null=True)      # When is the repayment due?
    repayment_date = models.DateTimeField(blank=True, null=True)    # When was repayment made?

    status = models.CharField(max_length=20, choices=LoanRepaymentStatus.choices, default=LoanRepaymentStatus.PENDING)

    # Payment request that was generated to complete the repayment.
    # Note: We are not storing the Payment id here, as a payment request can be
    # fulfilled by multiple payments. Think partial payments or insufficient funds
    # during clawback.
    # For simplicity, keeping this a char field and not Foreign Key.
    payment_request_id = models.CharField(max_length=40, null=True, blank=True)

    @transaction.atomic()
    def mark_paid(self, with_amount=None):
        self.repayment_date = datetime.now()
        self.status = LoanRepaymentStatus.PAID
        if with_amount:
            self.amount = with_amount
        self.save()
        self.loan.update_amount_due(self.amount)


reversion.register(LoanRepayment)
