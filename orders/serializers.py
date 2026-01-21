from rest_framework import serializers
from accounts import serializers as accounts_serializers
from carts import serializers as carts_serializers
from orders import models
from payments import models as payment_models
from django.db import transaction
from orders import models as orders_model

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

        order_items = instance.items.all()
        blocked_items = order_items.filter(status__in=["SHIPPED","DELIVERED","CANCELLED","REFUNDED"])

        if blocked_items.exists():
            item = blocked_items.first()
            raise serializers.ValidationError({"error_message":"Order contains items that cannot be cancelled",
                                               "data":{"order_id":instance.order_id,
                                                       "order_item_id":item.id,
                                                       "order_item_name":item.name
                                                      }
                                             }) 
        

        if instance.status in ["SHIPPED","DELIVERED","CANCELLED"]:
            raise serializers.ValidationError({"error_message":"Order cannot be cancelled.",
                                               "data":{"order_id":instance.order_id,
                                                       "order_status":instance.status
                                                      }
                                              })
        


        with transaction.atomic():
            instance = orders_model.OrderModel.objects.select_for_update().get(id=instance.id)
            
            instance.status = "CANCELLED"
            instance.save(update_fields=["status"])

            order_items.update(status="CANCELLED")        

        return instance
    



class OrderItemCancelSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source="order.order_id", read_only=True)

    class Meta:
        model = models.OrderItemModel
        fields = ["id","status","order_id"]
        read_only_fields = ["id","status","order_id"]

    
    def update(self, instance, validated_data):

        if instance.status in ["SHIPPED","DELIVERED","CANCELLED","REFUNDED"]:
            raise serializers.ValidationError({"error_message":"Order cannot be cancelled.",
                                               "data":{"order_id":instance.order.order_id,
                                                       "order_status":instance.order.status,
                                                       "order_item_status":instance.status
                                                      }
                                             })
        
        order = instance.order


        with transaction.atomic():
            order = orders_model.OrderModel.objects.select_for_update().get(id=order.id)

            instance.status = "CANCELLED"
            instance.save(update_fields=["status"])

            order_items = order.items.all()

            remaining_items = order_items.exclude(status="CANCELLED")
            
            if not remaining_items.exists():
                order.status="CANCELLED"
                order.save(update_fields=["status"])


        return instance
    



class OrderReturnSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.OrderModel
        fields = ["order_id","status"]
        read_only_fields = ["order_id","status"]

    
    def update(self, instance, validated_data):

        order_items =  instance.items.all()
        
        undelivered_items = order_items.exclude(status="DELIVERED")    
        if undelivered_items.exists():
            item = undelivered_items.first()
            raise serializers.ValidationError({"error_message":"Order cannot be returned.",
                                               "data":{"order_id":instance.order_id,
                                                       "order_item_id":item.id,
                                                       "order_item_name":item.name
                                                      }
                                             })
        
        if instance.status not in ["DELIVERED"]:
            raise serializers.ValidationError({"error_message":"Order isn't fully delivered yet.",
                                               "data":{"order_id":instance.order_id,
                                                       "order_status":instance.status
                                                      }
                                             })


        with transaction.atomic():
            instance = orders_model.OrderModel.objects.select_for_update().get(id=instance.id)

            instance.status = "RETURN_REQUESTED"
            instance.save(update_fields=["status"])

            order_items.update(status="RETURN_REQUESTED")

        
        return instance
    


class OrderItemReturnSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source="order.order_id", read_only=True)

    class Meta:
        model = models.OrderItemModel
        fields = ["id","order_id","status"]
        read_only_fields = ["id","order_id","status"]


    def update(self, instance, validated_data):
        
        if instance.status not in ["DELIVERED"]:
            raise serializers.ValidationError({"error_message":"Order item cannot be returned.",
                                               "data":{"order_item_id":instance.id,
                                                       "order_item_status":instance.status
                                                      }
                                             })

        order = instance.order

        with transaction.atomic():
            order = orders_model.OrderModel.objects.select_for_update().get(id=order.id)

            instance.status = "RETURN_REQUESTED"
            instance.save(update_fields=["status"])
            
            order_items = order.items.all()
            remaining_items = order_items.exclude(status="RETURN_REQUESTED")

            if not remaining_items.exists():
                order.status = "RETURN_REQUESTED"
                order.save(update_fields=["status"])


        return instance

    