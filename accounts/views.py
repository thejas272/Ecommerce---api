from rest_framework.response import Response
from rest_framework import status
from accounts import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated,DjangoModelPermissions
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from accounts.throttles import LoginRateThrottle, RefreshTokenRateThrottle
from accounts.helpers import create_audit_log
from accounts import models
from common.pagination import DefaultPagination
from django.db.models import Q
from common.swagger import ID_PARAM,IS_ACTIVE_PARAM,IS_STAFF_PARAM,DATE_FROM_PARAM,DATE_TO_PARAM,SEARCH_PARAM,U_ID_PARAM,MODEL_PARAM,ACTION_PARAM,OBJECT_ID_PARAM
from accounts.filters.admin_users import admin_filter_users
from accounts.filters.admin_logs import admin_filter_logs
from rest_framework import serializers as drf_serializers

# Create your views here.



class RegisterAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.RegsiterSerializer

    @swagger_auto_schema(tags=['Authentication'])
    def post(self,request):

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class LoginAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]
    serializer_class = serializers.LoginSerializer

    @swagger_auto_schema(tags=['Authentication'])
    def post(self,request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            if user:
                try:
                    refresh = RefreshToken.for_user(user)
                    access = refresh.access_token
                except Exception:
                    return Response({"detail":"Login failed. Please try again."},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                action = "LOGIN"
                message = f"{user.username} logged in."
                create_audit_log(user=user,action=action,instance=user,message=message)

                return Response({"Refresh":str(refresh),
                                 "Access":str(access)
                                },status=status.HTTP_200_OK
                                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LogoutAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.LogoutSerializer

    @swagger_auto_schema(tags=['Authentication'])
    def post(self,request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            
            action = "LOGOUT"
            message = f"{request.user.username} logged out."
            create_audit_log(user=request.user,action=action,instance=request.user,message=message)

            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(status=status.HTTP_400_BAD_REQUEST)



class RefreshTokenAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [RefreshTokenRateThrottle]
    serializer_class = serializers.RefreshTokenSerializer

    @swagger_auto_schema(tags=['Authentication'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            refresh = serializer.validated_data["refresh_token"]

            access = refresh.access_token
            return Response({"Access":str(access)},
                            status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ProfileApiView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return serializers.UpdateProfileSerializer
        return serializers.ProfileSerializer
        

    @swagger_auto_schema(tags=['User'])
    def get(self,request):
        serializer = self.get_serializer(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(tags=['User'])
    def patch(self,request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class UpdatePasswordAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UpdatePasswordSerializer

    @swagger_auto_schema(tags=['User'])
    def patch(self,request):
        serializer = self.serializer_class(request.user, data=request.data, context={"request":request})

        if serializer.is_valid():
            serializer.save()
            return Response({"detail":"Password changed successfully."},status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    


class UserListAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated,DjangoModelPermissions]
    serializer_class = serializers.UserSerializer
    queryset = models.User.objects.all()
    pagination_class = DefaultPagination

    @swagger_auto_schema(tags=['Admin'],
                         manual_parameters=[ID_PARAM,SEARCH_PARAM,IS_STAFF_PARAM,IS_ACTIVE_PARAM,DATE_FROM_PARAM,DATE_TO_PARAM]
                        )
    def get(self,request):
        users = self.get_queryset().order_by('-date_joined')

        try:
            users = admin_filter_users(request,users)
        except drf_serializers.ValidationError as e:
            return Response({"detail":e.detail}, status=status.HTTP_400_BAD_REQUEST)


        paginator = self.pagination_class()
        page = paginator.paginate_queryset(users,request)

        serializer = self.serializer_class(page, many=True)


        return paginator.get_paginated_response(serializer.data)
    




class AuditLogListAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated,DjangoModelPermissions]
    serializer_class = serializers.AuditLogSerializer
    queryset = models.AuditLog.objects.all()
    pagination_class = DefaultPagination

    @swagger_auto_schema(tags=['Admin'],
                         manual_parameters=[ID_PARAM,U_ID_PARAM,ACTION_PARAM,DATE_FROM_PARAM,DATE_TO_PARAM,SEARCH_PARAM,MODEL_PARAM,OBJECT_ID_PARAM]
                        )
    def get(self,request):
        logs = self.get_queryset()

        try:
            logs = admin_filter_logs(request,logs)
        except drf_serializers.ValidationError as e:
            return Response({"detail":e.detail},status=status.HTTP_400_BAD_REQUEST)

        paginator = self.pagination_class()
        page =paginator.paginate_queryset(logs,request)

        serializer = self.serializer_class(page, many=True)

        return paginator.get_paginated_response(serializer.data)
    