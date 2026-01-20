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
        



        payment_instance = payments_model.PaymentModel.objects.filter(order=order_instance,method="RAZORPAY",status="PENDING").first()

        if not payment_instance:
            return error_response(message = "Payment not eligible for initiation.",
                                  data    = {"order_id":order_id},
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        
        if payment_instance.provider_order_id:
            return success_response(message = "payment was already initiated.",
                                    data    = {"razorpay_order_id":payment_instance.provider_order_id,
                                               "razorpay_key": settings.RAZORPAY_KEY_ID,
                                               "order_id":order_id,
                                               "amount": int(payment_instance.amount*100),
                                               "currency":"INR"
                                               },
                                    status_code = status.HTTP_200_OK
                                   )
        



        try:
        
            razorpay_order = razorpay_client.order.create({"amount":int(payment_instance.amount*100),
                                                           "currency":"INR",
                                                           "receipt":order_id
                                                          }
                                                         )
            logger.info("Razorpay order created",extra={"order_id":order_id,
                                                        "razorpay_order_id":razorpay_order["id"]
                                                       }
                       )
        
        except razorpay.errors.RazorpayError:
            logger.warning("Razorpay failed to respond for order creation",extra={"order_id":order_id})

            return error_response(message = "Payment gateway failed, please try again.",
                                  status_code = status.HTTP_502_BAD_GATEWAY
                                 )
    

    
        with transaction.atomic():
            payment_instance.provider_order_id = razorpay_order["id"]
            payment_instance.save()


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
                payment_instance = payments_model.PaymentModel.objects.select_for_update().select_related('order').get(provider_order_id=razorpay_order_id)

                if payment_instance.status == "SUCCESS":
                    logger.info("Reattempt by webhook", extra={"razorpay_order_id":razorpay_order_id,
                                                               "razorpay_payment_id":razorpay_payment_id
                                                              }
                               )
                    return Response(status=200)
                


                if payment_status == "captured":

                    payment_instance.status="SUCCESS"
                    payment_instance.provider_payment_id = razorpay_payment_id
                    payment_instance.save()

                    payment_instance.order.status = "PAID"
                    payment_instance.order.save()

                    logger.info("Payment captured successfuly", extra={"razorpay_order_id":razorpay_order_id,
                                                                        "razorpay_payment_id":razorpay_payment_id
                                                                       }
                               )

                elif payment_status == "failed":

                    payment_instance.status = "FAILED"
                    payment_instance.provider_payment_id = razorpay_payment_id
                    payment_instance.save()

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

        if serializer.is_valid(raise_exception=True):
            order_id = serializer.validated_data["order_id"]

        try:
            order_instance = orders_model.OrderModel.objects.get(order_id=order_id,user=request.user)
        except orders_model.OrderModel.DoesNotExist:
            return error_response(message = "Invalid order id",
                                  data={"order_id":order_id},
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        
        if order_instance.status == "PAID":
            return error_response(message = "Payment already done.",
                                  data    = order_id,
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        

        
        prev_payment_instance = payments_model.PaymentModel.objects.filter(order=order_instance,method="RAZORPAY").order_by('-created_at').first()
        
        if not prev_payment_instance:
            return error_response(message = "No initial payment attempt found.",
                                  data    = {"order_id":order_id},
                                  status_code = status.HTTP_404_NOT_FOUND
                                 )
        
        if prev_payment_instance.status == "SUCCESS":
            return error_response(message = "Payment already completed.",
                                  data    = {"order_id":order_id},
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        
        if prev_payment_instance.status == "REFUNDED":
            return error_response(message = "Payment was refunded, retry not available.",
                                  data    = {"order_id":order_id},
                                  status_code = status.HTTP_400_BAD_REQUEST
                                 )
        
        cutoff_time = timezone.now() - timedelta(minutes=15)
        
        if prev_payment_instance.status == "PENDING":
            if prev_payment_instance.created_at >= cutoff_time:
                return error_response(message = "Previous payment is still in progress.",
                                      data    = {"order_id":order_id},
                                      status_code = status.HTTP_409_CONFLICT
                                     )
     

        logger.info("Payment retry initiated",extra={"order_id":order_id,
                                                     "previous_payment_status":prev_payment_instance.status,
                                                     "previous_payment_id":prev_payment_instance.id
                                                    }
                   )

        try:
            razorpay_order = razorpay_client.order.create(amount  = int(order_instance.grand_total * 100),
                                                          receipt = order_id,
                                                          currency = "INR"
                                                         )
        except razorpay.errors.RazorpayError:
            logger.warning("Razorpay failed to respond to payment reattempt.",extra={"order_id":order_id})

            return error_response(message = "Payment gateway unavailable.",
                                  status_code = status.HTTP_502_BAD_GATEWAY
                                 )
        
        with transaction.atomic():
            payments_model.PaymentModel.objects.create(order    = order_instance,
                                                    method   = "RAZORPAY",
                                                    status   = "PENDING",
                                                    amount   = order_instance.grand_total,
                                                    currency = "INR",
                                                    provider_order_id = razorpay_order["id"]
                                                    )
            prev_payment_instance.status = "FAILED"
            prev_payment_instance.save()
        
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
        
