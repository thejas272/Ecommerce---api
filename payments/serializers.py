from rest_framework import serializers




class PaymentInitiateSerializer(serializers.Serializer):
    order_id = serializers.CharField(required=True)




class PaymentStatusSerializer(serializers.Serializer):
    order_id       = serializers.CharField(read_only=True)
    order_status   = serializers.CharField(read_only=True)
    payment_status = serializers.CharField(read_only=True)
    retry_allowed  = serializers.BooleanField(read_only=True)
