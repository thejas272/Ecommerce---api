from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from carts import serializers
from carts import models as cart_models
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from common.pagination import DefaultPagination
from common.helpers import success_response,error_response,normalize_validation_errors
from rest_framework import serializers as drf_serializers
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

        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return success_response(message = "Product added to cart successfully.",
                                        data    = serializer.data,
                                        status_code = status.HTTP_201_CREATED
                                    )
        except drf_serializers.ValidationError as e:
            message,data = normalize_validation_errors(e.detail)
            return error_response(message = message,
                                  data    = data,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
    

    @swagger_auto_schema(tags=["Cart"])
    def get(self,request):
        cart_items = cart_models.CartModel.objects.filter(user=request.user).select_related("product","product__brand","product__category").order_by('-created_at')

        paginator = self.pagination_class() 
        page = paginator.paginate_queryset(cart_items,request)


        serializer = self.get_serializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)
        
    



class CartItemAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    @swagger_auto_schema(tags=["Cart"])
    def delete(self,request,id):
        try:
            cart_item = cart_models.CartModel.objects.get(id=id,user=request.user)
        except cart_models.CartModel.DoesNotExist:
            return error_response(message = "Invalid cart id.",
                                  data    = {"cart_id":id},
                                  status_code = status.HTTP_404_NOT_FOUND
                                 )
        
        cart_item.delete()
        return success_response(message = "Crat item deleted successfuly.",
                                data    = {"cart_id":id},
                                status_code = status.HTTP_204_NO_CONTENT
                               )
    


class CartItemQuantityAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UpdateCartQuantitySerializer
    lookup_field = "id"


    @swagger_auto_schema(tags=["Cart"])
    def patch(self,request,id):
        try:
            cart_item = cart_models.CartModel.objects.get(id=id,user=request.user)
        except cart_models.CartModel.DoesNotExist:
            return error_response(message = "Invalid Cart item id.",
                                  data    = {"cart_id":id},
                                  status_code = status.HTTP_404_NOT_FOUND
                                 )
        
                
        serializer = self.serializer_class(cart_item,data=request.data, context={"request":request}, partial=True)
        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return success_response(message = "Cart item quantity updated successfuly.",
                                        data    = serializer.data,
                                        status_code = status.HTTP_200_OK
                                    )
        except drf_serializers.ValidationError as e:
            message,data = normalize_validation_errors(e.detail)
            return error_response(message = message,
                                  data    = data,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )