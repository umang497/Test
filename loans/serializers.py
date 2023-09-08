from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from loans.models import Loan, LoanRepayment, LoanApprovalStatus


class LoanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ["customer", "loan_amount", "term"]


class LoanEvaluationSerializer(serializers.ModelSerializer):
    approval_status = serializers.ChoiceField(required=True, choices=LoanApprovalStatus.choices)

    class Meta:
        model = Loan
        fields = ["evaluated_by", "evaluation_date", "approval_status"]

    def validate_evaluated_by(self, evaluated_by):
        # Some application level checks for the evaluator.
        # Like we do not want the evaluator to approve their own loans.
        if evaluated_by.id == self.instance.customer.id:
            raise ValidationError('User not permitted to approve this loan')


class LoanDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Loan
        fields = [
            "id", "loan_amount", "amount_due", "disbursement_date",
            "closure_date", "term", "repayment_frequency", "approval_status"
        ]


class LoanRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRepayment
        fields = '__all__'
