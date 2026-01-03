from rest_framework import serializers
from products import models
import re
from django.db import IntegrityError,transaction
from rest_framework.validators import UniqueTogetherValidator
from accounts.helpers import create_audit_log

class CategoryCreateSerializer(serializers.ModelSerializer):
    name   = serializers.CharField(required=True)
    parent = serializers.PrimaryKeyRelatedField(queryset   = models.CategoryModel.objects.all(),
                                                required   = False,
                                                allow_null = True
                                                )
    
    class Meta:
        model = models.CategoryModel
        fields = ["id","name","parent","slug","is_active","created_at","updated_at"]
        read_only_fields = ["id","slug","created_at","updated_at"]

    
    def validate_name(self,value):
        value = value.strip()

        if not re.fullmatch(r'[A-Za-z]+( [A-Za-z]+)*',value):
            raise serializers.ValidationError("Category name can only contain letters and whitespace.")
        
        if models.CategoryModel.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Category already exists.")
        
        return value


    def create(self, validated_data):
        request = self.context.get("request")

        if not request or not request.user:
            raise serializers.ValidationError("User authentication required for this operation.")
        
        action  = "CREATE"
        message = f"New category {validated_data['name']} created by {request.user.username}"
        try:
            with transaction.atomic():
                category = super().create(validated_data)
                create_audit_log(user=request.user,action=action,instance=category,message=message)

                return category

        except IntegrityError:
            raise serializers.ValidationError("Category already exists.")



class AdminCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model =  models.CategoryModel
        fields = ["id","name","parent","slug","is_active","created_at","updated_at"]





class CategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.CategoryModel
        fields = ['id','name','parent','slug']



class CategoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CategoryModel
        fields = ["id","name","parent","slug","is_active","created_at","updated_at"]
        read_only_fields = ["id","slug","created_at","updated_at"]

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
        request = self.context.get("request")

        if not request or not request.user:
            raise serializers.ValidationError("User authentication required for this operation.")
        
        action  = "UPDATE"
        changes = {}
        for field,new_value in validated_data.items():

            old_value = getattr(instance,field)

            if old_value != new_value:
                changes[field] = {"old":str(old_value),
                                  "new":str(new_value)
                                  }

         
        try:
            with transaction.atomic():
                category = super().update(instance, validated_data)

                if changes:
                    changes_message = ", ".join(f"{field} changed from {v['old']} -> {v['new']}" for field,v in changes.items())
                    message = f"{changes_message} by {request.user.username}"
                    create_audit_log(user=request.user,action=action,instance=category,message=message,changes=changes)

                return category
        except IntegrityError:
            raise serializers.ValidationError("Category already exists.")



#----------------Brands-----------------


class BrandCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    
    class Meta:
        model = models.BrandModel
        fields = ["id","name","slug","is_active","created_at","updated_at"]
        read_only_fields = ["id","slug","created_at","updated_at"]


    def validate_name(self,value):
        value = value.strip()
        
        if not re.fullmatch(r'[A-Za-z]+( [A-Za-z]+)*',value):
            raise serializers.ValidationError("Brand name can only contain letters and spaces.")
        
        if models.BrandModel.objects.filter(name=value).exists():
            raise serializers.ValidationError("Brand already exists.")

        return value
    

    def create(self, validated_data):
        request = self.context.get("request")

        if not request or not request.user:
            raise serializers.ValidationError("User authentication required for this operation.")
        
        action  = "CREATE"
        message = f"Brand {validated_data["name"]} created by {request.user.username}"


        try:
            with transaction.atomic():
                brand = super().create(validated_data)
                create_audit_log(user=request.user,action=action,instance=brand,message=message)

                return brand
        except IntegrityError:
            raise serializers.ValidationError("Brand already exists.")


class AdminBrandSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BrandModel
        fields = ["id","name","slug","is_active","created_at","updated_at"]



class BrandSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BrandModel
        fields = ["id","name","slug"]




class BrandUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BrandModel
        fields = ["id","name","slug","is_active","created_at","updated_at"]
        read_only_fields = ["id","slug","created_at","updated_at"]

    def validate_name(self,value):
        value = value.strip()
        if not re.fullmatch(r'[A-Za-z]+( [A-Z(a-z]+)*',value):
            raise serializers.ValidationError("Brand name can only contain letters and spaces.")
        
        if models.BrandModel.objects.filter(name__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Brand already exists.")
        
        return value
    
    def update(self, instance, validated_data):
        request = self.context.get("request")

        if not request or not request.user:
            raise serializers.ValidationError("User authentication required for this operation.")
        
        action = "UPDATE"
        changes = {}

        for field,new_value in validated_data.items():
            old_value = getattr(instance,field)

            if old_value != new_value:
                changes[field] = {"old":str(old_value),
                                  "new":str(new_value)
                                  }


        try:
            with transaction.atomic():
                brand = super().update(instance, validated_data)

                if changes:
                    changes_message = ", ".join(f"{field} changed from {v['old']} -> {v['new']}" for field,v in changes.items())
                    message = f"{changes_message} by {request.user.username}"

                    create_audit_log(user=request.user,action=action,instance=brand,message=message,changes=changes)

                return brand
        except IntegrityError:
            raise serializers.ValidationError("Brand already exists.")





#-------------------Products---------------------


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
        fields = ["id","name","category","brand","slug","description","price","stock","is_active","created_at","updated_at"]
        read_only_fields = ["id","slug","created_at","updated_at"]

        validators = [
            UniqueTogetherValidator(queryset = models.ProductModel.objects.all(),
                                    fields = ["name","brand"],
                                    message = "This brand already has a product with the same name.")
        ]

    
    def validate_name(self,value):
        value = value.strip()
        if not re.fullmatch(r'[A-Za-z0-9]+( [A-Za-z0-9]+)*',value):
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
        return attrs
    
    def create(self, validated_data):
        request = self.context.get("request")

        if not request or not request.user:
            raise serializers.ValidationError("User authentication required for this operation.")
        
        action  = "CREATE"
        message = f"Product {validated_data['name']} created by {request.user.username}"

        try:
            with transaction.atomic():
                product = super().create(validated_data)
                create_audit_log(user=request.user,action=action,instance=product,message=message)

                return product
        except IntegrityError:
            raise serializers.ValidationError("This brand already has a product with the same name.")
        
        return product


class AdminProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ProductModel
        fields = ["id","name","brand","category","slug","description","price","stock","is_active","created_at","updated_at"]
    


class ProductSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.ProductModel
        fields = ["id","name","category","brand","slug","description","price","stock"]



class ProductUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ProductModel
        fields = ["id","name","category","brand","description","price","stock","slug","is_active","created_at","updated_at"]
        read_only_fields = ["id","slug","created_at","updated_at"]

        validators = [
            UniqueTogetherValidator(queryset=models.ProductModel.objects.all(),
                                    fields=["name","brand"],
                                    message="This brand already has a product with the same name."
                                    )
                     ]

    
    def validate_name(self,value):
        value = value.strip()
        if not re.fullmatch(r'[A-Za-z0-9]+( [A-Za-z0-9]+)*',value):
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
        return attrs
    
    def update(self, instance, validated_data):
        request = self.context.get("request")

        if not request or not request.user:
            raise serializers.ValidationError("User authentication required for this operation.")
        
        action = "UPDATE"
        changes = {}

        for field,new_value in validated_data.items():
            old_value = getattr(instance,field)

            if old_value != new_value:
                changes[field] = {"old":str(old_value),
                                  "new":str(new_value)
                                  }

        try:
            with transaction.atomic():
                product = super().update(instance, validated_data)

                if changes:
                    changes_message = ", ".join(f"{field} changed from {v['old']} -> {v['new']}" for field,v in changes.items())
                    message = f"{changes_message} by {request.user.username}"
                
                    create_audit_log(user=request.user,action=action,instance=product,message=message,changes=changes)

                return product
        except IntegrityError:
            raise serializers.ValidationError("This brand already has a product with the same name.")
        


