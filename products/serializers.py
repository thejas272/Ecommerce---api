from rest_framework import serializers
from products import models



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