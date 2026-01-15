from rest_framework import serializers
from accounts import serializers as accounts_serializers
from products import serializers as products_serializers
from carts import serializers as carts_serializers
from orders import serializers as orders_serializers

class ErrorResponseSerializer(serializers.Serializer):
    status  = serializers.BooleanField()
    message = serializers.CharField()
    data    = serializers.DictField(required=False)


class SuccessResponseSerializer(serializers.Serializer):
    status  = serializers.BooleanField()
    message = serializers.CharField()
    data    = serializers.DictField()    
    




#-----------Authentication--------------

class RegisterSuccessResponseSerializer(SuccessResponseSerializer):
    data = accounts_serializers.RegsiterSerializer()



class LoginSuccessSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access  = serializers.CharField()


class LoginSuccessResponseSerializer(SuccessResponseSerializer):
    data = LoginSuccessSerializer()



class RefreshTokenSuccessSerializer(LoginSuccessResponseSerializer):
    
    class Meta:
        ref_name="RefreshTokenSuccessResponse"



#-----------------User--------------------

class ProfileSuccessResponseSerializer(SuccessResponseSerializer):
    data = accounts_serializers.ProfileSerializer()


class UpdateProfileSuccessResponseSerializer(SuccessResponseSerializer):
    data = accounts_serializers.UpdateProfileSerializer()





class CreateAddressSuccessResponse(SuccessResponseSerializer):
    data = accounts_serializers.AddressCreateSerializer()



class AddressPaginatedDataSerializer(serializers.Serializer):
    count    = serializers.IntegerField()
    next     = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results  = accounts_serializers.AddressSerializer(many=True)

class AddressListSuccessResponseSerializer(SuccessResponseSerializer):
    data = AddressPaginatedDataSerializer()




class AddressDeleteResponse(serializers.Serializer):
    address_id = serializers.IntegerField()

class AddressDeleteSuccessResponse(SuccessResponseSerializer):
    data = AddressDeleteResponse()



class UpdateAddressSuccessResponseSerializer(SuccessResponseSerializer):
    data = accounts_serializers.AddressUpdateSerializer()



class AddressDetailSuccessResponse(SuccessResponseSerializer):
    data = accounts_serializers.AddressSerializer()





class UserPaginatedDataSerializer(serializers.Serializer):
    count    = serializers.IntegerField()
    next     = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results  = accounts_serializers.AdminUserListSerializer(many=True)

class UserListSuccessResponseSerializer(SuccessResponseSerializer):
    data = UserPaginatedDataSerializer()




class UserDetailSuccessResponseSerializer(SuccessResponseSerializer):
    data = accounts_serializers.AdminUserDetailSerializer()




class AuditLogPaginatedDataSerializer(serializers.Serializer):
    count    = serializers.IntegerField()
    next     = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results  = accounts_serializers.AdminAuditLogListSerializer()

class AuditLogListSuccessResponseSerializer(SuccessResponseSerializer):
    data = AuditLogPaginatedDataSerializer() 




class AuditLogDetailSuccessResponseSerializer(SuccessResponseSerializer):
    data = accounts_serializers.AdminAuditLogDetailSerializer()





class OrderListPaginatedDataSerializer(serializers.Serializer):
    count    = serializers.IntegerField()
    next     = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results  = accounts_serializers.AdminOrderListSerializer(many=True)

class OrderListSuccessResponseSerializer(SuccessResponseSerializer):
    data = OrderListPaginatedDataSerializer() 



class OrderDetailSuccessResponseSerializer(SuccessResponseSerializer):
    data = accounts_serializers.AdminOrderDetailSerializer()




class OrderUpdateSuccessResponseSerializer(SuccessResponseSerializer):
    data = accounts_serializers.AdminOrderUpdateSerializer()



#---------------Category----------------------

class CategoryCreateSucccessResponseSerializer(SuccessResponseSerializer):
    data = products_serializers.CategoryCreateSerializer()




class AdminCategoryListPaginatedDataSerializer(serializers.Serializer):
    count    = serializers.IntegerField()
    next     = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results  = products_serializers.AdminCategoryListSerializer(many=True)

class AdminCategoryListSuccessResponseSerializer(SuccessResponseSerializer):
    data = AdminCategoryListPaginatedDataSerializer()




class CategoryListPaginatedDateSerializer(serializers.Serializer):
    count    = serializers.IntegerField()
    next     = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results  = products_serializers.CategorySerializer(many=True)

class CategoryListSuccessResponseSerializer(SuccessResponseSerializer):
    data = CategoryListPaginatedDateSerializer()





class CategoryDetailSuccessResponseSerializer(SuccessResponseSerializer):
    data = products_serializers.CategorySerializer()




class CategoryUpdateSuccessResponseSerializer(SuccessResponseSerializer):
    data = products_serializers.CategoryUpdateSerializer()




class CategoryDeleteResponse(serializers.Serializer):
    category_id   = serializers.IntegerField()
    category_name = serializers.CharField()

class CategoryDeletSuccessResponseSerializer(SuccessResponseSerializer):
    data = CategoryDeleteResponse()




