from django.shortcuts import render
from products import serializers
from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from products import models
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.exceptions import NotFound
from accounts.helpers import create_audit_log
from django.db import IntegrityError,transaction
from common.swagger import CATEGORY_PARAM,BRAND_PARAM,SEARCH_PARAM,IS_ACTIVE_PARAM,PARENT_PARAM,MIN_PRICE_PARAM,MAX_PRICE_PARAM,SORT_PARAM,IN_STOCK_PARAM
from common.pagination import DefaultPagination
from products.filters.admin_categories import admin_category_list
from products.filters.admin_brands import admin_brand_list
from products.filters.admin_products import admin_products_list
from products.filters.user_products import user_products_list
from rest_framework import serializers as drf_serializers
from rest_framework.permissions import IsAdminUser

# Create your views here.



# --------------Categories-------------

class AdminCategoryAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated,DjangoModelPermissions,IsAdminUser]
    queryset = models.CategoryModel.objects.all().select_related('parent')
    pagination_class = DefaultPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.CategoryCreateSerializer
        return serializers.AdminCategoryListSerializer


    @swagger_auto_schema(tags=["Admin - Categories"])
    def post(self,request):
        serializer = self.get_serializer(data=request.data, context={"request":request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    @swagger_auto_schema(tags=["Admin - Categories"],
                         manual_parameters=[IS_ACTIVE_PARAM,PARENT_PARAM,CATEGORY_PARAM,SEARCH_PARAM]
                         )    
    def get(self,request):
        categories = self.get_queryset().order_by('-created_at')

        categories = admin_category_list(request,categories)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(categories, request)

        serializer = self.get_serializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)



class CategoryListAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.CategorySerializer
    pagination_class = DefaultPagination

    @swagger_auto_schema(tags=['Categories'])
    def get(self,request):
        categories = models.CategoryModel.objects.filter(is_active=True).select_related("parent").order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(categories, request)
        
        serializer = self.serializer_class(page, many=True)

        return paginator.get_paginated_response(serializer.data)
    



class CategoryDetailAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.CategorySerializer
    lookup_field = "slug"

    @swagger_auto_schema(tags=['Categories'])
    def get(self,request,slug):
        try:
            category = models.CategoryModel.objects.get(slug=slug, is_active=True)
        except models.CategoryModel.DoesNotExist:
            raise NotFound("Category does not exist.")

        serializer = self.serializer_class(category)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class AdminCategoryDetailAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, DjangoModelPermissions,IsAdminUser]
    queryset = models.CategoryModel.objects.all()
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return serializers.CategoryUpdateSerializer
        return serializers.AdminCategoryDetailSerializer
        

    @swagger_auto_schema(tags=["Admin - Categories"])
    def patch(self,request,id):
        try:
            category = models.CategoryModel.objects.get(id=id)
        except models.CategoryModel.DoesNotExist:
            raise NotFound("Category does not exist.")

        serializer = self.get_serializer(category, data=request.data, partial=True, context={"request":request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

    @swagger_auto_schema(tags=["Admin - Categories"])
    def delete(self,request,id):
        try:
            category = models.CategoryModel.objects.get(id=id, is_active=True)
        except models.CategoryModel.DoesNotExist:
            raise NotFound("Category does not exist.") 
        
        action  = "SOFT_DELETE"
        message = f"Category {category.name} deactivated by {request.user.username}"

        with transaction.atomic():
            category.is_active = False
            category.save()

            create_audit_log(user=request.user,action=action,instance=category,message=message) 

        return Response({"detail":"Category deleted successfully."},status=status.HTTP_200_OK)
    

    @swagger_auto_schema(tags=["Admin - Categories"])
    def get(self,request,id):
        try:
            category = models.CategoryModel.objects.get(id=id)
        except models.CategoryModel.DoesNotExist:
            raise NotFound("Category does not exist.")
        
        serializer = self.get_serializer(category)

        return Response(serializer.data, status=status.HTTP_200_OK)

# ---------------BRANDS------------------



class AdminBrandAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated,DjangoModelPermissions,IsAdminUser]
    queryset = models.BrandModel.objects.all()
    pagination_class = DefaultPagination
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.BrandCreateSerializer
        return serializers.AdminBrandSerializer

    @swagger_auto_schema(tags=['Admin - Brands'])
    def post(self,request):
        serializer = self.get_serializer(data=request.data, context={"request":request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(tags=["Admin - Brands"],
                         manual_parameters=[IS_ACTIVE_PARAM,BRAND_PARAM,SEARCH_PARAM])
    def get(self,request):
        brands = self.get_queryset().order_by('-created_at')

        brands = admin_brand_list(request,brands)


        paginator = self.pagination_class()
        page = paginator.paginate_queryset(brands,request)

        serializer = self.get_serializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)



class BrandListAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.BrandSerializer
    pagination_class = DefaultPagination

    @swagger_auto_schema(tags=["Brands"])
    def get(self,request):
        brands = models.BrandModel.objects.filter(is_active=True)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(brands, request)

        serializer = self.serializer_class(page, many=True)

        return paginator.get_paginated_response(serializer.data)



class BrandDetailAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.BrandSerializer
    lookup_field = "slug"

    @swagger_auto_schema(tags=['Brands'])
    def get(self,request,slug):
        try:
            brand = models.BrandModel.objects.get(slug=slug, is_active=True)
        except models.BrandModel.DoesNotExist:
            raise NotFound("Brand does not exist.")

        serializer = self.serializer_class(brand)
        return Response(serializer.data, status=status.HTTP_200_OK)



class AdminBrandDetailAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated, DjangoModelPermissions,IsAdminUser]
    queryset = models.BrandModel.objects.all()
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return serializers.BrandUpdateSerializer
        return serializers.AdminBrandSerializer


    @swagger_auto_schema(tags=["Admin - Brands"])
    def patch(self,request,id):
        try:
            brand = models.BrandModel.objects.get(id=id)
        except models.BrandModel.DoesNotExist:
            raise NotFound("Brand does not exist.")

        serializer = self.get_serializer(brand, data=request.data, partial=True, context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(tags=["Admin - Brands"])
    def delete(self,request,id):
        try:
            brand = models.BrandModel.objects.get(id=id, is_active=True)
        except models.BrandModel.DoesNotExist:
            raise NotFound("Brand does not exist.")

        action  = "SOFT_DELETE"
        message = f"Brand {brand.name} deactivated by {request.user.username}"

        with transaction.atomic():
            brand.is_active = False
            brand.save()

            create_audit_log(user=request.user,action=action,instance=brand,message=message)

        return Response({"detail":"Brand deleted successfully"}, status=status.HTTP_200_OK)
    

    @swagger_auto_schema(tags=["Admin - Brands"])
    def get(self,request,id):
        try:
            brand = models.BrandModel.objects.get(id=id)
        except models.BrandModel.DoesNotExist:
            raise NotFound("Brand does not exist.")
        
        serializer = self.get_serializer(brand)

        return Response(serializer.data, status=status.HTTP_200_OK)



# ------------ PRODUCTS ---------------


class AdminProductAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated,DjangoModelPermissions,IsAdminUser]
    queryset = models.ProductModel.objects.all().select_related('category','brand')
    pagination_class = DefaultPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.ProductCreateSerializer
        return serializers.AdminProductListSerializer

    @swagger_auto_schema(tags=["Admin - Products"])
    def post(self,request):
        serializer = self.get_serializer(data=request.data, context={"request":request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(tags=["Admin - Products"],
                         manual_parameters=[CATEGORY_PARAM,BRAND_PARAM,SEARCH_PARAM,MIN_PRICE_PARAM,MAX_PRICE_PARAM,IS_ACTIVE_PARAM]
                         )
    def get(self,request):
        products = self.get_queryset().order_by('-created_at')

        try:
            products = admin_products_list(request,products)
        except drf_serializers.ValidationError as e:
            return Response({"detail":e.detail},status=status.HTTP_400_BAD_REQUEST)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(products,request)

        serializer = self.get_serializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)
    


class ProductListAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.ProductSerializer
    pagination_class = DefaultPagination

    @swagger_auto_schema(tags=["Products"],
                         manual_parameters=[CATEGORY_PARAM,BRAND_PARAM,MIN_PRICE_PARAM,MAX_PRICE_PARAM,SEARCH_PARAM,SORT_PARAM,IN_STOCK_PARAM]
                         )
    def get(self,request):
        products = models.ProductModel.objects.filter(is_active=True).select_related('category','brand').order_by('-created_at')

        try:
            products = user_products_list(request,products)
        except drf_serializers.ValidationError as e:
            return Response({"detail":e.detail},status=status.HTTP_400_BAD_REQUEST)


        paginator = self.pagination_class()
        page = paginator.paginate_queryset(products, request)
        
        serializer = self.serializer_class(page, many=True)

        return paginator.get_paginated_response(serializer.data)



class ProductDetailAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.ProductSerializer
    lookup_field = "slug"

    @swagger_auto_schema(tags=['Products'])
    def get(self,request,slug):
        try:
            product = models.ProductModel.objects.get(slug=slug, is_active=True)
        except models.ProductModel.DoesNotExist:
            raise NotFound("Product does not exist.")
        
        serializer = self.serializer_class(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class AdminProductDetailAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated,DjangoModelPermissions,IsAdminUser]
    queryset = models.ProductModel.objects.all()
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return serializers.ProductUpdateSerializer
        return serializers.AdminProductDetailSerializer


    @swagger_auto_schema(tags=["Admin - Products"])
    def patch(self,request,id):
        try:
            product = models.ProductModel.objects.get(id=id)
        except models.ProductModel.DoesNotExist:
            raise NotFound("Product does not exist.")

        serializer = self.get_serializer(product, data=request.data, partial=True, context={"request":request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["Admin - Products"])
    def delete(self,request,id):
        try:
            product = models.ProductModel.objects.get(id=id,is_active=True)
        except models.ProductModel.DoesNotExist:
            raise NotFound("Product does not exist.")
        
        action = "SOFT_DELETE"
        message = f"Product {product.name} deactivated by {request.user.username}"

        with transaction.atomic():
            product.is_active = False
            product.save()

            create_audit_log(user=request.user,action=action,instance=product,message=message)

        return Response({"detail":"Product deleted successfully."}, status=status.HTTP_200_OK)
    

    @swagger_auto_schema(tags=["Admin - Products"])
    def get(self,request,id):
        try:
            product = models.ProductModel.objects.get(id=id)
        except models.ProductModel.DoesNotExist:
            raise NotFound("Product does not exist.")
        
        serializer = self.get_serializer(product)

        return Response(serializer.data, status=status.HTTP_200_OK)

