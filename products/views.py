from django.shortcuts import render
from products import serializers
from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from products import models
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
# Create your views here.


class CategoryListAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.CategoryListSerializer

    @swagger_auto_schema(tags=['Products'])
    def get(self,request):
        categories = models.CategoryModel.objects.filter(is_active=True)

        serializer = self.serializer_class(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class BrandListAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.BrandListSerializer

    @swagger_auto_schema(tags=["Products"])
    def get(self,request):
        brands = models.BrandModel.objects.filter(is_active=True)

        serializer = self.serializer_class(brands, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ProductListAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.ProductListSerializer

    @swagger_auto_schema(tags=["Products"])
    def get(self,request):
        products = models.ProductModel.objects.filter(is_active=True)

        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class CategoryDetailAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.CategoryDetailSerializer
    lookup_field = "slug"

    @swagger_auto_schema(tags=['Products'])
    def get(self,request,slug):
        category = get_object_or_404(models.CategoryModel,slug=slug,is_active=True)

        serializer = self.serializer_class(category)
        return Response(serializer.data, status=status.HTTP_200_OK)


