from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    UserPinSerializer,
    VTPassTransactionSerializer
)
from .models import VTPassTransaction
from .vtpass import VTPassService
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.db.models import Sum
from datetime import datetime
from dateutil.relativedelta import relativedelta
import uuid
from django.db.utils import IntegrityError
import logging
from decimal import Decimal

User = get_user_model()
logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Authentication"],
    description="Register a new user and create a VTPass account",
    request={
        "type": "object",
        "properties": {
            "email": {"type": "string", "format": "email", "description": "User's email address"},
            "username": {"type": "string", "description": "Unique username"},
            "password": {"type": "string", "format": "password", "description": "User's password"},
            "password_confirm": {"type": "string", "format": "password", "description": "Confirm password"},
            "first_name": {"type": "string", "description": "User's first name"},
            "last_name": {"type": "string", "description": "User's last name"},
            "phone_number": {"type": "string", "description": "User's phone number (optional)"},
            "date_of_birth": {"type": "string", "format": "date", "description": "User's date of birth (optional)"},
            "address": {"type": "string", "description": "User's address (optional)"},
            "state": {"type": "string", "description": "User's state of residence (optional)"},
            "bank_name": {"type": "string", "description": "User's bank name (optional)"},
            "account_number": {"type": "string", "description": "User's bank account number (optional)"},
            "account_name": {"type": "string", "description": "User's bank account name (optional)"},
            "bvn": {"type": "string", "description": "User's Bank Verification Number (optional)"},
            "preferred_network": {"type": "string", "description": "User's preferred mobile network (optional)"}
        },
        "required": ["email", "username", "password", "password_confirm", "first_name", "last_name"]
    },
    responses={
        201: {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "username": {"type": "string"},
                        "email": {"type": "string"},
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "phone_number": {"type": "string"},
                        "vtpass_account_id": {"type": "string"},
                        "vtpass_balance": {"type": "number"}
                    }
                },
                "tokens": {
                    "type": "object",
                    "properties": {
                        "access": {"type": "string"},
                        "refresh": {"type": "string"}
                    }
                },
                "vtpass_account": {
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string"},
                        "balance": {"type": "number"}
                    }
                }
            }
        },
        400: {"description": "Bad request, invalid data"},
        409: {"description": "Username or email already exists"}
    }
)
class RegisterView(generics.CreateAPIView):
    """View for user registration"""
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create VTPass account for the user
        vtpass_service = VTPassService()
        vtpass_account = vtpass_service.create_vtpass_account(user)
        
        # Generate tokens for the user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'vtpass_account': vtpass_account,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["User Profile"],
    description="Retrieve and update user profile information"
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating user profile"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user


@extend_schema(
    tags=["User Profile"],
    description="Set or update user's PIN for transaction authorization",
    request=UserPinSerializer,
    responses={200: {"description": "PIN set successfully"}}
)
class SetPINView(generics.UpdateAPIView):
    """View for setting the user's PIN"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserPinSerializer
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'PIN set successfully',
            'user': UserSerializer(self.get_object()).data
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=["User Profile"],
    description="Retrieve user's KYC level and account status information",
    responses={200: {
        "type": "object",
        "properties": {
            "kyc_level": {"type": "integer", "description": "Current KYC level of the user"},
            "account_status": {"type": "string", "description": "Current account status"},
            "is_bvn_verified": {"type": "boolean", "description": "Whether user has provided BVN"},
            "requirements": {
                "type": "object",
                "properties": {
                    "next_level": {"type": "integer", "description": "Next KYC level"},
                    "missing_fields": {"type": "array", "description": "Fields needed for next level"}
                }
            }
        }
    }}
)
class UserKYCStatusView(APIView):
    """View for retrieving user's KYC level and account status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        kyc_level = user.kyc_level
        
        # Determine missing fields for next level
        missing_fields = []
        if kyc_level == 1:
            if not user.bvn:
                missing_fields.append("BVN")
        
        return Response({
            "kyc_level": kyc_level,
            "account_status": user.account_status,
            "is_bvn_verified": bool(user.bvn),
            "requirements": {
                "next_level": kyc_level + 1 if kyc_level < 2 else kyc_level,
                "missing_fields": missing_fields
            }
        })


