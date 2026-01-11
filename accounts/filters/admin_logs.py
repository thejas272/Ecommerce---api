from rest_framework import serializers as drf_serializers
from django.db.models import Q


MODEL_OPTIONS = {"brand"    : "BrandModel",
                "category" : "CategoryModel",
                "product"  : "ProductModel",
                }
    
ACTIONS = {"LOGIN","LOGOUT","CREATE","UPDATE","SOFT_DELETE"}



def admin_filter_logs(request,queryset):

    user_id   = request.query_params.get("u_id")
    action    = request.query_params.get("action")
    search    = request.query_params.get("search")
    date_from = request.query_params.get("date_from")
    date_to   = request.query_params.get("date_to")
    model     = request.query_params.get("model")
    object_id = request.query_params.get("object_id")




        
    if user_id:
        try:
            user_id = int(user_id)
        except ValueError:
            raise drf_serializers.ValidationError({"error_message":"Invalid user id.",
                                                   "data":{"user_id":user_id}
                                                 })

        queryset = queryset.filter(user_id=user_id)



    if action:
        action = action.upper()

        if action in ACTIONS:
            queryset = queryset.filter(action=action)
        else:
            queryset = queryset.none()




    if search:
        search = search.strip()
        queryset = queryset.filter(Q(action__icontains=search)|
                                   Q(message__icontains=search)|
                                   Q(changes__icontains=search)
                                  )
        




    date_field = drf_serializers.DateField()

    if date_from:
        try:
            date_from = date_field.run_validation(date_from)
        except drf_serializers.ValidationError:
            raise drf_serializers.ValidationError({"error_message":"Invalid date format. Use YYYY-MM-DD.",
                                                   "data":{"date_from":date_from}
                                                 })


    if date_to:
        try:
            date_to = date_field.run_validation(date_to)
        except drf_serializers.ValidationError:
            raise drf_serializers.ValidationError({"error_message":"Invalid date format. Use YYYY-MM-DD.",
                                                   "data":{"date_to":date_to}
                                                 })   


    if date_from and date_to and date_from > date_to:
        raise drf_serializers.ValidationError({"error_message":"date_from cannot be greater than date_to.",
                                               "data":{"date_from":date_from,
                                                       "date_to":date_to
                                                      }
                                             })   
    



    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)

    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    


    if model:
        model = model.lower()

        model_filter = MODEL_OPTIONS.get(model)
        if model_filter is not None:
            queryset = queryset.filter(model=model_filter)
        else:
            queryset = queryset.none()


   
    if object_id:
        queryset = queryset.filter(object_id=object_id)


    return queryset





    

        
    