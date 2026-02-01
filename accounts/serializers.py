from rest_framework import serializers
from accounts import models
from django.db import IntegrityError,transaction
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken,TokenError
import re
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.conf import settings
from orders import models as orders_models
from accounts.helpers import create_audit_log
from payments import models as payments_model

class RegsiterSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True, max_length=30)
    last_name  = serializers.CharField(required=True, max_length=30)
    username   = serializers.CharField(required=True, max_length=30)
    password   = serializers.CharField(required=True, write_only=True, min_length=8)
    email      = serializers.EmailField(required=True)

    class Meta:
        model = models.User
        fields = ["first_name","last_name","username","password","email"]
    
    def validate_first_name(self, value):
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z]+",value):
            raise serializers.ValidationError("First name must only contain letters.")
        return value
    
    def validate_last_name(self, value):
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z]+( [A-Za-z]+)*", value.strip()):
            raise serializers.ValidationError("Last name must only contain letters and spaces.")
        return value
    
    def validate_username(self, value):
        value = value.strip()
        if not re.match(r'^[A-Za-z0-9_]+$', value):
            raise serializers.ValidationError("Username can only contain letters, numbers, and underscores.")
        
        if models.User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        
        return value
    

    def validate_email(self, value):
        value = value.lower()
        if models.User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already taken.")
        
        return value

    
    def validate(self, attrs):
        return attrs
    


    def create(self, validated_data):

        try:
            with transaction.atomic():
                user = models.User.objects.create_user(first_name = validated_data['first_name'],
                                                       last_name  = validated_data['last_name'],
                                                       username   = validated_data['username'],
                                                       password   = validated_data['password'],
                                                       email      = validated_data['email'],
                                                      )
                return user
        
        except IntegrityError:
            raise serializers.ValidationError({"error_message":"Username or email already taken.",
                                               "data":{"username":validated_data["username"],
                                                       "email":validated_data["email"]
                                                      }
                                              })
        



    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError({"error_message":"Invalid credentials.",
                                               "data":{"username":username,
                                                       "password":password
                                                      }
                                             })
        
        if not user.is_active:
            raise serializers.ValidationError({"error_message":"User account is not active.",
                                               "data":{"username":username}
                                             })
        
        attrs["user"] = user
        
        return attrs



class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)

    def validate(self, attrs):
        token = attrs.get("refresh")

        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError({"error_message":"Authentication is needed for this operation."})


        try:
            refresh_token = RefreshToken(token)
        except TokenError:
            raise serializers.ValidationError({"error_message":"Invalid or expired refresh token."})


        if refresh_token.token_type != "refresh":
            raise serializers.ValidationError({"error_message":"Invalid token type."})


        if int(refresh_token.get("user_id")) != request.user.id:
            raise serializers.ValidationError({"error_message":"Refresh token doesn't belong to this user."}) 
        
        
        attrs['refresh_token'] = refresh_token 
        return attrs
    
    def save(self, **kwargs):
        refresh_token = self.validated_data["refresh_token"]
        refresh_token.blacklist()




class CustomRefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)

    def validate(self, attrs):

        token = attrs.get('refresh')

        
        jwt_serializer = TokenRefreshSerializer(data={"refresh":token})

        try:
            jwt_serializer.is_valid(raise_exception=True)
        except TokenError:
            raise serializers.ValidationError({"error_message":"Invalid or expired refresh token."})

        jwt_data = jwt_serializer.validated_data

        access_token = AccessToken(jwt_data.get('access'))
        user_id = access_token["user_id"]


        
        try:
            user_instance = models.User.objects.get(id=user_id)
        except models.User.DoesNotExist:
            raise serializers.ValidationError({"error_message":"User does not exist."})

        if not user_instance.is_active:      
            raise serializers.ValidationError({"error_message":"User account is not active."}) 
        


        attrs["access"]  = jwt_data.get("access")
        attrs["refresh"] = jwt_data.get("refresh")

        if attrs["refresh"] is None:
            raise serializers.ValidationError({"error_message":"Refresh token disabled."})
        
        return attrs
    


class ProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.User
        fields = ["id","username","email","first_name","last_name","is_active","last_login","date_joined"]





