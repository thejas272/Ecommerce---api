from rest_framework import serializers as drf_serializers
from django.db.models import Q


# filter users for admin only api

def admin_filter_users(request,queryset):

    search      = request.query_params.get("search")
    is_staff    = request.query_params.get("is_staff")
    is_active   = request.query_params.get("is_active")
    date_from   = request.query_params.get("date_from")
    date_to     = request.query_params.get("date_to")





    if search:
        queryset = queryset.filter(Q(username__icontains=search) |
                                   Q(email__icontains=search) |
                                   Q(first_name__icontains=search) |
                                   Q(last_name__icontains=search)
                                   )
                


    if is_staff:
        is_staff = is_staff.lower()

        if is_staff == "true":
            queryset = queryset.filter(is_staff=True)
        elif is_staff == "false":
            queryset = queryset.filter(is_staff=False)

    

    if is_active:
        is_active = is_active.lower()

        if is_active == "true":
            queryset = queryset.filter(is_active=True)
        elif is_active == "false":
            queryset = queryset.filter(is_active=False)
    



    date_field = drf_serializers.DateField()

    if date_from:
        try:
            date_from = date_field.run_validation(date_from)
        except drf_serializers.ValidationError:
            raise drf_serializers.ValidationError({"date_from":"Invalid date format. Use YYYY-MM-DD."})

    if date_to:
        try:
            date_to = date_field.run_validation(date_to)
        except drf_serializers.ValidationError:
            raise drf_serializers.ValidationError({"date_to":"Invalid date format. Use YYYY-MM-DD."})


    if date_from and date_to and date_from > date_to:
        raise drf_serializers.ValidationError({"date_range":"date_from cannot be greater than date_to."})


    if date_from:
        queryset = queryset.filter(date_joined__date__gte=date_from)

    if date_to:
        queryset = queryset.filter(date_joined__date__lte=date_to) 

    return queryset


        

