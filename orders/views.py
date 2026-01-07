from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from orders.serializers import CheckoutPreviewSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from orders.helpers import calculate_checkout_price
from django.db import transaction
from rest_framework import serializers as drf_serializers
from products import models as product_models
from payments import models as payment_models
from accounts import models as accounts_models
from carts import models as carts_models
from orders import models as orders_models
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
        
        product_ids = cart_items.values_list("product_id",flat=True)
        products = product_models.ProductModel.objects.filter(id__in=product_ids)

        inactive_products = [product for product in products if not product.is_active]

        if inactive_products:
            raise drf_serializers.ValidationError({"product_id":p.id,
                                                   "product_name":p.name,
                                                   "product_slug":p.slug
                                                   }for p in inactive_products
                                                 )

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
    


class OrderCreateAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Order"])
    def post(self,request):
        default_address = accounts_models.AddressModel.objects.filter(user=request.user,is_default=True).first()

        if not default_address:
            return Response({"detail":"Please add a address to place an order."},status=status.HTTP_400_BAD_REQUEST)

        cart_items = carts_models.CartModel.objects.filter(user=request.user).select_related("product","product__brand","product__category")
        
        if not cart_items.exists():
            return Response({"detail":"Please add items to your cart place an order."}, status=status.HTTP_400_BAD_REQUEST)
        
        
        product_ids = cart_items.values_list("product_id", flat=True)

        with transaction.atomic():

            products = product_models.ProductModel.objects.select_for_update().filter(id__in=product_ids) 

            inactive_products = [product for product in products if not product.is_active]

            if inactive_products:
                raise drf_serializers.ValidationError({"product_id":p.id,
                                                       "product_name":p.name,
                                                       "product_slug":p.slug,
                                                       "message":"Product unavailable."
                                                       } for p in inactive_products
                                                     )

            product_map = {product.id : product for product in products}
           
            # stock validation   
            for cart_item in cart_items:
                product_instance = product_map[cart_item.product_id]

                if cart_item.quantity > product_instance.stock:
                    raise drf_serializers.ValidationError({"product_id":product_instance.id,
                                                           "product_name":product_instance.name,
                                                           "product_slug":product_instance.slug,
                                                           "message":"Insufficient stock."
                                                          }
                                                         )
                else:
                    product_instance.stock = product_instance.stock - cart_item.quantity

            product_models.ProductModel.objects.bulk_update(products, ["stock"])



            subtotal,shipping_fee,grand_total = calculate_checkout_price(cart_items)
            
            order = orders_models.OrderModel.objects.create(user         = request.user,
                                                            name         = default_address.name,
                                                            phone        = default_address.phone,
                                                            address_line = default_address.address_line,
                                                            city         = default_address.city,
                                                            state        = default_address.state,
                                                            pincode      = default_address.pincode,
                                                            subtotal     = subtotal,
                                                            shipping_fee = shipping_fee,
                                                            grand_total  = grand_total,
                                                            )
            order_items = []
            for cart_item in cart_items:
                order_items.append(orders_models.OrderItemModel(order         = order,
                                                                product       = cart_item.product,
                                                                product_name  = cart_item.product.name,
                                                                brand_name    = cart_item.product.brand.name,
                                                                category_name = cart_item.product.category.name,
                                                                product_slug  = cart_item.product.slug,
                                                                brand_slug    = cart_item.product.brand.slug,
                                                                category_slug = cart_item.product.category.slug,
                                                                unit_price    = cart_item.unit_price,
                                                                quantity      = cart_item.quantity,
                                                                total_price   = cart_item.total_price,
                                                                )
                                  )
            orders_models.OrderItemModel.objects.bulk_create(order_items)

            payment_models.PaymentModel.objects.create(order = order,
                                                       provider = "COD",
                                                       status = "PENDING",
                                                       amount = grand_total,
                                                       currency = "INR",
                                                       )
            
            cart_items.delete()
        return Response({"order_id":order.order_id,
                         "status":order.status,
                         "detail":"Order created."
                        }, status=status.HTTP_201_CREATED)



            