@extend_schema(
    tags=["VTPass"],
    description="Get the current VTPass account balance",
    responses={
        200: {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Response code from VTPass"},
                "response_description": {"type": "string", "description": "Response description from VTPass"},
                "data": {
                    "type": "object",
                    "properties": {
                        "balance": {"type": "string", "description": "Current account balance"}
                    }
                }
            }
        },
        401: {"description": "Unauthorized, no valid token provided"},
        500: {"description": "Internal server error or VTPass service error"}
    }
)
class VTPassBalanceView(APIView):
    """View for retrieving the user's VTPass balance"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        vtpass_service = VTPassService()
        balance = vtpass_service.get_user_balance()
        
        return Response(balance)


@extend_schema(
    tags=["VTPass"],
    description="Get available services by type (e.g., airtime, data, electricity)",
    parameters=[
        OpenApiParameter(
            name="service_type",
            description="Type of service to retrieve",
            required=True,
            type=str,
            location=OpenApiParameter.PATH,
            examples=[
                OpenApiExample(
                    "Airtime",
                    summary="Get airtime services",
                    value="airtime"
                ),
                OpenApiExample(
                    "Data",
                    summary="Get data services",
                    value="data"
                ),
                OpenApiExample(
                    "Exam",
                    summary="Get education services",
                    value="education"
                ),
                OpenApiExample(
                    "Electricity",
                    summary="Get electricity services",
                    value="electricity"
                ),
            ]
        )
    ],
    responses={
        200: {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Response code from VTPass"},
                "response_description": {"type": "string", "description": "Response description from VTPass"},
                "content": {
                    "type": "object",
                    "properties": {
                        "serviceID": {"type": "string", "description": "Service identifier"},
                        "service_name": {"type": "string", "description": "Name of the service"},
                        "variations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "variation_code": {"type": "string", "description": "Code for this variation"},
                                    "name": {"type": "string", "description": "Name of the variation"},
                                    "price": {"type": "number", "description": "Price of the variation"},
                                    "variation_amount": {"type": "number", "description": "Amount for this variation"},
                                    "fixedPrice": {"type": "boolean", "description": "Whether the price is fixed"}
                                }
                            }
                        }
                    }
                }
            }
        },
        401: {"description": "Unauthorized, no valid token provided"},
        404: {"description": "Service type not found"},
        500: {"description": "Internal server error or VTPass service error"}
    }
)
class VTPassServicesView(APIView):
    """View for retrieving available VTPass services"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, service_type):
        vtpass_service = VTPassService()
        services = vtpass_service.get_services(service_type)
        
        return Response(services)


