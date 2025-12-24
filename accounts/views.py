from rest_framework.response import Response
from rest_framework import status
from accounts import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema

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
    serializer_class = serializers.LoginSerializer
    @swagger_auto_schema(tags=['Authentication'])

    def post(self,request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            if user:
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                return Response({"Refresh":str(refresh),
                                 "Access":str(access)
                                },status=status.HTTP_200_OK
                                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    



class RefreshTokenAPIView(GenericAPIView):
    permission_classes = [AllowAny]
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