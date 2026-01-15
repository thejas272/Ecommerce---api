from rest_framework import serializers




class PaymentInitiateSerializer(serializers.Serializer):
    order_id = serializers.CharField(required=True)

