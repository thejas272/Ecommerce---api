from rest_framework import serializers
from products import models
import re
from django.db import IntegrityError,transaction



class CategoryCreateSerializer(serializers.ModelSerializer):
    name   = serializers.CharField(required=True)
    parent = serializers.PrimaryKeyRelatedField(queryset   = models.CategoryModel.objects.all(),
                                                required   = False,
                                                allow_null = True
                                                )
    
    class Meta:
        model = models.CategoryModel
        fields = ["name","parent"]

    
    def validate_name(self,value):
        value = value.strip()

        if not re.fullmatch(r'[A-Za-z]+( [A-Za-z]+)*',value):
            raise serializers.ValidationError("Category name can only contain letters and whitespace.")
        
        if models.CategoryModel.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Category already exists.")
        
        return value

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError("Category already exists.")




class CategoryListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.CategoryModel
        fields = ['id','name','parent','slug']



class CategoryDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.CategoryModel
        fields = ['id','name','parent','slug']


class CategoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CategoryModel
        fields = ["name","parent"]

    def validate_name(self,value):
        value = value.strip()
    
        if not re.fullmatch(r'[A-Za-z]+( [A-Za-z]+)*',value):
            raise serializers.ValidationError("Category name can only contain letters and spaces.")
        
        if models.CategoryModel.objects.filter(name__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Category already exists.")
        
        return value
    
    def validate_parent(self,value):
        if self.instance and self.instance == value:
            raise serializers.ValidationError("A category cannot be it's own parent.")
        
        return value
    
    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError("Category already exists.")






class BrandCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    
    class Meta:
        model = models.BrandModel
        fields = ["name"]


    def validate_name(self,value):
        value = value.strip()
        
        if not re.fullmatch(r'[A-Za-z]+( [A-Za-z]+)*',value):
            raise serializers.ValidationError("Brand name can only contain letters and spaces.")
        
        if models.BrandModel.objects.filter(name=value).exists():
            raise serializers.ValidationError("Brand already exists.")

        return value
    

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError("Brand already exists.")


class BrandListSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BrandModel
        fields = ["id","name","slug"]


class BrandDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BrandModel
        fields = ["id","name","slug"]



class BrandUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BrandModel
        fields = ["name"]

    def validate_name(self,value):
        if not re.fullmatch(r'[A-Za-z]+( [A-Z(a-z]+)*',value):
            raise serializers.ValidationError("Brand name can only contain letters and spaces.")
        
        if models.BrandModel.objects.filter(name__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Brand already exists.")
        
        return value
    
    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError("Brand already exists.")





class ProductCreateSerializer(serializers.ModelSerializer):
    name     = serializers.CharField(required=True)
    category = serializers.PrimaryKeyRelatedField(queryset = models.CategoryModel.objects.all(),
                                                  required=True,
                                                 ) 
    brand    = serializers.PrimaryKeyRelatedField(queryset = models.BrandModel.objects.all(),
                                                  required=True,
                                                 )
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    price       = serializers.DecimalField(required=True, max_digits=10, decimal_places=2, min_value=0)
    stock       = serializers.IntegerField(required=False)

    class Meta:
        model = models.ProductModel
        fields = ["name","category","brand","description","price","stock"]

    
    def validate_name(self,value):
        value = value.strip()
        if not re.fullmatch(r'[A-Za-z]+( [A-Za-z]+)*',value):
            raise serializers.ValidationError("Product name can only contain letters and spaces.")

        return value
    
    def validate_price(self,value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        
        return value
    
    def validate_stock(self,value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        
        return value
    
    def validate(self, attrs):
        name  = attrs.get("name").strip()
        brand = attrs.get("brand")

        if models.ProductModel.objects.filter(name__iexact=name,brand=brand).exists():
            raise serializers.ValidationError("This brand already has a product with the same name.")
        
        return attrs
    
    def create(self, validated_data):
        try:
            with transaction.atomic():
                return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError("This brand already has a product with the same name.")
        
        return product

    



class ProductListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.ProductModel
        fields = ["id","name","category","brand","slug","description","price","stock"]




class ProductDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.ProductModel
        fields = ["id","name","brand","category","slug","description","price","stock"]


