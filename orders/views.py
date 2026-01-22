from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from orders.helpers import calculate_checkout_price
from django.db import transaction
from common.pagination import DefaultPagination
from rest_framework import serializers as drf_serializers
from products import models as product_models
from payments import models as payment_models
from accounts import models as accounts_models
from carts import models as carts_models
from orders import models as orders_models
from orders.helpers import calculate_checkout_price
from orders import serializers as orders_serializers
from common.helpers import success_response,error_response, normalize_validation_errors
from common.schemas import SuccessResponseSerializer,ErrorResponseSerializer,CheckoutPreviewSuccessResponseSerializer,CreateOrderSuccessResponseSerializer,OrderListSuccessResponseSerializer,OrderDetailSuccessResponseSerializer,OrderCancelSuccessResponseSerializer,OrderItemCancelSuccessResponseSerializer,OrderReturnSuccessResponseSerializer,OrderItemReturnSuccessResponseSerializer

# Create your views here.


class CheckoutPreviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Order"], request_body=None,
                         responses={200: CheckoutPreviewSuccessResponseSerializer,
                                    400 : ErrorResponseSerializer,
                                    500 : ErrorResponseSerializer
                                   }
                        )
    def post(self,request):
        default_address = accounts_models.AddressModel.objects.filter(user=request.user,is_default=True).first()

        if not default_address:
            return error_response(message = "please add an address to continue checkout.",
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )        
        
        cart_items = carts_models.CartModel.objects.filter(user=request.user).select_related('product','product__brand','product__category')
        
        if not cart_items.exists():
            return error_response(message = "Please add items to your cart to checkout.",
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        

        product_ids = cart_items.values_list("product_id",flat=True)
        products = product_models.ProductModel.objects.filter(id__in=product_ids)


        try:
            inactive_products = [product for product in products if not product.is_active]

            if inactive_products:
                raise drf_serializers.ValidationError({"error_message":"Some products are no longer available.",
                                                       "data":[{"product_id":p.id,
                                                                "product_name":p.name,
                                                                "product_slug":p.slug
                                                               }for p in inactive_products
                                                              ]
                                                     })
            
            for item in cart_items:
                product_instance = item.product

                if item.quantity > product_instance.stock:
                    raise drf_serializers.ValidationError({"error_message":"Insuffiecient stock.",
                                                           "data":{"product_id":product_instance.id,
                                                                   "product_name":product_instance.name,
                                                                   "product_slug":product_instance.slug,
                                                                  }
                                                         })


            subtotal,shipping_fee,grand_total = calculate_checkout_price(cart_items)
            data = {
                "address"      : default_address,
                "cart_items"   : cart_items,
                "subtotal"     : subtotal,
                "shipping_fee" : shipping_fee,
                "grand_total"  : grand_total
            }

            serializer = orders_serializers.CheckoutPreviewResponseSerializer(instance=data)

            return success_response(message = "Checkout preview successful.",
                                    data    = serializer.data,
                                    status_code = status.HTTP_200_OK
                                   )
        
        except drf_serializers.ValidationError as e:
            message,data = normalize_validation_errors(e.detail)
            
            return error_response(message = message,
                                  data    = data,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )



class OrderAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    @swagger_auto_schema(tags=["Order"], request_body = orders_serializers.OrderCreateSerializer,
                         responses = {201 : CreateOrderSuccessResponseSerializer,
                                      400 : ErrorResponseSerializer,
                                      500 : ErrorResponseSerializer
                                     }
                        )
    def post(self,request):

        serializer = orders_serializers.OrderCreateSerializer(data=request.data)
        try:
            if serializer.is_valid(raise_exception=True):
                payment_method = serializer.validated_data["payment_method"]

        except drf_serializers.ValidationError as e:
            message,data = normalize_validation_errors(e.detail)
            
            return error_response(message = message,
                                  data    = data,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        

        if payment_method == "COD":

            payment_status   = "PENDING"
            payment_required = False

        elif payment_method == "RAZORPAY":
            
            payment_status   = "PENDING"
            payment_required = True


        default_address = accounts_models.AddressModel.objects.filter(user=request.user,is_default=True).first()

        if not default_address:
            return error_response(message = "Please add an address to place an order.",
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )


        cart_items = carts_models.CartModel.objects.filter(user=request.user).select_related("product","product__brand","product__category")
        
        if not cart_items.exists():
            return error_response(message = "Please add items to your cart place an order.",
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )


        product_ids = cart_items.values_list("product_id", flat=True)

        try:
            with transaction.atomic():
                products = product_models.ProductModel.objects.select_for_update().filter(id__in=product_ids)

                inactive_products = [product for product in products if not product.is_active]

                if inactive_products:
                    raise drf_serializers.ValidationError({"error_message":"Some products are no longer available.",
                                                           "data":[{"product_id":p.id,
                                                                    "product_name":p.name,
                                                                    "product_slug":p.slug
                                                                   }for p in inactive_products
                                                                  ]
                                                          })

                product_map = {product.id : product for product in products}
            
                # stock validation   
                for cart_item in cart_items:
                    product_instance = product_map[cart_item.product_id]

                    if cart_item.quantity > product_instance.stock:
                        raise drf_serializers.ValidationError({"error_message":"Insufficient stock.",
                                                               "data":{"product_id":product_instance.id,
                                                                       "product_name":product_instance.name,
                                                                       "product_slug":product_instance.slug
                                                                      }
                                                              })
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
                                                                    status        = "PENDING"
                                                                    )
                                    )
                orders_models.OrderItemModel.objects.bulk_create(order_items)



                payment_models.PaymentModel.objects.create(order    = order,
                                                           method = payment_method,
                                                           status   = payment_status,
                                                           amount   = grand_total,
                                                           currency = "INR",
                                                          )
                
                cart_items.delete()
                return success_response(message = "Order info created successfuly.",
                                        data    = {"order_id"        : order.order_id,
                                                   "order_status"    : order.status,
                                                   "payment_required": payment_required
                                                  },
                                        status_code = status.HTTP_201_CREATED
                                       )
        
        except drf_serializers.ValidationError as e:
            message,data = normalize_validation_errors(e.detail)
            
            return error_response(message = message,
                                  data    = data,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        

    
    
    @swagger_auto_schema(tags=["Order"], request_body=None, responses={200 : OrderListSuccessResponseSerializer,
                                                                       400 : ErrorResponseSerializer,
                                                                       500 : ErrorResponseSerializer
                                                                      }
                        )
    def get(self,request):
        orders = orders_models.OrderModel.objects.filter(user=request.user).order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders, request)

        serializer = orders_serializers.OrderListSerializer(page, many=True)

        paginated_data = {"count":paginator.page.paginator.count,
                          "next":paginator.get_next_link(),
                          "previous":paginator.get_previous_link(),
                          "results":serializer.data
                         }
        
        return success_response(message = "Order list fetched successfuly.",
                                data = paginated_data,
                                status_code = status.HTTP_200_OK
                               )

    




class OrderDetailAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = "order_id"
    serializer_class = orders_serializers.OrderDetailSerializer
    
    @swagger_auto_schema(tags=["Order"], responses={200: OrderDetailSuccessResponseSerializer,
                                                    404 : ErrorResponseSerializer,
                                                    500 : ErrorResponseSerializer
                                                   }
                        )
    def get(self,request,id):
        try:
            order_instance = orders_models.OrderModel.objects.filter(user=request.user).prefetch_related('items').get(order_id=id)
        except orders_models.OrderModel.DoesNotExist:
            return error_response(message = "Invalid order ID.",
                                  data    = {"order_id":id},
                                  status_code = status.HTTP_404_NOT_FOUND
                                 )
        
        serializer = self.get_serializer(instance=order_instance)

        return success_response(message = "Order detail fetched successfuly,",
                                data    = serializer.data,
                                status_code = status.HTTP_200_OK
                               )
    
    


        
class OrderCancelAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = "order_id"
    serializer_class = orders_serializers.OrderCancelSerializer

    @swagger_auto_schema(tags=["Order"], request_body=None, responses={200 : OrderCancelSuccessResponseSerializer,
                                                                       404 : ErrorResponseSerializer,
                                                                       400 : ErrorResponseSerializer,
                                                                       500 : ErrorResponseSerializer
                                                                      }
                        )
    def patch(self,request,id):
        try:
            order_instance = orders_models.OrderModel.objects.get(order_id=id,user=request.user)
        except orders_models.OrderModel.DoesNotExist:
            return error_response(message = "Invalid order id.",
                                  data={"order_id":id},
                                  status_code = status.HTTP_404_NOT_FOUND
                                 )

        serializer = self.get_serializer(instance=order_instance, data={}, partial=True)

        try:
            if serializer.is_valid():
                serializer.save()
                return success_response(message = "Order cancelled successfuly.",
                                        data    = serializer.data,
                                        status_code = status.HTTP_200_OK
                                       )
        except drf_serializers.ValidationError as e:    
            message,data = normalize_validation_errors(e.detail)

            return error_response(message = message,
                                  data    = data,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        


class OrderItemCancelAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = orders_serializers.OrderItemCancelSerializer
    lookup_field = "id"

    @swagger_auto_schema(tags=["Order"], request_body=None, responses={200 : OrderItemCancelSuccessResponseSerializer,
                                                                       400 : ErrorResponseSerializer,
                                                                       404 : ErrorResponseSerializer,
                                                                       500 : ErrorResponseSerializer
                                                                      }
                        )
    def patch(self,request,id):
        try:
            order_item = orders_models.OrderItemModel.objects.get(id=id,order__user=request.user)
        except orders_models.OrderItemModel.DoesNotExist:
            return error_response(message = "Invalid order item id.",
                                  data    = {"order_item_id":id},
                                  status_code = status.HTTP_404_NOT_FOUND
                                 )
        
        serializer = self.serializer_class(instance=order_item, data={}, context={"request":request})

        try:
            if serializer.is_valid():
                serializer.save()
                return success_response(message = "Item cancelled successfuly.",
                                        data    = serializer.data,
                                        status_code = status.HTTP_200_OK
                                    )
        except drf_serializers.ValidationError as e:
            message,data = normalize_validation_errors(e.detail)

            return error_response(message = message,
                                  data    = data,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )



class OrderReturnAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = orders_serializers.OrderReturnSerializer
    lookup_field = "order_id"

    @swagger_auto_schema(tags=["Order"], request_body=None, responses={200 : OrderReturnSuccessResponseSerializer,
                                                                       500 : ErrorResponseSerializer,
                                                                       400 : ErrorResponseSerializer,
                                                                       404 : ErrorResponseSerializer
                                                                      }
                        )
    def patch(self,request,order_id):
        try:
            order_instance = orders_models.OrderModel.objects.get(user=request.user,order_id=order_id)
        except orders_models.OrderModel.DoesNotExist:
            return error_response(message = "Invalid order id.",
                                  data    = {"order_id":order_id},
                                  status_code = status.HTTP_404_NOT_FOUND
                                 )
        
        serializer = self.serializer_class(instance=order_instance, data={})

        try:
            if serializer.is_valid():
                serializer.save()
                return success_response(message = "Order return request successful.",
                                        data    = serializer.data,
                                        status_code = status.HTTP_200_OK
                                    )
        except drf_serializers.ValidationError as e:
            message,data = normalize_validation_errors(e.detail)

            return error_response(message = message,
                                  data    = data,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        



class OrderItemReturnAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = orders_serializers.OrderItemReturnSerializer
    lookup_field = "id"

    @swagger_auto_schema(tags=["Order"], request_body=None, responses={200 : OrderItemReturnSuccessResponseSerializer,
                                                                       400 : ErrorResponseSerializer,
                                                                       404 : ErrorResponseSerializer,
                                                                       500 : ErrorResponseSerializer
                                                                      }
                        )
    
    def patch(self,request,id):
        try:
            order_item = orders_models.OrderItemModel.objects.get(id=id,order__user=request.user)
        except orders_models.OrderItemModel.DoesNotExist:
            return error_response(message = "Invalid order item id.",
                                  data    = {"order_item_id":id},
                                  status_code = status.HTTP_404_NOT_FOUND 
                                 )
        
        serializer = self.serializer_class(instance=order_item, data={})

        try:
            if serializer.is_valid():
                serializer.save()
                return success_response(message = "Order item return request successful.",
                                        data    = serializer.data,
                                        status_code = status.HTTP_200_OK
                                       )
            
        except drf_serializers.ValidationError as e:
            message,data = normalize_validation_errors(e.detail)

            return error_response(message = message,
                                  data    = data,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )