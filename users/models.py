from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser and includes
    additional fields for VTPass integration.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pin = models.CharField(max_length=6, blank=True, null=True)
    
    # VTPass related fields
    vtpass_account_id = models.CharField(max_length=100, blank=True, null=True)
    vtpass_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    preferred_network = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    account_name = models.CharField(max_length=200, blank=True, null=True)
    bvn = models.CharField(max_length=20, blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    has_pin = models.BooleanField(default=False)
    account_status = models.CharField(max_length=20, default='active', choices=[
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('inactive', 'Inactive')
    ])
    
    # Make email the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username is still required by Django
    
    def __str__(self):
        return self.email
    
    @property
    def kyc_level(self):
        """
        Determine KYC level based on available user information
        Level 1: Basic registration
        Level 2: Has provided BVN
        """
        if self.bvn:
            return 2
        return 1


class VTPassTransaction(models.Model):
    """
    Model to store VTPass transactions for each user
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=50)  # e.g., 'airtime', 'data', 'electricity', etc.
    service_id = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    request_id = models.CharField(max_length=100, unique=True)  # VTPass request ID
    vtpass_reference = models.CharField(max_length=100, blank=True, null=True)  # VTPass reference
    status = models.CharField(max_length=20, default='pending')  # pending, successful, failed
    response_data = models.JSONField(blank=True, null=True)  # Store the complete response from VTPass
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount}"
