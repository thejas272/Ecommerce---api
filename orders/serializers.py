from rest_framework import serializers
from accounts import serializers as accounts_serializers
from carts import serializers as carts_serializers
from orders import models
from payments import models as payment_models
from django.db import transaction
from orders import models as orders_model
from decimal import Decimal
from django.db import IntegrityError

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


        if not instance.is_all_items_cancellable:
            raise serializers.ValidationError({"error_message":"Order cannot be cancelled once items are shipped.",
                                               "data":{"order_id":instance.order_id}
                                             })
        
        try:
            with transaction.atomic():
                instance = orders_model.OrderModel.objects.select_for_update().get(id=instance.id)
                order_items = instance.items.select_for_update()
                payment_instance = payment_models.PaymentModel.objects.select_for_update().filter(order=instance).order_by('-created_at').first()

                if not payment_instance:
                    raise serializers.ValidationError({"error_message":"Payment info not found.",
                                                    "data":{"order_id":instance.order_id}
                                                    })

                if payment_instance.is_processing:
                    raise serializers.ValidationError({"error_message":"Payment is being processed, try again shortly.",
                                                    "data":{"order_id":instance.order_id}
                                                    })
                
                if payment_instance.payment_confirmation == "PENDING":
                    raise serializers.ValidationError({"error_message":"Payment confirmation pending, try again shortly.",
                                                       "data":{"order_id":instance.order_id}
                                                     })
                


                instance.status = "CANCELLED"
                instance.save(update_fields=["status"])

                order_items.update(status="CANCELLED")        

                if payment_instance.is_unpaid:

                    payment_instance.status = "CANCELLED"
                    payment_instance.save(update_fields=["status"])



                if payment_instance.can_refund:
                    refund_items = []

                    if payment_models.RefundModel.objects.filter(order=instance,payment=payment_instance,status="SUCCESS").exists():
                        raise serializers.ValidationError({"error_message":"Refund already done",
                                                           "data":{"order_id":instance.order_id}
                                                         })

                    refund = payment_models.RefundModel.objects.create(order = instance,
                                                                    payment = payment_instance,
                                                                    amount  = payment_instance.amount,
                                                                    currency = payment_instance.currency,
                                                                    method  = payment_instance.method,
                                                                    reason  = "ORDER_CANCELLED",                
                                                                    )

                    
                    for item in order_items.all():
                        refund_items.append(payment_models.RefundItemModel(refund = refund,
                                                                           item   = item,
                                                                           amount = item.total_price,
                                                                          )
                                           )
                        
                    payment_models.RefundItemModel.objects.bulk_create(refund_items)
                    
                    payment_instance.refund_info = "REQUESTED"
                    payment_instance.save(update_fields=["refund_info"])
        
        except IntegrityError:
            raise serializers.ValidationError({"error_message":"Refund already processed for items.",
                                               "data":{"order_id":instance.order_id}
                                             })

        return instance
    



class OrderItemCancelSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source="order.order_id", read_only=True)

    class Meta:
        model = models.OrderItemModel
        fields = ["id","status","order_id"]
        read_only_fields = ["id","status","order_id"]

    
    def update(self, instance, validated_data):

        if not instance.is_cancellable:
            raise serializers.ValidationError({"error_message":"Order item cannot be cancelled.",
                                               "data":{"order_id":instance.order.order_id,
                                                       "order_status":instance.order.status,
                                                       "order_item_status":instance.status
                                                      }
                                             })


        try:
            with transaction.atomic():
                order = orders_model.OrderModel.objects.select_for_update().get(id=instance.order.id)
                order_items = order.items.select_for_update()
                payment_instance = payment_models.PaymentModel.objects.select_for_update().filter(order=order).order_by('-created_at').first()

                if not payment_instance:
                    raise serializers.ValidationError({"error_message":"Payment info not found.",
                                                    "order_id":order.order_id
                                                    })

                if payment_instance.is_processing:
                    raise serializers.ValidationError({"error_message":"Payment is being processed, try again shortly.",
                                                    "order_id":order.order_id
                                                    })
                
                if payment_instance.payment_confirmation == "PENDING":
                    raise serializers.ValidationError({"error_message":"Payment confirmation pending, try again shortly",
                                                       "data":{"order_id":order.order_id}
                                                     })


                instance.status = "CANCELLED"
                instance.save(update_fields=["status"])

                if order.is_cancelled:
                    order.status = "CANCELLED"
                    order.save(update_fields=["status"])

                    if payment_instance.is_unpaid:

                        payment_instance.status = "CANCELLED"
                        payment_instance.save(update_fields=["status"])
                
                else:
                    if payment_instance.is_unpaid:
                        order.subtotal    = order.subtotal - instance.total_price
                        order.grand_total = order.grand_total - instance.total_price

                        payment_instance.amount = payment_instance.amount - instance.total_price
                        
                        order.save(update_fields=["subtotal","grand_total"])
                        payment_instance.save(update_fields=["amount"])

                
                
                if payment_instance.is_paid:

                    if payment_models.RefundItemModel.objects.filter(item=instance,status="SUCCESS").exists():
                        raise serializers.ValidationError({"error_message":"Refund already processed for this item.",
                                                        "data":{"order_id":order.order_id}
                                                        })
                    

                    refund = payment_models.RefundModel.objects.create(order = order,
                                                                    payment = payment_instance,
                                                                    amount  = Decimal(0),
                                                                    currency = payment_instance.currency,
                                                                    method  = payment_instance.method,
                                                                    reason  = "ORDER_ITEM_CANCELLED",
                                                                                                
                                                                    )

                    payment_models.RefundItemModel.objects.create(refund = refund,
                                                                item   = instance,
                                                                amount = instance.total_price,
                                                                )
                    refund.amount += instance.total_price
                        
                    if order.is_cancelled:
                        refund.amount += order.shipping_fee

                    refund.save(update_fields=["amount"])
                    
                    payment_instance.refund_info = "REQUESTED"
                    payment_instance.save(update_fields=["refund_info"])

        except IntegrityError:
            raise serializers.ValidationError({"error_message":"Refund already processed for this item.",
                                               "data":{"order_id":instance.order.order_id}
                                             })
        
        return instance
    



class OrderReturnSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.OrderModel
        fields = ["order_id","status","return_info"]
        read_only_fields = ["order_id","status","return_info"]

    
    def update(self, instance, validated_data):

        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError({"error_message":"Authentication required for this operaiton."})
        


        if not instance.is_all_items_returnable:
            raise serializers.ValidationError({"error_message":"Order cannot be returned.",
                                               "data":{"order_id":instance.order_id}
                                             })
        
        try:
            with transaction.atomic():
                instance = orders_model.OrderModel.objects.select_for_update().get(id=instance.id)
                order_items =  instance.items.select_for_update()
                payment_instance = payment_models.PaymentModel.objects.select_for_update().filter(order=instance).order_by('-created_at').first()

                if not payment_instance:
                    raise serializers.ValidationError({"error_message":"Payment info not found",
                                                       "data":{"order_id":instance.order_id}
                                                     })
                
                if payment_instance.is_processing:
                    raise serializers.ValidationError({"error_message":"Payment is currently being processed",
                                                       "data":{"order_id":instance.order_id}
                                                     })



                # return record creation
                                
                if orders_model.ReturnModel.objects.filter(order=instance,status__in=["CONFIRMED","PICKED_UP","RECEIVED","REFUND_COMPLETED"]).exists():
                    raise serializers.ValidationError({"error_message":"Return already processed for this order.",
                                                       "data":{"order_id":instance.order_id}
                                                     })

                return_instance = orders_model.ReturnModel.objects.create(requested_by = request.user,
                                                                        order   = instance,
                                                                        name    = instance.name,
                                                                        phone   = instance.phone,
                                                                        address_line = instance.address_line,
                                                                        city    = instance.city,
                                                                        state   = instance.state,
                                                                        pincode = instance.pincode,
                                                                        reason  = "ORDER_RETURN"
                                                                        )
                
                return_items = []
                for item in order_items:
                    return_items.append(orders_model.ReturnItemModel(return_instance=return_instance,
                                                                    item = item
                                                                    )
                                        ) 
                orders_model.ReturnItemModel.objects.bulk_create(return_items)



                # order instance return info updation
                instance.return_info = "REQUESTED"
                instance.save(update_fields=["return_info"])

                order_items.update(return_info="REQUESTED")



                # refund record creation

                if payment_models.RefundModel.objects.filter(order=instance,payment=payment_instance,status="SUCCESS").exists():
                    raise serializers.ValidationError({"error_message":"Refund already processed for this order.",
                                                       "data":{"order_id":instance.order_id}
                                                     })

                refund = payment_models.RefundModel.objects.create(order   = instance,
                                                                   payment = payment_instance,
                                                                   amount  = Decimal(0),
                                                                   currency = payment_instance.currency,
                                                                   method   = payment_instance.method,
                                                                   reason   = return_instance.reason,
                                                                   )
                
                refund_items = []
                for item in order_items:
                    refund_items.append(payment_models.RefundItemModel(refund = refund,
                                                                       item   = item,
                                                                       amount = item.total_price
                                                                      )
                                       )
                    refund.amount += item.total_price
                
                payment_models.RefundItemModel.objects.bulk_create(refund_items)

                refund.save(update_fields=["amount"])


                payment_instance.refund_info = "REQUESTED"
                payment_instance.save(update_fields=["refund_info"])


        except IntegrityError:
            raise serializers.ValidationError({"error_message":"Return already processed for item.",
                                               "data":{"order_id":instance.order_id}
                                             })
                

        return instance
    






class OrderItemReturnSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source="order.order_id", read_only=True)

    class Meta:
        model = models.OrderItemModel
        fields = ["id","order_id","status","return_info"]
        read_only_fields = ["id","order_id","status","return_info"]


    def update(self, instance, validated_data):

        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError({"error_message":"Authentication required for this operation."})



        if not instance.is_item_returnable:
            raise serializers.ValidationError({"error_message":"Item cannot be returned.",
                                               "data":{"order_id":instance.order.order_id,
                                                       "order_item_id":instance.id,
                                                       "order_item_status":instance.status
                                                      }
                                             })

        try:
            with transaction.atomic():
                order = orders_model.OrderModel.objects.select_for_update().get(id=instance.order.id)
                order_items = order.items.select_for_update() 
                payment_instance = payment_models.PaymentModel.objects.select_for_update().filter(order=order).order_by('-created_at').first()

                if not payment_instance:
                    raise serializers.ValidationError({"error_message":"Payment info not found",
                                                        "data":{"order_id":order.order_id,
                                                                "order_item_id":instance.id,
                                                                "order_item_status":instance.status
                                                                }
                                                    })


                if payment_instance.is_processing:
                    raise serializers.ValidationError({"error_message":"Payment is currently being processed",
                                                       "data":{"order_id":order.order_id,
                                                               "order_item_id":instance.id,
                                                               "order_item_status":instance.status
                                                              }
                                                                
                                                     })
                


                #return record creation
                

                if orders_model.ReturnItemModel.objects.filter(item=instance,status__in=["CONFIRMED","PICKED_UP","RECEIVED","REFUND_COMPLETED"]).exists():
                    raise serializers.ValidationError({"error_message":"Return for this item already processed.",
                                                       "data":{"order_id":order.order_id,
                                                               "order_item_id":instance.id,
                                                               "order_item_status":instance.status
                                                              }
                                                     })
                
                
                return_instance = orders_model.ReturnModel.objects.create(requested_by = request.user,
                                                                        order   = order,
                                                                        name    = order.name,
                                                                        phone   = order.phone,
                                                                        address_line = order.address_line,
                                                                        city    = order.city,
                                                                        state   = order.state,
                                                                        pincode = order.pincode,
                                                                        reason  = "ORDER_ITEM_RETURN"
                                                                        )
                
                
                orders_model.ReturnItemModel.objects.create(return_instance = return_instance,
                                                            item = instance
                                                           )
                


                # order item return info, order return info (only if all items returned) updation

                instance.return_info = "REQUESTED"
                instance.save(update_fields=["return_info"])


                if order.was_return_requested:
                    order.return_info = "REQUESTED"
                    order.save(update_fields=["return_info"])




                # refund record creation 

                if payment_models.RefundItemModel.objects.filter(item=instance,status="SUCCESS").exists():
                    raise serializers.ValidationError({"error_message":"Refund already processed for this item.",
                                                       "data":{"order_id":order.order_id,
                                                               "order_item_id":instance.id,
                                                               "order_item_status":instance.status
                                                              }
                                                     })
                

                refund = payment_models.RefundModel.objects.create(order = order,
                                                                   payment = payment_instance,
                                                                   amount = Decimal(0),
                                                                   currency = payment_instance.currency,
                                                                   method = payment_instance.method,
                                                                   reason = "ORDER_ITEM_RETURN"
                                                                   )
                
                
                payment_models.RefundItemModel.objects.create(refund = refund,
                                                              item   = instance,
                                                              amount = instance.total_price
                                                             )
                refund.amount += instance.total_price
                refund.save(update_fields=["amount"])
                



                payment_instance.refund_info = "REQUESTED"
                payment_instance.save(update_fields=["refund_info"])




        except IntegrityError:
            raise serializers.ValidationError({"error_message":"Return already processed for this item.",
                                               "data":{"order_id":order.order_id,
                                                       "order_item_id":instance.id,
                                                       "order_item_status":instance.status
                                                      }
                                             })


        return instance

    