class UpdateProfileSerializer(serializers.ModelSerializer):
    username   = serializers.CharField(max_length=30)
    first_name = serializers.CharField(max_length=30)
    last_name  = serializers.CharField(max_length=30) 
    
    class Meta:
        model = models.User
        fields = ["username","email","first_name","last_name"]

    def validate_username(self,value):
        if not re.match(r'^[A-Za-z0-9_]+$',value):
            raise serializers.ValidationError("Username can only contain letters, number, and underscores.")
        
        if models.User.objects.filter(username=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Username already taken.")
        return value
    
    def validate_email(self,value):
        value = value.lower()
        if models.User.objects.filter(email__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Email already taken.")

        return value
    
    def validate_first_name(self,value):
        if not re.fullmatch(r'[A-Za-z]+',value):
            raise serializers.ValidationError("First name can only contain letters.")
        return value
    
    def validate_last_name(self,value):
        if not re.fullmatch(r'[A-Za-z]+( [A-Za-z]+)*',value):
            raise serializers.ValidationError("Last name must only contain letters and spaces.")
        return value
    
    def validate(self, attrs):
        return attrs
    

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"error_message":"Username or email already taken.",
                                               "data":{"username":validated_data.get("username", ""),
                                                       "email":validated_data.get("email", "")
                                                      }
                                             })
        



class UpdatePasswordSerializer(serializers.ModelSerializer):
    old_password     = serializers.CharField(write_only=True, required=True)
    new_password     = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True, min_length=8) 

    class Meta:
        model = models.User
        fields = ["old_password","new_password","confirm_password"]

    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError({"error_message":"Authentication required for this operation."})
        

        user = request.user

        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"error_message":"Current password is incorrect."})

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"error_message":"Passwords do not match."})

        return attrs
    
    def save(self, **kwargs):
        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError({"error_message":"Authentication required for this operation."})


        user = request.user
        new_password = self.validated_data.get("new_password")

        with transaction.atomic():
            user.set_password(new_password)
            user.save()

            refresh_tokens = OutstandingToken.objects.filter(user=user)

            for token in refresh_tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        


class AddressCreateSerializer(serializers.ModelSerializer):
    is_default = serializers.BooleanField(required=False)

    class Meta:
        model = models.AddressModel
        fields = ["id","name","phone","address_line","city","state","pincode","is_default"]
        read_only_fields = ["id"]

    def validate_name(self,value):
        if not re.fullmatch(r'[A-Za-z]+( [A-Za-z]+)*',value):
            raise serializers.ValidationError("Name can only contain letters and spaces.")
        
        return value
    
    def validate_pincode(self,value):
        if not re.fullmatch(r'[0-9]{6}',value):
            raise serializers.ValidationError("Invalid pincode.")
        
        return value
    
    def create(self, validated_data):
        request = self.context.get("request")

        if not request or not request.user:
            raise serializers.ValidationError({"error_message":"Authentication required for this operation."})
        
        validated_data['user'] = request.user

        try:
            current_address = models.AddressModel.objects.filter(user=request.user)

            with transaction.atomic():
                if not current_address.exists():
                    validated_data['is_default'] = True
                else:
                    is_default = validated_data.get('is_default')
                    if is_default and is_default == True:
                        current_address.filter(is_default=True).update(is_default=False)

                return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"error_message":"Only one default address is allowed."})



class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AddressModel
        fields = ["id","name","phone","address_line","city","state","pincode","is_default"]




class AddressUpdateSerializer(serializers.ModelSerializer):
    is_default = serializers.BooleanField(required=False) 

    class Meta:
        model = models.AddressModel
        fields = ["id","name","phone","address_line","city","state","pincode","is_default"]
        read_only_fields = ["id"]


    def validate_name(self,value):
        if not re.fullmatch(r'[A-Za-z]+( [A-Za-z]+)*',value):
            raise serializers.ValidationError("Name can only contain letters and spaces.")
        
        return value
    
    def validate_pincode(self,value):
        if not re.fullmatch(r'[0-9]{6}',value):
            raise serializers.ValidationError("Invalid pincode.")
        
        return value
    

    def update(self, instance, validated_data):
        request = self.context.get('request')

        if not request or not request.user:
            raise serializers.ValidationError({"error_message":"Authentication required for this operation."})
        
        try:
            is_default = validated_data.get('is_default')

            with transaction.atomic():
                if is_default and is_default == True:
                    models.AddressModel.objects.filter(user=request.user,is_default=True).exclude(id=instance.id).update(is_default=False)

                return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"error_message":"Only one default address is allowed."})
    


class AddressNestedSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AddressModel
        fields = ["name","phone","address_line","city","state","pincode",]





class AdminUserListSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.User
        fields = ["id","username","email","first_name","last_name","is_staff","is_superuser","last_login","is_active","date_joined"]



class AdminUserDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.User
        fields = ["id","username","email","first_name","last_name","is_staff","is_superuser","last_login","is_active","date_joined"]


# ---------------------Audit Log --------------------------------



class AdminUserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ["id","username","email"]

