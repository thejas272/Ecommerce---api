from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from carts import serializers
from carts import models as cart_models
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from common.pagination import DefaultPagination
# Create your views here.


class CartListCreateAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.AddToCartSerializer
        return serializers.CartListSerializer

    @swagger_auto_schema(tags=["Cart"])
    def post(self,request):
        
        serializer = self.get_serializer(data=request.data, context={"request":request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    @swagger_auto_schema(tags=["Cart"])
    def get(self,request):
        cart_items = cart_models.CartModel.objects.filter(user=request.user).select_related("product","product__brand","product__category").order_by('-created_at')

        paginator = self.pagination_class() 
        page = paginator.paginate_queryset(cart_items,request)


        serializer = self.get_serializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)
        
    



class CartItemAPIView(GenericAPIView):
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
    
    
    @swagger_auto_schema(tags=["Cart"])
    def delete(self,request,id):
        try:
            cart_item = cart_models.CartModel.objects.get(id=id,user=request.user)
        except cart_models.CartModel.DoesNotExist:
            return Response({"detail":"Invalid cart id."},status=status.HTTP_404_NOT_FOUND)
        
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


