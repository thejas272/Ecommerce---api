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
from common.schemas import ErrorResponseSerializer,PaymentInitiateSuccessResponseSerializer
import razorpay
import json
from rest_framework.response import Response
from django.db import transaction
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