class AdminAuditLogListSerializer(serializers.ModelSerializer):
    user = AdminUserNestedSerializer(read_only=True, allow_null=True)
    class Meta:
        model = models.AuditLog
        fields = ["id","action","message","changes","user","model","object_id","created_at"]



class AdminAuditLogDetailSerializer(serializers.ModelSerializer):
    user = AdminUserDetailSerializer(read_only=True, allow_null=True)

    class Meta:
        model = models.AuditLog
        fields = ["id","action","message","changes","user","model","object_id","created_at"]




# -------------------------Order Management ------------------------------

class AdminOrderListSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = orders_models.OrderModel
        fields = ["id","user_email","order_id","status","grand_total","created_at"]





class AdminOrderItemListSerializer(serializers.ModelSerializer):

    class Meta:
        model = orders_models.OrderItemModel
        fields = ["id","product","product_name","brand_name","category_name","product_slug","brand_slug","category_slug","unit_price","quantity","total_price","created_at","updated_at"]


class AdminOrderDetailSerializer(serializers.ModelSerializer):
    user        = AdminUserNestedSerializer(read_only=True)
    order_items = AdminOrderItemListSerializer(source="items",read_only=True, many=True)

    class Meta:
        model = orders_models.OrderModel
        fields = ["id","user","order_items","name","phone","address_line","city","state","pincode","subtotal","shipping_fee","grand_total","status","order_id","created_at","updated_at"]




#class AdminOrderUpdateSerializer(serializers.ModelSerializer):
#    status = serializers.ChoiceField(required=True, choices=orders_models.OrderModel.STATUS_CHOICES)

#    class Meta:
#        model = orders_models.OrderModel
#        fields = ["status"]

#    def validate(self, attrs):               
#        status = attrs["status"]

#        current_status = self.instance.status

#        order_status_flow = orders_models.OrderModel.ORDER_STATUS_FLOW

#        if status == current_status:
#            raise serializers.ValidationError({"error_message":"Order is already in this status.",
#                                               "data":{"current_status":current_status,
#                                                       "new_status":status
#                                                      }
#                                             })
        
#        allowed_next_stages = order_status_flow.get(current_status,[])

#        if status not in allowed_next_stages:
#            raise serializers.ValidationError({"error_message":"Invalid status update request, please check and try again.",
#                                               "data":{"current_status":current_status,
#                                                       "new_status":status,
#                                                       "allowed_next":allowed_next_stages
#                                                      }
#                                             })

#        return attrs
    

#    def update(self, instance, validated_data):
    
#        request = self.context.get("request")
#        if not request or not request.user:
#            raise serializers.ValidationError({"error_message":"Authentication required for this operation."}) 

#        action = "ORDER_STATUS_UPDATE"
#        message = f"Order status of {instance.order_id} changed from {instance.status} -> {validated_data['status']} by {request.user.username}"
#        changes = {"status":{"old":str(instance.status),
#                            "new":str(validated_data["status"])
#                           }
#                  }

        
#        with transaction.atomic():
#            order = super().update(instance, validated_data)
#            create_audit_log(user=request.user,action=action,message=message,instance=order,changes=changes)

#            return order
        



class AdminOrderPaymentHistorySerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source="order.order_id",read_only=True)
    
    class Meta:
        model = payments_model.PaymentModel
        fields = ["id","order_id","method","status","amount","currency","provider_order_id","provider_payment_id","created_at","updated_at"]





#class AdminMarkOrderItemReturnedSerializer(serializers.ModelSerializer):
    #order_id = serializers.CharField(source="order.order_id", read_only=True)

    #class Meta:
        #model = orders_models.OrderItemModel
        #fields = ["id","order_id","status"]
        #read_only_fields = ["id","order_id","status"]

    #def update(self, instance, validated_data):
        
        #if instance.status != "RETURN_REQUESTED": 
            #raise serializers.ValidationError({"error_message":"Order item return request not recieved.",
                                               #"data":{"order_item_id":instance.id,
                                                       #"order_id":instance.order.order_id,
                                                       #"status":instance.status
                                                      #}
                                             #})
        #order = instance.order

        #with transaction.atomic():
            #order = orders_models.OrderModel.objects.select_for_update().get(id=order.id)

            #instance.status = "RETURNED"
            #instance.save(update_fields=["status"])

            #order_items = order.items.all()
            #existing_items = order_items.exclude(status="RETURNED")

            #if not existing_items.exists():
                #order.status = "RETURNED"
                #order.save(update_fields=["status"])


        #return instance




#class OrderRefundInitiateSerializer(serializers.Serializer):
#    order_id      = serializers.CharField(required=False)
#    order_item_id = serializers.IntegerField(required=False)
#    reason        = serializers.CharField(required=True)
#    refund_shipping_fee = serializers.BooleanField(required=True)


