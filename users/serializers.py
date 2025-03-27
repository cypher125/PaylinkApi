from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from .models import VTPassTransaction

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password_confirm', 
                  'first_name', 'last_name', 'phone_number', 'date_of_birth',
                  'address', 'state', 'bank_name', 'account_number', 'account_name',
                  'bvn', 'preferred_network')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # Remove password_confirm as it's not part of the User model
        validated_data.pop('password_confirm')
        
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data.get('phone_number', ''),
            date_of_birth=validated_data.get('date_of_birth'),
            address=validated_data.get('address', ''),
            state=validated_data.get('state', ''),
            bank_name=validated_data.get('bank_name', ''),
            account_number=validated_data.get('account_number', ''),
            account_name=validated_data.get('account_name', ''),
            bvn=validated_data.get('bvn', ''),
            preferred_network=validated_data.get('preferred_network', '')
        )
        
        user.set_password(validated_data['password'])
        user.save()
        
        # Here we would integrate with VTPass to create a test account
        # This will be handled in the views
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for retrieving user information"""
    kyc_level = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                  'phone_number', 'date_of_birth', 'address', 'state',
                  'vtpass_account_id', 'vtpass_balance', 'preferred_network',
                  'bank_name', 'account_number', 'account_name', 'bvn', 'occupation',
                  'account_status', 'kyc_level', 'date_joined', 'has_pin')
        read_only_fields = ('id', 'email', 'vtpass_account_id', 'vtpass_balance',
                           'kyc_level', 'date_joined', 'has_pin')


class UserPinSerializer(serializers.ModelSerializer):
    """Serializer for setting up user PIN"""
    pin = serializers.CharField(required=True, min_length=4, max_length=6)
    pin_confirm = serializers.CharField(required=True, min_length=4, max_length=6)
    
    class Meta:
        model = User
        fields = ('pin', 'pin_confirm')
    
    def validate(self, attrs):
        if attrs['pin'] != attrs['pin_confirm']:
            raise serializers.ValidationError({"pin": "PIN fields didn't match."})
        return attrs
    
    def update(self, instance, validated_data):
        instance.pin = validated_data['pin']
        instance.has_pin = True
        instance.save()
        return instance


class VTPassTransactionSerializer(serializers.ModelSerializer):
    """Serializer for VTPass transactions"""
    class Meta:
        model = VTPassTransaction
        fields = ('id', 'transaction_type', 'service_id', 'amount', 'phone_number',
                  'email', 'request_id', 'vtpass_reference', 'status', 
                  'response_data', 'created_at')
        read_only_fields = ('id', 'request_id', 'vtpass_reference', 'status', 
                           'response_data', 'created_at')