@extend_schema(
    tags=["VTPass"],
    description="Purchase a service through VTPass",
    request={
        "type": "object",
        "properties": {
            "service_id": {"type": "string", "description": "Service ID (e.g., mtn, airtel)"},
            "variation_code": {"type": "string", "description": "Variation code for the service"},
            "amount": {"type": "number", "description": "Amount to purchase"},
            "phone": {"type": "string", "description": "Recipient's phone number"},
            "email": {"type": "string", "format": "email", "description": "Email to receive receipt"},
            "pin": {"type": "string", "description": "User's PIN for authorization"},
            "transaction_type": {"type": "string", "description": "Type of transaction"},
            "auto_retry": {"type": "boolean", "description": "Whether to auto-retry the transaction"},
            "billersCode": {"type": "string", "description": "Biller's code for the service"},
            "billerscode": {"type": "string", "description": "Alternative biller's code for the service"},
            "billers_code": {"type": "string", "description": "Another alternative biller's code for the service"}
        },
        "required": ["service_id", "amount", "phone", "email", "pin"]
    },
    responses={
        200: {
            "type": "object",
            "properties": {
                "transaction": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "transaction_type": {"type": "string"},
                        "service_id": {"type": "string"},
                        "amount": {"type": "number"},
                        "phone_number": {"type": "string"},
                        "email": {"type": "string"},
                        "request_id": {"type": "string"},
                        "vtpass_reference": {"type": "string"},
                        "status": {"type": "string"},
                        "response_data": {"type": "object"}
                    }
                },
                "response": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "response_description": {"type": "string"},
                        "content": {"type": "object"}
                    }
                }
            }
        },
        400: {"description": "Bad request, invalid data or insufficient balance"},
        401: {"description": "Unauthorized, no valid token provided"},
        402: {"description": "Payment required, insufficient balance"},
        500: {"description": "Internal server error or VTPass service error"}
    }
)
class VTPassPurchaseView(APIView):
    """View for purchasing a service through VTPass"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        service_id = request.data.get('service_id')
        variation_code = request.data.get('variation_code')
        amount = request.data.get('amount')
        phone = request.data.get('phone')
        email = request.data.get('email')
        auto_retry = request.data.get('auto_retry', False)
        
        # Debug logging for JAMB-related fields
        print("=== VTPASS PURCHASE VIEW ===")
        print(f"All request data: {request.data}")
        print(f"billersCode: {request.data.get('billersCode')}")
        print(f"billerscode: {request.data.get('billerscode')}")
        print(f"billers_code: {request.data.get('billers_code')}")
        
        if not all([service_id, amount, phone, email]):
            return Response({
                'message': 'Missing required fields'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify PIN
        pin = request.data.get('pin')
        if not pin or pin != request.user.pin:
            return Response({
                'success': False,
                'message': 'Invalid PIN'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert amount to decimal for proper comparison
        try:
            amount_decimal = Decimal(str(amount))
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'message': 'Invalid amount'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if user has sufficient balance
        if Decimal(str(request.user.vtpass_balance)) < amount_decimal:
            return Response({
                'success': False,
                'message': 'Insufficient balance for this transaction',
                'required_amount': float(amount_decimal),
                'available_balance': float(request.user.vtpass_balance)
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        vtpass_service = VTPassService()
        
        # Get or generate request_id
        request_id = request.data.get('request_id', '')
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Check if a transaction with this request_id already exists
        try:
            existing_transaction = VTPassTransaction.objects.filter(request_id=request_id).first()
            if existing_transaction:
                # Return the existing transaction if it exists
                return Response({
                    'message': 'Transaction already exists',
                    'transaction': VTPassTransactionSerializer(existing_transaction).data,
                    'response': existing_transaction.response_data
                })
        except Exception as e:
            # Log the error but continue
            logger.error(f"Error checking for existing transaction: {str(e)}")
        
        # Create a transaction record
        transaction_type = request.data.get('transaction_type', 'purchase')
        
        # Generate a unique request ID
        new_request_id = f"REQ-{uuid.uuid4().hex[:10].upper()}"
        
        # Create a transaction record in our database
        transaction = VTPassTransaction.objects.create(
            user=request.user,
            transaction_type=transaction_type,
            service_id=service_id,
            amount=amount,
            phone_number=phone,
            email=email,
            request_id=new_request_id
        )
        
        # Make the purchase
        response = vtpass_service.purchase_service(
            service_id=service_id,
            variation_code=variation_code,
            amount=amount,
            phone=phone,
            email=email,
            request_id=request_id,
            auto_retry=auto_retry,
            # Add all service-specific parameters, especially for JAMB
            billersCode=request.data.get('billersCode'),
            # Also try alternative formats that might be in the request
            billerscode=request.data.get('billerscode'),
            billers_code=request.data.get('billers_code')
        )
        
        # Update the transaction record with the response
        transaction.response_data = response
        
        # Check for successful transaction: VTPass success codes include '000' and 'success'
        # Also consider 'delivered' status in the transaction content
        if (response.get('code') == 'success' or 
            response.get('code') == '000' or 
            response.get('code') == '01' or 
            (response.get('content', {}).get('transactions', {}).get('status') == 'delivered')):
            
            transaction.status = 'successful'
            # Get reference ID from appropriate location in response
            if 'data' in response:
                transaction.vtpass_reference = response.get('data', {}).get('reference_id')
            elif 'content' in response and 'transactions' in response.get('content', {}):
                transaction.vtpass_reference = response.get('content', {}).get('transactions', {}).get('product_name')
            
            # Deduct amount from user's balance
            request.user.vtpass_balance = Decimal(str(request.user.vtpass_balance)) - amount_decimal
            request.user.save()
        else:
            transaction.status = 'failed'
            
            # Enhanced error handling for specific VTPass error codes
            error_code = response.get('code')
            if error_code == '016':
                logger.warning(f"VTPass transaction failed with code 016. Request ID: {request_id}, Details: {response}")
                # Don't deduct balance for failed transactions
                
                # Add more context to the response for the frontend
                response['error_message'] = 'Transaction failed on the provider side. This could be due to network issues, invalid recipient number, or the service being temporarily unavailable.'
                response['suggested_action'] = 'Please try again after a few minutes or contact support if the issue persists.'
            elif error_code == '014':
                logger.warning(f"VTPass insufficient funds error. Request ID: {request_id}, Details: {response}")
                response['error_message'] = 'Insufficient funds in the VTPass account.'
                response['suggested_action'] = 'Please contact support to top up the VTPass account.'
            elif error_code == '009':
                logger.warning(f"VTPass duplicate request error. Request ID: {request_id}, Details: {response}")
                response['error_message'] = 'This appears to be a duplicate transaction request.'
                response['suggested_action'] = 'Please check if the previous transaction was successful before trying again.'
            else:
                logger.warning(f"VTPass unknown error. Code: {error_code}, Request ID: {request_id}, Details: {response}")
                response['error_message'] = 'An error occurred while processing your transaction.'
                response['suggested_action'] = 'Please try again or contact support for assistance.'
        
        transaction.save()
        
        return Response({
            'transaction': VTPassTransactionSerializer(transaction).data,
            'response': response
        })


@extend_schema(
    tags=["VTPass"],
    description="Check the status of a VTPass transaction",
    parameters=[
        OpenApiParameter(
            name="request_id",
            description="Transaction request ID",
            required=True,
            type=str,
            location=OpenApiParameter.PATH
        )
    ]
)
class VTPassTransactionStatusView(APIView):
    """View for checking the status of a VTPass transaction"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, request_id):
        try:
            transaction = VTPassTransaction.objects.get(request_id=request_id, user=request.user)
        except VTPassTransaction.DoesNotExist:
            return Response({
                'message': 'Transaction not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        vtpass_service = VTPassService()
        status_response = vtpass_service.verify_transaction(request_id)
        
        # Update the transaction record with the latest status
        if status_response.get('code') == 'success':
            transaction.status = 'successful'
            transaction.response_data = status_response
            transaction.save()
        
        return Response({
            'transaction': VTPassTransactionSerializer(transaction).data,
            'status': status_response
        })


@extend_schema(
    tags=["VTPass"],
    description="List all transactions for the current user",
    responses={200: VTPassTransactionSerializer(many=True)}
)
class UserTransactionsView(generics.ListAPIView):
    """View for listing a user's transactions"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VTPassTransactionSerializer
    
    def get_queryset(self):
        return VTPassTransaction.objects.filter(user=self.request.user).order_by('-created_at')


@extend_schema(
    tags=["Dashboard"],
    description="Get financial statistics for the dashboard",
    responses={
        200: {
            "type": "object",
            "properties": {
                "balance": {"type": "number", "description": "Current wallet balance"},
                "this_month_spent": {"type": "number", "description": "Total spent in current month"},
                "total_spent": {"type": "number", "description": "Total amount spent all time"},
                "recent_transactions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Transaction ID"},
                            "transaction_type": {"type": "string", "description": "Type of transaction"},
                            "service_id": {"type": "string", "description": "Service identifier"},
                            "amount": {"type": "number", "description": "Transaction amount"},
                            "phone_number": {"type": "string", "description": "Phone number if applicable"},
                            "email": {"type": "string", "description": "Email if applicable"},
                            "request_id": {"type": "string", "description": "Request ID"},
                            "vtpass_reference": {"type": "string", "description": "VTPass reference if applicable"},
                            "status": {"type": "string", "description": "Transaction status"},
                            "created_at": {"type": "string", "format": "date-time", "description": "Transaction timestamp"}
                        }
                    }
                }
            }
        },
        401: {"description": "Unauthorized, no valid token provided"},
        500: {"description": "Internal server error"}
    }
)
class DashboardStatsView(APIView):
    """View for retrieving financial dashboard statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get current date and first day of current month
        today = datetime.now()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        try:
            # Get real-time VTPass balance
            vtpass_service = VTPassService()
            vtpass_balance_response = vtpass_service.get_user_balance()
            
            # Extract balance from VTPass response
            balance = 0.00
            if isinstance(vtpass_balance_response, dict):
                balance_data = vtpass_balance_response.get('data', {})
                if isinstance(balance_data, dict):
                    balance_str = balance_data.get('balance', '0.00')
                    try:
                        balance = float(balance_str)
                    except (ValueError, TypeError):
                        balance = 0.00
            
            # Calculate this month's spending
            this_month_transactions = VTPassTransaction.objects.filter(
                user=user,
                created_at__gte=first_day_of_month,
                status='successful'  # This matches our model's status field values
            )
            this_month_spent = this_month_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Calculate total spending (all time)
            all_transactions = VTPassTransaction.objects.filter(
                user=user,
                status='successful'  # This matches our model's status field values
            )
            total_spent = all_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Get recent transactions (last 5)
            recent_transactions = VTPassTransaction.objects.filter(
                user=user
            ).order_by('-created_at')[:5]
            
            # Serialize transactions
            transaction_serializer = VTPassTransactionSerializer(recent_transactions, many=True)
            
            response_data = {
                'balance': float(balance),  # Convert Decimal to float for JSON serialization
                'this_month_spent': float(this_month_spent),  # Convert Decimal to float
                'total_spent': float(total_spent),  # Convert Decimal to float
                'recent_transactions': transaction_serializer.data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    tags=["Wallet"],
    description="Fund user wallet",
    request={
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "Amount to fund"},
            "payment_method": {
                "type": "string",
                "enum": ["bank_transfer", "card", "ussd"],
                "description": "Payment method to use"
            },
            "transaction_reference": {"type": "string", "description": "Optional transaction reference"}
        },
        "required": ["amount", "payment_method"]
    },
    responses={
        200: {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "description": "Whether the funding was successful"},
                "message": {"type": "string", "description": "Response message"},
                "transaction": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Transaction ID"},
                        "amount": {"type": "number", "description": "Transaction amount"},
                        "status": {"type": "string", "description": "Transaction status"},
                        "created_at": {"type": "string", "format": "date-time", "description": "Transaction timestamp"}
                    }
                },
                "updated_balance": {"type": "number", "description": "New wallet balance after funding"}
            }
        },
        400: {"description": "Bad request, invalid data"},
        401: {"description": "Unauthorized, no valid token provided"},
        402: {"description": "Payment failed"}
    }
)
class FundWalletView(APIView):
    """View for funding user wallet"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method')
        transaction_reference = request.data.get('transaction_reference', str(uuid.uuid4()))
        
        if not amount or not payment_method:
            return Response({
                'success': False,
                'message': 'Amount and payment method are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Convert amount to Decimal for proper handling
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'message': 'Invalid amount format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # For demo purposes:
        # - Bank transfer payments always succeed
        # - Other payment methods always fail
        if payment_method == 'bank_transfer':
            transaction_status = 'successful'
            success = True
            message = 'Wallet funded successfully'
            
            # Update user's balance - properly handle Decimal types
            user = request.user
            user.vtpass_balance = Decimal(str(user.vtpass_balance)) + amount
            user.save()
        else:
            transaction_status = 'failed'
            success = False
            message = 'Payment failed. Please try bank transfer instead.'
        
        # Create transaction record
        transaction = VTPassTransaction.objects.create(
            user=request.user,
            transaction_type='wallet_funding',
            service_id='wallet',
            amount=amount,
            email=request.user.email,
            request_id=transaction_reference,
            status=transaction_status,
            response_data={
                'payment_method': payment_method,
                'transaction_reference': transaction_reference
            }
        )
        
        return Response({
            'success': success,
            'message': message,
            'transaction': {
                'id': str(transaction.id),
                'amount': float(transaction.amount),
                'status': transaction.status,
                'created_at': transaction.created_at.isoformat()
            },
            'updated_balance': float(user.vtpass_balance)
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Wallet"],
    description="Check payment status",
    parameters=[
        OpenApiParameter(
            name="transaction_reference",
            description="Transaction reference to check",
            required=True,
            type=str,
            location=OpenApiParameter.PATH
        )
    ],
    responses={
        200: {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "description": "Whether the status check was successful"},
                "status": {"type": "string", "description": "Current transaction status"},
                "message": {"type": "string", "description": "Response message"},
                "transaction": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Transaction ID"},
                        "transaction_type": {"type": "string", "description": "Type of transaction"},
                        "service_id": {"type": "string", "description": "Service identifier"},
                        "amount": {"type": "number", "description": "Transaction amount"},
                        "phone_number": {"type": "string", "description": "Phone number if applicable"},
                        "email": {"type": "string", "description": "Email if applicable"},
                        "request_id": {"type": "string", "description": "Request ID"},
                        "vtpass_reference": {"type": "string", "description": "VTPass reference if applicable"},
                        "status": {"type": "string", "description": "Transaction status"},
                        "created_at": {"type": "string", "format": "date-time", "description": "Transaction timestamp"}
                    }
                }
            }
        },
        401: {"description": "Unauthorized, no valid token provided"},
        404: {"description": "Transaction not found"}
    }
)
class CheckPaymentStatusView(APIView):
    """View for checking payment status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, transaction_reference):
        try:
            transaction = VTPassTransaction.objects.get(
                request_id=transaction_reference,
                user=request.user
            )
            
            return Response({
                'success': True,
                'status': transaction.status,
                'message': 'Transaction status retrieved successfully',
                'transaction': VTPassTransactionSerializer(transaction).data
            })
        except VTPassTransaction.DoesNotExist:
            return Response({
                'success': False,
                'status': 'unknown',
                'message': 'Transaction not found'
            }, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=["Authentication"],
    description="Logout a user and blacklist their refresh token",
    request={
        "type": "object",
        "properties": {
            "refresh_token": {"type": "string", "description": "The refresh token to blacklist"}
        },
        "required": ["refresh_token"]
    },
    responses={
        205: {"description": "Successfully logged out"},
        400: {"description": "Bad request, invalid token"},
        401: {"description": "Unauthorized, no valid token provided"}
    }
)
class LogoutView(APIView):
    """View for logging out a user and blacklisting their refresh token"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Get the refresh token from the request data
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required for logout."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Blacklist the token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Return success response
            return Response(
                {"detail": "Successfully logged out."},
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            # Return error response
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
