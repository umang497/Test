# Generated by Django 3.1.14 on 2023-09-08 14:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import utils.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('loan_amount', models.DecimalField(decimal_places=2, max_digits=12, validators=[utils.validators.validate_non_negative])),
                ('amount_due', models.DecimalField(decimal_places=2, default=0, max_digits=12, validators=[utils.validators.validate_positive])),
                ('currency', models.CharField(choices=[('INR', 'Indian Rupee')], default='INR', max_length=3)),
                ('evaluation_date', models.DateTimeField(blank=True, null=True)),
                ('disbursement_date', models.DateTimeField(blank=True, null=True)),
                ('closure_date', models.DateTimeField(blank=True, null=True)),
                ('term', models.PositiveSmallIntegerField()),
                ('repayment_frequency', models.PositiveSmallIntegerField(choices=[(7, 'Weekly')], default=7)),
                ('approval_status', models.CharField(choices=[('PENDING', 'PENDING'), ('APPROVED', 'APPROVED'), ('REJECTED', 'REJECTED')], default='PENDING', max_length=20)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('evaluated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LoanRepayment',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, validators=[utils.validators.validate_non_negative])),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('repayment_date', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'PENDING'), ('PAID', 'PAID'), ('CANCELLED', 'CANCELLED'), ('PREPAID', 'PREPAID')], default='PENDING', max_length=20)),
                ('payment_request_id', models.CharField(blank=True, max_length=40, null=True)),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='loans.loan')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
