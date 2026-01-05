from rest_framework import serializers
from carts import models as carts_models
from products import models as products_models
from rest_framework.validators import UniqueTogetherValidator
from django.db.utils import IntegrityError
from django.db import transaction
from products import serializers as products_serializers



class AddToCartSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=products_models.ProductModel.objects.filter(is_active=True),
                                                 required=True,
                                                )
    quantity = serializers.IntegerField(min_value=1, required=True)

    class Meta:
        model = carts_models.CartModel
        fields = ["id","product","quantity","unit_price","total_price"]
        read_only_fields = ["id","unit_price","total_price"]

        
    def validate_quantity(self,value):
        if value <= 0:
            raise serializers.ValidationError("Quantity cannot be zero or negative.")
        return value
        

    def validate(self,attrs):
        request = self.context["request"]

        product  = attrs.get('product')
        quantity = attrs.get('quantity')

        existing_cart_quantity = 0

        existing_cart_instance = carts_models.CartModel.objects.filter(user=request.user,product=product).first()
        if existing_cart_instance is not None:
            existing_cart_quantity = existing_cart_instance.quantity

        if quantity+existing_cart_quantity > product.stock:
            raise serializers.ValidationError("Insufficient stock.") 

        return attrs
    

    def create(self, validated_data):
        request = self.context["request"]
        
        product =validated_data['product']

        cart_instance,created = carts_models.CartModel.objects.get_or_create(user=request.user,product=product,
                                                                             defaults={"unit_price":product.price,
                                                                                       "quantity":validated_data['quantity'],
                                                                                       }
                                                                            )

        if not created:
            cart_instance.quantity = cart_instance.quantity + validated_data['quantity']
            cart_instance.save()
        
        return cart_instance




class CartListSerializer(serializers.ModelSerializer):
    product = products_serializers.ProductNestedSerializer(read_only=True)
    
    brand_name    = serializers.CharField(source="product.brand.name", read_only=True)
    category_name = serializers.CharField(source="product.category.name", read_only=True)
    
    class Meta:
        model = carts_models.CartModel
        fields = ["id","product","brand_name","category_name","unit_price","quantity","total_price","created_at","updated_at"]
    


class UpdateCartQuantitySerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1, required=True)
    
    class Meta:
        model = carts_models.CartModel
        fields = ["id","product","unit_price","quantity","total_price"]
        read_only_fields = ["id","product","unit_price","total_price"]

    def validate_quantity(self,value):
        if value <= 0:
            raise serializers.ValidationError("Quantity cannot be zero or negative.")
        return value
    
    def validate(self,attrs):
        quantity = attrs.get('quantity')

        if quantity > self.instance.product.stock:
            raise serializers.ValidationError("insufficient stock.")
        
        return attrs
    
    def update(self, instance, validated_data):

        return super().update(instance, validated_data)
    
        

