from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView
)
from rest_framework.response import Response
from rest_framework import status
from .views import (
    RegisterView,
    UserProfileView,
    SetPINView,
    VTPassBalanceView,
    VTPassServicesView,
    VTPassPurchaseView,
    VTPassTransactionStatusView,
    UserTransactionsView,
    DashboardStatsView,
    UserKYCStatusView,
    UserSerializer,
    FundWalletView,
    CheckPaymentStatusView,
)
from drf_spectacular.utils import extend_schema

# Extend schema for JWT token views
@extend_schema(
    tags=["Authentication"],
    description="Obtain JWT token pair by providing username and password",
)
class ExtendedTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            
            # Add user info to the response
            if request.user.is_authenticated:
                user = request.user
            else:
                # Get user from provided credentials
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                user = serializer.user
                
            # Include user profile data in the response
            response.data['user'] = UserSerializer(user).data
            return response
            
        except Exception as e:
            # Handle unexpected errors gracefully
            print(f"Login error: {str(e)}")
            return Response(
                {"detail": "Login failed. Please try again."},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=["Authentication"],
    description="Refresh access token using refresh token",
)
class ExtendedTokenRefreshView(TokenRefreshView):
    pass


urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', ExtendedTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', ExtendedTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    
    # User profile endpoints
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('set-pin/', SetPINView.as_view(), name='set-pin'),
    path('kyc-status/', UserKYCStatusView.as_view(), name='kyc-status'),
    
    # Dashboard stats endpoint
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    
    # VTPass endpoints
    path('balance/', VTPassBalanceView.as_view(), name='vtpass-balance'),
    path('services/<str:service_type>/', VTPassServicesView.as_view(), name='vtpass-services'),
    path('purchase/', VTPassPurchaseView.as_view(), name='vtpass-purchase'),
    path('transaction-status/<str:request_id>/', VTPassTransactionStatusView.as_view(), name='vtpass-transaction-status'),
    path('transactions/', UserTransactionsView.as_view(), name='user-transactions'),
    
    # Wallet funding endpoints
    path('fund-wallet/', FundWalletView.as_view(), name='fund-wallet'),
    path('payment-status/<str:transaction_reference>/', CheckPaymentStatusView.as_view(), name='payment-status'),
]
