from rest_framework import serializers
from accounts import serializers as accounts_serializers
from carts import serializers as carts_serializers

class CheckoutPreviewSerializer(serializers.Serializer):
    address = accounts_serializers.AddressNestedSerializer(read_only=True)

    cart_items = carts_serializers.CartNestedSerializer(read_only=True, many=True)

    subtotal     = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    grand_total  = serializers.DecimalField(max_digits=10, decimal_places=2)