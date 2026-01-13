from rest_framework import serializers
from accounts import serializers as accounts_serializers

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
