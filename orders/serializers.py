from rest_framework import serializers
from accounts import serializers as accounts_serializers
from carts import serializers as carts_serializers
from orders import models
from payments import models as payment_models

class CheckoutPreviewRequestSerializer(serializers.ModelSerializer):
    pass

class CheckoutPreviewResponseSerializer(serializers.Serializer):
    address = accounts_serializers.AddressNestedSerializer(read_only=True)

    cart_items = carts_serializers.CartNestedSerializer(read_only=True, many=True)

    subtotal     = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    shipping_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    grand_total  = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)



class OrderCreateSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(required=True, choices=payment_models.PaymentModel.PAYMENT_METHOD_CHOICES)





class OrderListSerializer(serializers.ModelSerializer):
    items_count = serializers.IntegerField(source="items.count", read_only=True)    

    class Meta:
        model = models.OrderModel
        fields = ["order_id","status","created_at","grand_total","items_count"]





class OrderItemListSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.OrderItemModel
        fields = ["product_name","brand_name","category_name","product_slug","category_slug","brand_slug","unit_price","quantity","total_price"]



class OrderDetailSerializer(serializers.ModelSerializer):
    order_items = OrderItemListSerializer(read_only=True, source="items", many=True)

    class Meta:
        model = models.OrderModel
        fields = ["order_id","status","name","phone","address_line","city","state","pincode","subtotal","shipping_fee","grand_total","created_at","order_items"]



class OrderCancelSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.OrderModel
        fields = ["status","order_id"]
        read_only_fields = ["status","order_id"]

    
    def update(self, instance, validated_data):
        if instance.status in ["SHIPPED","DELIVERED"]:
            raise serializers.ValidationError({"error_message":"Order cannot be cancelled once shipped.",
                                               "data":{"order_id":instance.order_id,
                                                       "order_status":instance.status
                                                      }
                                              })
        
        instance.status = "CANCELLED"

        instance.save()
        return instance