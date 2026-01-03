from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from carts import serializers
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
# Create your views here.


class AddToCartAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.AddToCartSerializer

    @swagger_auto_schema(tags=["Cart"])
    def post(self,request):
        
        serializer = self.serializer_class(data=request.data, context={"request":request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)