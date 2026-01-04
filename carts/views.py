from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from carts import serializers
from carts import models as cart_models
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
    


class UpdateCartQuantityAPIVIew(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UpdateCartQuantitySerializer
    lookup_field = "id"

    @swagger_auto_schema(tags=["Cart"])
    def patch(self,request,id):
        try:
            cart_item = cart_models.CartModel.objects.get(id=id,user=request.user)
        except cart_models.CartModel.DoesNotExist:
            return Response({"detail":"Invalid Cart item id."},status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(cart_item,request.data, context={"request":request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)