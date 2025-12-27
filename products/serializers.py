from rest_framework import serializers
from products import models
import re
from django.db import IntegrityError,transaction

class CategoryCreateSerializer(serializers.ModelSerializer):
    name   = serializers.CharField(required=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=models.CategoryModel.objects.all(),
                                                required=False,
                                                allow_null=True
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


class BrandListSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BrandModel
        fields = ["id","name","slug"]


class ProductListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.ProductModel
        fields = ["id","name","category","brand","slug","description","price","stock"]



class CategoryDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.CategoryModel
        fields = ['id','name','parent','slug']




class BrandDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BrandModel
        fields = ["id","name","slug"]



class ProductDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.ProductModel
        fields = ["id","name","brand","category","slug","description","price","stock"]


