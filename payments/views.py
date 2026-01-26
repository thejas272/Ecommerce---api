from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from payments import serializers as payments_serializers
from orders import models as orders_model
from payments import models as payments_model
from common.helpers import error_response,success_response,normalize_validation_errors
from rest_framework import status
from payments.razorpay import razorpay_client
from django.conf import settings
from rest_framework import serializers as drf_serializers
from common.schemas import ErrorResponseSerializer,PaymentInitiateSuccessResponseSerializer,PaymentStatusSuccessResponseSerializer
import razorpay
import json
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal,ROUND_HALF_UP
import logging
logger = logging.getLogger("payments")

# Create your views here.


class PaymentInitiateAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = payments_serializers.PaymentInitiateSerializer

    @swagger_auto_schema(tags=["Payment"], request_body = payments_serializers.PaymentInitiateSerializer,
                         responses = {200 : PaymentInitiateSuccessResponseSerializer,
                                      500 : ErrorResponseSerializer,
                                      400 : ErrorResponseSerializer,
                                      404 : ErrorResponseSerializer,
                                      502 : ErrorResponseSerializer
                                     }
                        )
    def post(self,request):

        serializer = self.serializer_class(data=request.data)
        
        try:
            if serializer.is_valid(raise_exception = True):
                order_id = serializer.validated_data["order_id"]
        
            order_instance = orders_model.OrderModel.objects.get(order_id=order_id,user=request.user)

        except drf_serializers.ValidationError as e:
            message,data = normalize_validation_errors(e.detail)

            return error_response(message = message,
                                  data    = data,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )

        except orders_model.OrderModel.DoesNotExist:
            return error_response(message = "Invalid order id.",
                                  data    = {"order_id":order_id},
                                  status_code = status.HTTP_404_NOT_FOUND
                                 )
        

        if order_instance.status == "PAID":
            return error_response(message = "Order already paid.",
                                  data    = {"order_id":order_id},
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )


        if order_instance.items.filter(status__in=orders_model.OrderItemModel.BLOCKED_STATUSES_PAYMENT).exists():
            return error_response(message = "Payment cannot be made for this order.",
                                  data    = {"order_id":order_id},
                                  status_code =  status.HTTP_409_CONFLICT
                                 )
        
        try:
            with transaction.atomic():

                payment_instance = payments_model.PaymentModel.objects.select_for_update().filter(order=order_instance,method="RAZORPAY",status="PENDING").first()
                
                if not payment_instance:
                    raise drf_serializers.ValidationError({"error_message":"Payment not eligible.",
                                                           "data":{"order_id":order_id}
                                                         })
                

                razorpay_amount = int((payment_instance.amount * Decimal(100)).quantize(Decimal("1"),rounding=ROUND_HALF_UP))
                
                if payment_instance.provider_order_id:
                    return success_response(message = "payment was already initiated.",
                                            data    = {"razorpay_order_id":payment_instance.provider_order_id,
                                                       "razorpay_key": settings.RAZORPAY_KEY_ID,
                                                       "order_id":order_id,
                                                       "amount": razorpay_amount,
                                                       "currency":"INR"
                                                      },
                                            status_code = status.HTTP_200_OK
                                        )
                

                payment_processing_timeout = timezone.now() - timedelta(minutes=2)

                if payment_instance.processing_started_at:
                    if payment_instance.processing_started_at >= payment_processing_timeout:
                        raise drf_serializers.ValidationError({"error_message":"Payment is already being processed.",
                                                               "data":{"order_id":order_id}
                                                             })

                payment_instance.processing_started_at = timezone.now()
                payment_instance.save(update_fields=["processing_started_at"])

        except drf_serializers.ValidationError as e:
            message,data = normalize_validation_errors(e.detail)

            return error_response(message = message,
                                  data    = data,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        
            



        try:

            razorpay_order = razorpay_client.order.create({"amount":razorpay_amount,
                                                           "currency":"INR",
                                                           "receipt":order_id
                                                         })
            
            logger.info("Razorpay order created",extra={"order_id":order_id,
                                                        "razorpay_order_id":razorpay_order["id"]
                                                       }
                       )
        
        except razorpay.errors.RazorpayError:
            with transaction.atomic():
                payment_instance = payments_model.PaymentModel.objects.select_for_update().get(id=payment_instance.id)
                payment_instance.processing_started_at = None
                payment_instance.save(update_fields=["processing_started_at"])

            logger.warning("Razorpay failed to respond for order creation",extra={"order_id":order_id})

            return error_response(message = "Payment gateway failed, please try again.",
                                  status_code = status.HTTP_502_BAD_GATEWAY
                                 )
    

    
        with transaction.atomic():
            payment_instance = payments_model.PaymentModel.objects.select_for_update().get(id=payment_instance.id)
            
            payment_instance.provider_order_id = razorpay_order["id"]
            payment_instance.processing_started_at = None 
            payment_instance.save(update_fields=["provider_order_id","processing_started_at"])


        return success_response(message = "Payment initiation successful",
                                data    = {"razorpay_order_id":razorpay_order["id"],
                                           "razorpay_key":settings.RAZORPAY_KEY_ID,
                                           "order_id":order_id,
                                           "amount":razorpay_order["amount"],
                                           "currency":"INR"
                                          },
                                status_code = status.HTTP_200_OK
                               )
    



class PaymentWebhookAPIView(GenericAPIView):
    permission_classes = []
    swagger_schema=None

    def post(self,request):
        payload = request.body.decode('utf-8')
        received_signature = request.headers.get("X-Razorpay-Signature")

        logger.info("Webhook recieved")

        if not received_signature:
            logger.warning("Signature missing in header")
            return Response(status=200)
        

        try:
            razorpay_client.utility.verify_webhook_signature(payload,
                                                             received_signature,
                                                             settings.RAZORPAY_WEBHOOK_SECRET
                                                            )
            logger.info("Signature verification successful")
        
        except razorpay.errors.SignatureVerificationError:
            logger.warning("Signature verification failed")
            return Response(status=200)
        


        payload = json.loads(payload)

        event = payload.get("event")
        if event not in ["payment.captured","payment.failed"]:
            return Response(status=200)
        
        try:
            payment_entity = payload["payload"]["payment"]["entity"]
        except KeyError:
            logger.warning("Razorpay payload is not correct")
            return Response(status=200)


        razorpay_order_id   = payment_entity["order_id"]
        razorpay_payment_id = payment_entity["id"]
        payment_status      = payment_entity["status"] 


        try: 
            with transaction.atomic():
                payment_instance = payments_model.PaymentModel.objects.select_for_update().get(provider_order_id=razorpay_order_id)

                if payment_instance.status in ["SUCCESS","FAILED","REFUNDED"]:    
                    logger.info("Reattempt by webhook", extra={"razorpay_order_id":razorpay_order_id,
                                                               "razorpay_payment_id":razorpay_payment_id,
                                                               "payment_status":payment_instance.status
                                                              }
                               )
                    return Response(status=200)
                

                order = orders_model.OrderModel.objects.select_for_update().get(id=payment_instance.order.id)
                order_items = orders_model.OrderItemModel.objects.select_for_update().filter(order=order,status="PENDING")                


                if payment_status == "captured":
    
                    payment_instance.status = "SUCCESS"
                    payment_instance.provider_payment_id = razorpay_payment_id
                    payment_instance.save(update_fields=["status","provider_payment_id"])
    

                    order.status = "PAID"
                    order.save(update_fields=["status"])

                    order_items.update(status="PAID")

                    logger.info("Payment captured successfuly", extra={"razorpay_order_id":razorpay_order_id,
                                                                        "razorpay_payment_id":razorpay_payment_id
                                                                       }
                               )

                elif payment_status == "failed":

                    payment_instance.status = "FAILED"
                    payment_instance.provider_payment_id = razorpay_payment_id

                    payment_instance.save(update_fields=["status","provider_payment_id"])

                    logger.info("Payment failed", extra={"razorpay_order_id":razorpay_order_id,
                                                         "razorpay_payment_id":razorpay_payment_id
                                                        }
                               )

            return Response(status=200)

        
        except payments_model.PaymentModel.DoesNotExist:
            logger.warning("Payment record not found", extra={"razorpay_order_id":razorpay_order_id,
                                                              "razorpay_payment_id":razorpay_payment_id
                                                             }
                          )
            return Response(status=200)



class PaymentRetryAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = payments_serializers.PaymentInitiateSerializer
    @swagger_auto_schema(tags=["Payment"], request_body=payments_serializers.PaymentInitiateSerializer,
                         responses={200 : PaymentInitiateSuccessResponseSerializer,
                                    500 : ErrorResponseSerializer,
                                    400 : ErrorResponseSerializer,
                                    404 : ErrorResponseSerializer,
                                    409 : ErrorResponseSerializer,
                                    502 : ErrorResponseSerializer
                                    })

    def post(self,request):
        serializer = self.serializer_class(data=request.data)

        try:
            if serializer.is_valid(raise_exception=True):
                order_id = serializer.validated_data["order_id"]
            
            order_instance = orders_model.OrderModel.objects.get(order_id=order_id,user=request.user)        


            if order_instance.status == "PAID":
                raise drf_serializers.ValidationError({"error_message":"Payment already done",
                                                           "data":{"order_id":order_id}
                                                         })
                

            if order_instance.items.filter(status__in=orders_model.OrderItemModel.BLOCKED_STATUSES_PAYMENT).exists():
                raise drf_serializers.ValidationError({"error_message":"Payment cannot be made for this order",
                                                       "data":{"order_id":order_id}
                                                     })

            with transaction.atomic():

                prev_payment_instance = payments_model.PaymentModel.objects.select_for_update().filter(order=order_instance,method="RAZORPAY").order_by('-created_at').first()
                

                if not prev_payment_instance:
                    raise drf_serializers.ValidationError({"error_message":"No initial payment attempt found.",
                                                           "data":{"order_id":order_id}
                                                         })
                

                if prev_payment_instance.status == "SUCCESS":
                    raise drf_serializers.ValidationError({"error_message":"Payment already completed",
                                                           "data":{"order_id":order_id}
                                                         })
                
                
                if prev_payment_instance.status == "REFUNDED":
                    raise drf_serializers.ValidationError({"error_message":"Payment was refunded, retry not available",
                                                           "data":{"order_id":order_id}
                                                         })
                
                
                cutoff_time = timezone.now() - timedelta(minutes=15)
                
                if prev_payment_instance.status == "PENDING":
                    if prev_payment_instance.created_at >= cutoff_time:
                        raise drf_serializers.ValidationError({"error_message":"Previous payment is still in progress",
                                                               "data":{"order_id":order_id}
                                                             })
                    
                
                payment_processing_timeout = timezone.now() - timedelta(minutes=2)

                if prev_payment_instance.processing_started_at:
                    if prev_payment_instance.processing_started_at >= payment_processing_timeout:
                        raise drf_serializers.ValidationError({"error_message":"Payment is being processed.",
                                                               "data":{"order_id":order_id}
                                                             })


                prev_payment_instance.processing_started_at = timezone.now()
                prev_payment_instance.save(update_fields=["processing_started_at"])
                    
                    
        except drf_serializers.ValidationError as e:
            message,data = normalize_validation_errors(e.detail)

            return error_response(message = message,
                                  data    = data,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        
        except orders_model.OrderModel.DoesNotExist:
            return error_response(message = "Invalid order id",
                                  data={"order_id":order_id},
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        

        

        try:
            razorpay_amount = int((prev_payment_instance.amount * Decimal(100)).quantize(Decimal("1"),rounding=ROUND_HALF_UP))

            razorpay_order = razorpay_client.order.create(amount  = razorpay_amount,
                                                          receipt = order_id,
                                                          currency = "INR"
                                                         )
            
        except razorpay.errors.RazorpayError:
            with transaction.atomic():
                prev_payment_instance = payments_model.PaymentModel.objects.select_for_update().get(id=prev_payment_instance.id)
                prev_payment_instance.processing_started_at = None 
                prev_payment_instance.save(update_fields=["processing_started_at"])

            logger.warning("Razorpay failed to respond to payment reattempt.",extra={"order_id":order_id})

            return error_response(message = "Payment gateway unavailable.",
                                  status_code = status.HTTP_502_BAD_GATEWAY
                                 )
        

        with transaction.atomic():
            prev_payment_instance = payments_model.PaymentModel.objects.select_for_update().get(id=prev_payment_instance.id)
            
            payments_model.PaymentModel.objects.create(order    = order_instance,
                                                       method   = "RAZORPAY",
                                                       status   = "PENDING",
                                                       amount   = prev_payment_instance.amount,
                                                       currency = "INR",
                                                       provider_order_id = razorpay_order["id"]
                                                      )
            prev_payment_instance.status = "FAILED"
            prev_payment_instance.processing_started_at = None
            prev_payment_instance.save(update_fields=["status","processing_started_at"])


        logger.info("Payment retry initiated",extra={"order_id":order_id,
                                                     "previous_payment_status":prev_payment_instance.status,
                                                     "previous_payment_id":prev_payment_instance.id
                                                    }
                   )
        
        return success_response(message = "Payment re-initiation successful",
                                data    = {"razorpay_order_id":razorpay_order["id"],
                                           "razorpay_key":settings.RAZORPAY_KEY_ID,
                                           "order_id":order_id,
                                           "amount":razorpay_order["amount"],
                                           "currency":razorpay_order["currency"],
                                          },
                                status_code = status.HTTP_200_OK
                                )
        
        

        


class PaymentStatusAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = payments_serializers.PaymentStatusSerializer
    lookup_field = "order_id"

    @swagger_auto_schema(tags=["Payment"],
                        responses = {200 : PaymentStatusSuccessResponseSerializer,
                                     500 : ErrorResponseSerializer,
                                     404 : ErrorResponseSerializer
                                    }
                       )
    def get(self,request,order_id):
        try:
            order_instance = orders_model.OrderModel.objects.get(order_id=order_id,user=request.user)
        except orders_model.OrderModel.DoesNotExist:
            return error_response(message = "Invalid order id",
                                  data    = {"order_id":order_id},
                                  status_code = status.HTTP_404_NOT_FOUND
                                 )
        
        if not order_instance.payments.exists():
            return error_response(message = "No payment attempts done.",
                                  data    =  {"order_id":order_id},
                                  status_code = status.HTTP_404_NOT_FOUND
                                 )
        
        payment_instance = order_instance.payments.order_by('-created_at').first()

        cutoff_time = timezone.now() - timedelta(minutes=15)
        retry_allowed = False
        if payment_instance.status == "FAILED" or (payment_instance.status == "PENDING" and payment_instance.created_at < cutoff_time):
            retry_allowed = True 

        
        data = {"order_id":order_instance.order_id,
                "order_status":order_instance.status,
                "payment_status": payment_instance.status,
                "retry_allowed": retry_allowed
               }
        
        serializer = self.serializer_class(instance=data)

        return success_response(message = "Payment status fetched successfuly.",
                                data    = serializer.data,
                                status_code = status.HTTP_200_OK
                               )
        
