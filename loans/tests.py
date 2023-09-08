import base64
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from loans.models import Loan, LoanApprovalStatus, LoanRepayment, LoanRepaymentStatus
from userman.models import User, UserLevel
from utils.models import RecurrenceFrequency


def get_basic_auth_header(user, password):
    """
    Return a dict containing the correct headers to set to make HTTP Basic Auth request
    """
    user_pass = f"{user}:{password}"
    auth_string = base64.b64encode(user_pass.encode("utf-8"))
    auth_headers = {
        "HTTP_AUTHORIZATION": "Basic " + auth_string.decode("utf-8"),
    }
    return auth_headers


def create_loan_payload(loan_amount=100, term=5):
    return {
        'loan_amount': loan_amount,
        'term': term
    }


def evaluate_loan_payload(loan_id=None, approval_status=LoanApprovalStatus.APPROVED):
    return {
        'loan_id': loan_id,
        'approval_status': approval_status
    }


def repay_loan_payload(loan_id=None, amount=20):
    return {
        'loan_id': loan_id,
        'amount': amount
    }


class LoanFlowsTests(TestCase):
    def create_user(self, username, password, name, phone_number) -> User:
        self.client.post(
            path=reverse('register_user'),
            data={
                'username': username,
                'password': password,
                'name': name,
                'phone_number': phone_number
            }
        )
        return User.objects.get(username=username)

    def setUp(self):
        super().__init__()
        self.customer_1 = self.create_user("customer1", "customer1pass", "Bruce Wayne", "9876543211")
        self.customer_2 = self.create_user("customer2", "customer2pass", "Alfred", "9876543212")
        self.admin1 = self.create_user("admin1", "admin1pass", "Shark", "8876543212")
        self.admin1.user_level = UserLevel.ADMIN
        self.admin1.save()
        self.admin2 = self.create_user("admin2", "admin2pass", "Fish", "8876543213")
        self.admin2.user_level = UserLevel.ADMIN
        self.admin2.save()

    def test_unauthenticated_create_loan(self):
        auth_headers = get_basic_auth_header("customer1", "wrong_password")
        response = self.client.post(
            path=reverse('create_loan_request'),
            data=create_loan_payload(),
            **auth_headers
        )
        self.assertEquals(response.status_code, 401)
        self.assertEquals(response.json(), {'detail': 'Invalid username/password.'})

    def test_banned_user_create_loan(self):
        self.customer_1.user_level = UserLevel.BANNED
        self.customer_1.save()

        auth_headers = get_basic_auth_header("customer1", "customer1pass")
        response = self.client.post(
            path=reverse('create_loan_request'),
            data=create_loan_payload(),
            **auth_headers
        )
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.json(), {'detail': 'You do not have permission to perform this action.'})

    def test_create_loan_successful(self):
        auth_headers = get_basic_auth_header("customer1", "customer1pass")
        response = self.client.post(
            path=reverse('create_loan_request'),
            data=create_loan_payload(),
            **auth_headers
        )
        self.assertEquals(response.status_code, 201)
        loan = Loan.objects.get(customer=self.customer_1)
        self.assertEquals(loan.approval_status, LoanApprovalStatus.PENDING)
        self.assertEquals(Decimal(loan.amount_due), Decimal(0))
        self.assertEquals(Decimal(loan.loan_amount), Decimal(100))
        self.assertEquals(loan.repayment_frequency, RecurrenceFrequency.WEEKLY)
        self.assertEquals(loan.term, 5)
        self.assertEquals(LoanRepayment.objects.count(), 0)

    def test_create_loan_admin_user(self):
        auth_headers = get_basic_auth_header("admin1", "admin1pass")
        response = self.client.post(
            path=reverse('create_loan_request'),
            data=create_loan_payload(),
            **auth_headers
        )
        self.assertEquals(response.status_code, 201)
        loan = Loan.objects.get(customer=self.admin1)
        self.assertEquals(loan.approval_status, LoanApprovalStatus.PENDING)
        self.assertEquals(Decimal(loan.amount_due), Decimal(0))
        self.assertEquals(Decimal(loan.loan_amount), Decimal(100))
        self.assertEquals(loan.repayment_frequency, RecurrenceFrequency.WEEKLY)
        self.assertEquals(loan.term, 5)
        self.assertEquals(LoanRepayment.objects.count(), 0)

    def test_unauthorised_loan_details_access(self):
        # loan created by customer 1. But customer 2 and admin 1 try to access it.
        self.test_create_loan_successful()
        loan = Loan.objects.get()
        auth_headers = get_basic_auth_header("admin1", "admin1pass")
        response = self.client.get(
            path=reverse('get_loan_details', args=[loan.id]),
            **auth_headers
        )
        self.assertEquals(response.status_code, 404)
        self.assertEquals(response.json(), {'message': 'Loan Not Found'})

        auth_headers = get_basic_auth_header("customer2", "customer2pass")
        response = self.client.get(
            path=reverse('get_loan_details', args=[loan.id]),
            **auth_headers
        )
        self.assertEquals(response.status_code, 404)
        self.assertEquals(response.json(), {'message': 'Loan Not Found'})

    def test_authorised_loan_details_access(self):
        self.test_create_loan_successful()
        loan = Loan.objects.get()
        auth_headers = get_basic_auth_header("customer1", "customer1pass")
        response = self.client.get(
            path=reverse('get_loan_details', args=[loan.id]),
            **auth_headers
        )
        expected_response = {
            'amount_due': '0.00',
            'approval_status': 'PENDING',
            'closure_date': None,
            'disbursement_date': None,
            'id': str(loan.id),
            'loan_amount': '100.00',
            'repayment_frequency': 7,
            'term': 5
        }
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.json(), expected_response)

    def test_customer_trying_to_approve_loan(self):
        self.test_create_loan_successful()
        loan = Loan.objects.get()
        auth_headers = get_basic_auth_header("customer2", "customer2pass")
        response = self.client.post(
            path=reverse('submit_loan_evaluation'),
            data=evaluate_loan_payload(loan_id=loan.id),
            **auth_headers
        )
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.json(), {'detail': 'You do not have permission to perform this action.'})

    def test_admin_approve_loan(self):
        self.test_create_loan_successful()
        loan = Loan.objects.get()
        auth_headers = get_basic_auth_header("admin1", "admin1pass")
        response = self.client.post(
            path=reverse('submit_loan_evaluation'),
            data=evaluate_loan_payload(loan_id=loan.id),
            **auth_headers
        )
        self.assertEquals(response.status_code, 200)
        loan.refresh_from_db()
        self.assertEquals(loan.amount_due, loan.loan_amount)
        self.assertEquals(loan.approval_status, LoanApprovalStatus.APPROVED)
        self.assertIsNotNone(loan.disbursement_date)
        self.assertEquals(LoanRepayment.objects.count(), 5)
        for repayment in LoanRepayment.objects.filter(loan=loan):
            self.assertEquals(repayment.amount, 20)
            self.assertEquals(repayment.status, LoanRepaymentStatus.PENDING)

    def test_admin_reject_loan(self):
        self.test_create_loan_successful()
        loan = Loan.objects.get()
        auth_headers = get_basic_auth_header("admin1", "admin1pass")
        response = self.client.post(
            path=reverse('submit_loan_evaluation'),
            data=evaluate_loan_payload(loan_id=loan.id, approval_status=LoanApprovalStatus.REJECTED),
            **auth_headers
        )
        self.assertEquals(response.status_code, 200)
        loan.refresh_from_db()
        self.assertEquals(loan.amount_due, 0)
        self.assertEquals(loan.approval_status, LoanApprovalStatus.REJECTED)
        self.assertIsNone(loan.disbursement_date)
        self.assertEquals(LoanRepayment.objects.count(), 0)

    def test_admin_trying_to_evaluate_their_own_loan(self):
        self.test_create_loan_admin_user()
        loan = Loan.objects.get()
        auth_headers = get_basic_auth_header("admin1", "admin1pass")
        response = self.client.post(
            path=reverse('submit_loan_evaluation'),
            data=evaluate_loan_payload(loan_id=loan.id),
            **auth_headers
        )
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {'message': {'evaluated_by': ['User not permitted to approve this loan']}})

    def test_different_admin_approve_admin_loan(self):
        self.test_create_loan_successful()
        loan = Loan.objects.get()
        auth_headers = get_basic_auth_header("admin2", "admin2pass")
        response = self.client.post(
            path=reverse('submit_loan_evaluation'),
            data=evaluate_loan_payload(loan_id=loan.id),
            **auth_headers
        )
        self.assertEquals(response.status_code, 200)
        loan.refresh_from_db()
        self.assertEquals(loan.amount_due, loan.loan_amount)
        self.assertEquals(loan.approval_status, LoanApprovalStatus.APPROVED)
        self.assertIsNotNone(loan.disbursement_date)

    def test_approved_loan_unequal_installment(self):
        auth_headers = get_basic_auth_header("customer1", "customer1pass")
        self.client.post(
            path=reverse('create_loan_request'),
            data=create_loan_payload(loan_amount=100, term=7),
            **auth_headers
        )
        loan = Loan.objects.get()
        auth_headers = get_basic_auth_header("admin1", "admin1pass")
        self.client.post(
            path=reverse('submit_loan_evaluation'),
            data=evaluate_loan_payload(loan_id=loan.id),
            **auth_headers
        )
        # First 6 repayments have the same installment amount
        for repayment in LoanRepayment.objects.filter(loan=loan).order_by('due_date')[:6]:
            self.assertEquals(str(repayment.amount), '14.28')
            self.assertEquals(repayment.status, LoanRepaymentStatus.PENDING)

        # Excess installment is adjsuted with the last installment
        last_repayment = LoanRepayment.objects.filter(loan=loan).order_by('due_date').last()
        self.assertEquals(str(last_repayment.amount), '14.32')
        self.assertEquals(last_repayment.status, LoanRepaymentStatus.PENDING)

    def test_invalid_amount_repayment(self):
        self.test_admin_approve_loan()
        auth_headers = get_basic_auth_header("customer1", "customer1pass")
        loan = Loan.objects.get()
        response = self.client.post(
            path=reverse('make_repayment'),
            data=repay_loan_payload(loan_id=loan.id, amount=10),
            **auth_headers
        )
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {'message': 'Minimum acceptable amount is 20.00'})

        response = self.client.post(
            path=reverse('make_repayment'),
            data=repay_loan_payload(loan_id=loan.id, amount=500),
            **auth_headers
        )
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {'message': 'Trying to pay more than the due amount.'})

    def test_loan_repayment_exact_installment(self):
        self.test_admin_approve_loan()
        auth_headers = get_basic_auth_header("customer1", "customer1pass")
        loan = Loan.objects.get()
        response = self.client.post(
            path=reverse('make_repayment'),
            data=repay_loan_payload(loan_id=loan.id),
            **auth_headers
        )
        self.assertEquals(response.status_code, 200)
        loan.refresh_from_db()
        self.assertEquals(str(loan.amount_due), '80.00')
        repayments = LoanRepayment.objects.filter(loan=loan).order_by("due_date")
        self.assertEquals(repayments.first().status, LoanRepaymentStatus.PAID)
        self.assertIsNotNone(repayments.first().repayment_date)

        for repayment in repayments[1:]:
            self.assertEquals(repayment.status, LoanRepaymentStatus.PENDING)
            self.assertIsNone(repayment.repayment_date)

    def test_loan_repayment_more_than_installment(self):
        self.test_admin_approve_loan()
        auth_headers = get_basic_auth_header("customer1", "customer1pass")
        loan = Loan.objects.get()
        response = self.client.post(
            path=reverse('make_repayment'),
            data=repay_loan_payload(loan_id=loan.id, amount=35),
            **auth_headers
        )
        self.assertEquals(response.status_code, 200)
        loan.refresh_from_db()
        self.assertEquals(str(loan.amount_due), '65.00')
        repayments = LoanRepayment.objects.filter(loan=loan).order_by("due_date")
        self.assertEquals(repayments.first().status, LoanRepaymentStatus.PAID)
        self.assertEquals(str(repayments.first().amount), '35.00')
        self.assertIsNotNone(repayments.first().repayment_date)

        # Remaining repayments also got adjusted
        for repayment in repayments[1:]:
            self.assertEquals(repayment.status, LoanRepaymentStatus.PENDING)
            self.assertIsNone(repayment.repayment_date)
            self.assertEquals(str(repayment.amount), '16.25')

    def test_loan_payment_complete(self):
        self.test_admin_approve_loan()
        auth_headers = get_basic_auth_header("customer1", "customer1pass")
        loan = Loan.objects.get()
        for i in range(0, 5):
            self.assertIsNone(loan.closure_date)
            self.assertGreater(loan.amount_due, 0)
            self.client.post(
                path=reverse('make_repayment'),
                data=repay_loan_payload(loan_id=loan.id),
                **auth_headers
            )
        loan.refresh_from_db()
        self.assertEquals(loan.amount_due, 0)
        self.assertIsNotNone(loan.closure_date)
        self.assertEquals(LoanRepayment.objects.filter(loan=loan, status=LoanRepaymentStatus.PAID).count(), 5)
        self.assertEquals(LoanRepayment.objects.filter(loan=loan, status=LoanRepaymentStatus.PENDING).count(), 0)

        response = self.client.post(
                path=reverse('make_repayment'),
                data=repay_loan_payload(loan_id=loan.id),
                **auth_headers
            )
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {'message': 'Trying to pay for an already closed loan.'})
