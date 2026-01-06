from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from orders.serializers import CheckoutPreviewSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from accounts import models as accounts_models
from carts import models as carts_models
from orders.helpers import calculate_checkout_price

# Create your views here.


class CheckoutPreviewAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutPreviewSerializer

    @swagger_auto_schema(tags=["Order"])
    def post(self,request):
        default_address = accounts_models.AddressModel.objects.filter(user=request.user,is_default=True).first()

        if not default_address:
            return Response({"detail":"please add a address to continue checkout."},status=status.HTTP_400_BAD_REQUEST)
        
        cart_items = carts_models.CartModel.objects.filter(user=request.user).select_related('product','product__brand','product__category')
        
        if not cart_items.exists():
            return Response({"detail":"Please add items to your cart to checkout."},status=status.HTTP_400_BAD_REQUEST)
        

        subtotal,shipping_fee,grand_total = calculate_checkout_price(cart_items)
        data = {
            "address"      : default_address,
            "cart_items"   : cart_items,
            "subtotal"     : subtotal,
            "shipping_fee" : shipping_fee,
            "grand_total"  : grand_total
        }

        serializer = self.serializer_class(instance=data)

        return Response(serializer.data, status=status.HTTP_200_OK)