class AdminCategoryDetailSuccessResponseSerializer(SuccessResponseSerializer):
    data = products_serializers.AdminCategoryDetailSerializer()





#----------------Brand-------------------


class BrandCreateSuccessResponseSerializer(SuccessResponseSerializer):
    data = products_serializers.BrandCreateSerializer()




class AdminBrandPaginatedDataSerializer(serializers.Serializer):
    count    = serializers.IntegerField()
    next     = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results  = products_serializers.AdminBrandSerializer()

class AdminBrandListSuccessResponseSerializer(SuccessResponseSerializer):
    data = AdminBrandPaginatedDataSerializer()




class BrandListPaginatedDataSerializer(serializers.Serializer):
    count    = serializers.IntegerField()
    next     = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results  = products_serializers.BrandSerializer(many=True)

class BrandListSuccessResponseSerializer(SuccessResponseSerializer):
    data = BrandListPaginatedDataSerializer()






class BrandDetailSuccessResponseSerializer(SuccessResponseSerializer):
    data = products_serializers.BrandSerializer()




class BrandUpdateSuccessResponseSerializer(SuccessResponseSerializer):
    data = products_serializers.BrandUpdateSerializer()




class BrandDeleteResponse(serializers.Serializer):
    brand_id   = serializers.IntegerField()
    brand_name = serializers.CharField()

class BrandDeleteSuccessResponseSerializer(SuccessResponseSerializer):
    data = BrandDeleteResponse()





class AdminBrandDetailSuccessSerializer(SuccessResponseSerializer):
    data = products_serializers.AdminBrandSerializer()




#---------------------Products--------------------------


class ProductCreateSuccessResponseSerializer(SuccessResponseSerializer):
    data = products_serializers.ProductCreateSerializer()



class AdminProductPaginatedDataSerializer(serializers.Serializer):
    count    = serializers.IntegerField()
    next     = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results  = products_serializers.AdminProductListSerializer(many=True)

class AdminProductListSuccessResponseSerializer(SuccessResponseSerializer):
    data = AdminProductPaginatedDataSerializer() 




class ProductPaginatedDataSerializer(serializers.Serializer):
    count    = serializers.IntegerField()
    next     = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results  = products_serializers.ProductSerializer(many=True)

class ProductListSuccessResponseSerializer(SuccessResponseSerializer):
    data = ProductPaginatedDataSerializer() 





class ProductDetailSuccessResponseSerializer(SuccessResponseSerializer):
    data = products_serializers.ProductSerializer()




class ProductUpdateSuccessResponseSerializer(SuccessResponseSerializer):
    data = products_serializers.ProductUpdateSerializer()




class ProductDeleteResponse(serializers.Serializer):
    product_id   = serializers.IntegerField()
    product_name = serializers.CharField()

class ProductDeleteSuccessResponseSerializer(SuccessResponseSerializer):
    data = ProductDeleteResponse()





class AdminProductDetailSuccessResponseSerializer(SuccessResponseSerializer):
    data =  products_serializers.AdminProductDetailSerializer()






#---------------------Carts--------------------------------




class AddToCartSuccessResponseSerializer(SuccessResponseSerializer):
    data = carts_serializers.AddToCartSerializer()





class CartListPaginatedData(serializers.Serializer):
    count = serializers.IntegerField()
    next  = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = carts_serializers.CartListSerializer(many=True)

class CartListSuccessResponseSerializer(SuccessResponseSerializer):
    data = CartListPaginatedData()




class CartItemDeleteResponse(serializers.Serializer):
    cart_id = serializers.IntegerField()

class CartItemDeleteSuccessResponseSerializer(SuccessResponseSerializer):
    data = CartItemDeleteResponse()





class UpdateCartQuantitySuccessResponseSerializer(SuccessResponseSerializer):
    data = carts_serializers.UpdateCartQuantitySerializer()




#------------------Order-----------------------

class CheckoutPreviewSuccessResponseSerializer(SuccessResponseSerializer):
    data = orders_serializers.CheckoutPreviewResponseSerializer()






class CreateOrderResponse(serializers.Serializer):
    order_id         = serializers.IntegerField()
    order_status     = serializers.CharField()
    payment_required = serializers.BooleanField()
    
class CreateOrderSuccessResponseSerializer(SuccessResponseSerializer):
    data = CreateOrderResponse()





class OrderListPaginatedData(serializers.Serializer):
    count    = serializers.IntegerField()
    next     = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results  = orders_serializers.OrderListSerializer(many=True)

class OrderListSuccessResponseSerializer(SuccessResponseSerializer):
    data = OrderListPaginatedData()




class OrderDetailSuccessResponseSerializer(SuccessResponseSerializer):
    data = orders_serializers.OrderDetailSerializer()





class OrderCancelSuccessResponseSerializer(SuccessResponseSerializer):
    data = orders_serializers.OrderCancelSerializer()







#--------------------Payments -----------------------

class PaymentInitiateResponse(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_key = serializers.CharField()
    order_id = serializers.CharField()
    amount   = serializers.IntegerField()
    currency = serializers.CharField() 
    
class PaymentInitiateSuccessResponseSerializer(SuccessResponseSerializer):
    data = PaymentInitiateResponse()