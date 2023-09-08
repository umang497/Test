from decimal import Decimal

from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes

from loans.helpers import rebalance_loan_repayment_schedule
from loans.models import LoanApprovalStatus, Loan, LoanRepayment, LoanRepaymentStatus
from userman.permissions.loans import ApplyLoanPermission, ManageLoanPermission
from .serializers import LoanCreateSerializer, LoanDetailsSerializer, LoanEvaluationSerializer, LoanRepaymentSerializer


# ------------------ Customer endpoints ------------------

@api_view(['POST'])
@permission_classes([ApplyLoanPermission, ])
@authentication_classes([BasicAuthentication])
def create_loan_request(request) -> JsonResponse:
    # Validating the request.
    request_data = request.data.copy()
    request_data.update({'customer': request.user.id})
    serializer = LoanCreateSerializer(data=request_data)
    if not serializer.is_valid():
        return JsonResponse(
            {'message': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer.save()
    read_serializer = LoanDetailsSerializer(instance=serializer.instance)
    return JsonResponse(read_serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
# Do we really need authentication here? We can allow anyone to repay the loan.
@authentication_classes([BasicAuthentication])
def make_repayment(request) -> JsonResponse:
    if not request.data.get('loan_id'):
        return JsonResponse(
            {'message': "loan_id is a required field."},
            status=status.HTTP_400_BAD_REQUEST
        )
    with transaction.atomic():
        try:
            # Let's lock the loan object to avoid concurrent balance updates.
            loan = Loan.objects.select_for_update(nowait=True
                                                  ).get(id=request.data.get('loan_id'), customer=request.user)
            if loan.has_been_paid_back():
                return JsonResponse(
                    {'message': "Trying to pay for an already closed loan."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Loan.DoesNotExist:
            return JsonResponse(
                {'message': 'Loan Not Found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if not request.data.get('amount'):
            return JsonResponse(
                {'message': "amount is a required field."},
                status=status.HTTP_400_BAD_REQUEST
            )
        amount = Decimal(request.data.get('amount'))
        if amount > loan.amount_due:
            return JsonResponse(
                {'message': "Trying to pay more than the due amount."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Note: If there is a due amount, there must be at least one pending repayment.
        elif amount < loan.upcoming_repayment.amount:
            return JsonResponse(
                {'message': f"Minimum acceptable amount is {loan.upcoming_repayment.amount}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif amount > loan.upcoming_repayment.amount:
            loan.upcoming_repayment.mark_paid(with_amount=amount)
            rebalance_loan_repayment_schedule(loan)
        else:
            loan.upcoming_repayment.mark_paid(with_amount=amount)
    return JsonResponse(LoanDetailsSerializer(instance=loan).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
def get_user_loans(request) -> JsonResponse:
    loans = Loan.objects.filter(customer=request.user).order_by('disbursement_date')
    return JsonResponse(
        {'loans': [LoanDetailsSerializer(instance=loan).data for loan in loans]},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
def get_loan_details(request, loan_id) -> JsonResponse:
    try:
        loan = Loan.objects.get(id=loan_id, customer=request.user)
    except Loan.DoesNotExist:
        return JsonResponse(
            {'message': 'Loan Not Found'},
            status=status.HTTP_404_NOT_FOUND
        )
    return JsonResponse(LoanDetailsSerializer(instance=loan).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
def get_repayment_schedule(request, loan_id) -> JsonResponse:
    try:
        loan = Loan.objects.get(id=loan_id, customer=request.user)
    except Loan.DoesNotExist:
        return JsonResponse(
            {'message': 'Loan Not Found'},
            status=status.HTTP_404_NOT_FOUND
        )
    loan_repayments = LoanRepayment.objects.filter(loan=loan).exclude(status=LoanRepaymentStatus.PREPAID)
    return JsonResponse(
        {'repayments': [LoanRepaymentSerializer(instance=repayment).data for repayment in loan_repayments]},
        status=status.HTTP_200_OK)

# ------------------ Internal Team endpoints ------------------


@api_view(['GET'])
@permission_classes([ManageLoanPermission, ])
@authentication_classes([BasicAuthentication])
def get_pending_loans(request) -> JsonResponse:
    pending_loans = Loan.objects.filter(status=LoanApprovalStatus.PENDING).order_by('created')
    return JsonResponse(
        {'pending_loans': [LoanDetailsSerializer(instance=loan).data for loan in pending_loans]},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([ManageLoanPermission, ])
@authentication_classes([BasicAuthentication])
def submit_loan_evaluation(request) -> JsonResponse:
    if not request.data.get('loan_id'):
        return JsonResponse(
            {'message': "loan_id is a required field."},
            status=status.HTTP_400_BAD_REQUEST
        )
    with transaction.atomic():
        try:
            # Let's lock the loan object, we do not want multiple schedules getting created for the same loan.
            loan = Loan.objects.select_for_update(nowait=True).get(id=request.data.get('loan_id'))
        except Loan.DoesNotExist:
            return JsonResponse(
                {'message': 'Loan Not Found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if loan.approval_status != LoanApprovalStatus.PENDING:
            return JsonResponse(
                {'message': 'Cannot approve loan if it is not pending.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request_data = request.data.copy()
        request_data.update({'evaluated_by': request.user.id})
        serializer = LoanEvaluationSerializer(instance=loan, data=request_data)
        if not serializer.is_valid():
            return JsonResponse(
                {'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        if serializer.validated_data['approval_status'] == LoanApprovalStatus.APPROVED:
            loan.approve(approved_by=request.user)
        elif serializer.validated_data['approval_status'] == LoanApprovalStatus.REJECTED:
            loan.reject(rejected_by=request.user)
    read_serializer = LoanDetailsSerializer(instance=loan)
    return JsonResponse(read_serializer.data, status=status.HTTP_200_OK)
