"""
Views for user management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
import logging

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    KYCSubmissionSerializer,
    UserProfileSerializer,
)

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Allow anyone to register"""
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action in ['retrieve', 'me']:
            return UserProfileSerializer
        elif self.action == 'submit_kyc':
            return KYCSubmissionSerializer
        return UserSerializer
    
    def create(self, request, *args, **kwargs):
        """Register a new user"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        logger.info(f"New user registered: {user.email}")
        
        return Response(
            {
                'message': 'User registered successfully',
                'user': UserSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info(f"User profile updated: {request.user.email}")
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def submit_kyc(self, request):
        """Submit KYC information"""
        user = request.user
        
        # Check if already verified
        if user.kyc_status == User.KYCStatus.VERIFIED:
            return Response(
                {'error': 'KYC already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info(f"KYC submitted for user: {user.email}")
        
        return Response({
            'message': 'KYC submitted successfully and is under review',
            'kyc_status': user.kyc_status
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve_kyc(self, request, pk=None):
        """Approve user KYC (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can approve KYC'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        user.kyc_status = User.KYCStatus.VERIFIED
        user.kyc_verified_at = timezone.now()
        user.save()
        
        logger.info(f"KYC approved for user: {user.email} by {request.user.email}")
        
        return Response({
            'message': 'KYC approved successfully',
            'user': UserSerializer(user).data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject_kyc(self, request, pk=None):
        """Reject user KYC (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can reject KYC'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        user.kyc_status = User.KYCStatus.REJECTED
        user.save()
        
        logger.info(f"KYC rejected for user: {user.email} by {request.user.email}")
        
        return Response({
            'message': 'KYC rejected',
            'user': UserSerializer(user).data
        })
