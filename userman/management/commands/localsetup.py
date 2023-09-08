from django.core.management import BaseCommand
from django.db import transaction

from userman.models import User, UserLevel


class Command(BaseCommand):
    def create_customers(self):
        for i in range(20, 26):
            User.objects.create_user(
                username=f'customer{i}',
                password=f'customerpass{i}',
                phone_number=f'98765432{i}',
                name=f'Customer {i}'
            )

    def create_admins(self):
        for i in range(21, 23):
            User.objects.create_user(
                username=f'admin{i}',
                password=f'adminpass{i}',
                phone_number=f'98765432{i}',
                name=f'Admin {i}',
                user_level=UserLevel.ADMIN
            )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Creating super user(use username: Super1 and password: superpass for django admin')
        User.objects.create_superuser(
            username="Super2", password="superpass", phone_number=f'9876543210', name=f'Super Man')

        self.stdout.write('Creating some customers:')
        self.create_customers()

        self.stdout.write('Creating some admins')
        self.create_admins()
