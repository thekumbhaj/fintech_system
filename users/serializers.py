"""
Serializers for User model
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'password_confirm',
            'phone_number',
            'first_name',
            'last_name',
            'date_of_birth',
        ]
    
    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        """Create user"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    full_name = serializers.CharField(read_only=True)
    is_kyc_verified = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone_number',
            'first_name',
            'last_name',
            'full_name',
            'kyc_status',
            'is_kyc_verified',
            'date_of_birth',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'kyc_status', 'created_at', 'updated_at']


class KYCSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for KYC submission"""
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'document_type',
            'document_number',
            'document_expiry',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'postal_code',
            'country',
        ]
    
    def validate(self, attrs):
        """Validate KYC data"""
        required_fields = ['first_name', 'last_name', 'date_of_birth', 'document_type', 
                          'document_number', 'address_line1', 'city', 'country']
        
        for field in required_fields:
            if not attrs.get(field):
                raise serializers.ValidationError({field: "This field is required for KYC."})
        
        return attrs
    
    def update(self, instance, validated_data):
        """Update user with KYC data and mark as submitted"""
        from django.utils import timezone
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.kyc_status = User.KYCStatus.IN_REVIEW
        instance.kyc_submitted_at = timezone.now()
        instance.save()
        
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    """Detailed serializer for user profile"""
    full_name = serializers.CharField(read_only=True)
    is_kyc_verified = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone_number',
            'first_name',
            'last_name',
            'full_name',
            'kyc_status',
            'is_kyc_verified',
            'kyc_submitted_at',
            'kyc_verified_at',
            'date_of_birth',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'postal_code',
            'country',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'kyc_status',
            'kyc_submitted_at',
            'kyc_verified_at',
            'created_at',
            'updated_at',
        ]
