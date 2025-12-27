from django.shortcuts import render
from products import serializers
from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from products import models
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from decimal import Decimal, InvalidOperation
from django.db.models import Q
from rest_framework.permissions import DjangoModelPermissions
# Create your views here.


class DefaultPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 50
    page_size_query_param = "page_size"



class CategoryCreateAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated,DjangoModelPermissions]
    serializer_class = serializers.CategoryCreateSerializer
    queryset = models.CategoryModel.objects.all()

    @swagger_auto_schema(tags=["Products"])
    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)







class CategoryListAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.CategoryListSerializer
    pagination_class = DefaultPagination

    @swagger_auto_schema(tags=['Products'])
    def get(self,request):
        categories = models.CategoryModel.objects.filter(is_active=True)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(categories, request)
        
        serializer = self.serializer_class(page, many=True)

        return paginator.get_paginated_response(serializer.data)
    

class BrandListAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.BrandListSerializer
    pagination_class = DefaultPagination

    @swagger_auto_schema(tags=["Products"])
    def get(self,request):
        brands = models.BrandModel.objects.filter(is_active=True)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(brands, request)

        serializer = self.serializer_class(page, many=True)

        return paginator.get_paginated_response(serializer.data)
    

class ProductListAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.ProductListSerializer
    pagination_class = DefaultPagination


    SORT_OPTIONS = {"price_asc":"price",
                    "price_desc":"-price",
                    "newest":"-created_at",
                    "oldest":"created_at"
                    }

    @swagger_auto_schema(tags=["Products"])
    def get(self,request):
        products = models.ProductModel.objects.filter(is_active=True)

        category  = request.query_params.get("category")
        brand     = request.query_params.get("brand")
        min_price = request.query_params.get("min_price") 
        max_price = request.query_params.get("max_price")
        search    = request.query_params.get("search") 
        sort      = request.query_params.get("sort")
        in_stock  = request.query_params.get("in_stock")

        try:
            if min_price:
                min_price = Decimal(min_price)
            if max_price:
                max_price = Decimal(max_price)
        except InvalidOperation:
            return Response({"detail":"Invalid price format"},status=status.HTTP_400_BAD_REQUEST)

        # filter cheks
        if category:
            products = products.filter(category__slug=category)

        if brand:
            products = products.filter(brand__slug=brand)
        
        if min_price:
            products = products.filter(price__gte=min_price)
        
        if max_price:
            products = products.filter(price__lte=max_price)

        
        if search:
            products = products.filter(Q(name__icontains=search)|
                                       Q(category__name__icontains=search)|
                                       Q(brand__name__icontains=search)|
                                       Q(slug__icontains=search)|
                                       Q(description__icontains=search)
                                       )
            
        
        order_by = self.SORT_OPTIONS.get(sort)
        if order_by:
            products = products.order_by(order_by)
        

        if in_stock == "true":
            products = products.filter(stock__gt=0)
        elif in_stock == "false":
            products = products.filter(stock=0)
        

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(products, request)
        
        serializer = self.serializer_class(page, many=True)

        return paginator.get_paginated_response(serializer.data)





class CategoryDetailAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.CategoryDetailSerializer
    lookup_field = "slug"

    @swagger_auto_schema(tags=['Products'])
    def get(self,request,slug):
        category = get_object_or_404(models.CategoryModel, slug=slug, is_active=True)

        serializer = self.serializer_class(category)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class BrandDetailAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.BrandDetailSerializer
    lookup_field = "slug"

    @swagger_auto_schema(tags=['Products'])
    def get(self,request,slug):
        brand = get_object_or_404(models.BrandModel, slug=slug, is_active=True)

        serializer = self.serializer_class(brand)
        return Response(serializer.data, status=status.HTTP_200_OK)



class ProductDetailAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.ProductDetailSerializer
    lookup_field = "slug"

    @swagger_auto_schema(tags=['Products'])
    def get(self,request,slug):
        product = get_object_or_404(models.ProductModel, slug=slug, is_active=True)

        serializer = self.serializer_class(product)
        return Response(serializer.data, status=status.HTTP_200_OK)