#    def validate(self, attrs):
#        order_id = attrs.get("order_id")
#        order_item_id = attrs.get("order_item_id")
#        refund_shipping_fee = attrs.get("refund_shipping_fee")


#       if not order_id and not order_item_id:
#            raise serializers.ValidationError({"error_message":"Provide either order_id for order cancellation or order_item_id for item cancellation.",
#                                               "data":{"order_id":"null",
#                                                       "order_item_id":"null"
#                                                      }
#                                             })

#        if order_id and order_item_id:
#            raise serializers.ValidationError({"error_message":"Cannot accept both order_id and order_item_id.",
#                                               "data":{"order_id":order_id,
#                                                       "order_item_id":order_item_id
#                                                      }
#                                             })



#        if order_id:
#            try:
#                order_instance = orders_models.OrderModel.objects.prefetch_related("items").get(order_id=order_id)
#            except orders_models.OrderModel.DoesNotExist:
#                raise serializers.ValidationError({"error_message":"Invalid order_id",
#                                                   "data":{"order_id":order_id}
#                                                 })
            
#            eligible_items = order_instance.items.filter(status__in=["CANCELLED","RETURNED"]).exclude(item_refunds__status__in=["PENDING","SUCCESS"])
            
#            if not eligible_items.exists():
#                raise serializers.ValidationError({"error_message":"No items in this order available for refund.",
#                                                   "data":{"order_id":order_instance.order_id}
#                                                 })
            

#            attrs["order_instance"] = order_instance
#            attrs["refund_scope"]  = "order"

#            attrs["payment_instance"] = order_instance.payments.all().filter(status="SUCCESS").order_by('-created_at').first()

#            if not attrs["payment_instance"]:
#                raise serializers.ValidationError({"error_message":"Payment info not found.",
#                                                   "data":{"order_id":order_instance.order_id}
#                                                 })


#            attrs["amount"] = sum(item.total_price for item in eligible_items)            

#            if order_instance.shipping_fee != 0.0:
#                if refund_shipping_fee:
#                    attrs["amount"] += order_instance.shipping_fee 
            


#            if attrs["amount"] > attrs["payment_instance"].amount:
#                raise serializers.ValidationError({"error_message":"Refund exceeds paid amount.",
#                                                  "data":{"refund_amount":attrs["amount"],
#                                                          "paid_amount"  :attrs["payment_instance"].amount
#                                                         }
#                                                 })
            

#            attrs["order_item_instance"] = list(eligible_items)



#        elif order_item_id:
#            try:
#                order_item_instance = orders_models.OrderItemModel.objects.prefetch_related("item_refunds").get(id=order_item_id)
#            except orders_models.OrderItemModel.DoesNotExist:
#                raise serializers.ValidationError({"error_message":"Invalid order_item_id",
#                                                   "data":{"order_item_id":order_item_id}
#                                                 })
            
            
#            if order_item_instance.status not in ["CANCELLED","RETURNED"]:
#                raise serializers.ValidationError({"error_message":"Order item refund cannot be initiated.",
#                                                   "data":{"order_item_id":order_item_id,
#                                                           "order_id":order_item_instance.order.order_id,
#                                                           "order_item_status":order_item_instance.status
#                                                          }
#                                                 })
#            
#            if order_item_instance.item_refunds.filter(status__in=["PENDING","SUCCESS"]).exists():
#                raise serializers.ValidationError({"error_message":"Refund request already submitted.",
#                                                   "data":{"order_item_id":order_item_id,
#                                                           "order_id":order_item_instance.order.order_id
#                                                          }
#                                                  })
            
            
#            attrs["order_instance"] = order_item_instance.order
#            attrs["refund_scope"]  = "order_item"
#            attrs["amount"] = order_item_instance.total_price


#            if attrs["order_instance"].items.count() == 1 and attrs["order_instance"].shipping_fee != 0.0:
#                if refund_shipping_fee:
#                    attrs["amount"] += attrs["order_instance"].shipping_fee



#            attrs["payment_instance"] = attrs["order_instance"].payments.all().filter(status="SUCCESS").order_by('-created_at').first()

#            if not attrs["payment_instance"]:
#                raise serializers.ValidationError({"error_message":"Payment info not found.",
#                                                   "data":{"order_id":attrs["order_instance"].order_id,
#                                                           "order_item_id":order_item_instance.id
#                                                          }
#                                                })
            
#            attrs["order_item_instance"] = [order_item_instance]
            
        

#        if attrs["amount"] <= 0:
#            raise serializers.ValidationError({"error_message":"Invalid amount.",
#                                               "data":{"amount":attrs["amount"]}
#                                             })
        


#        return attrs