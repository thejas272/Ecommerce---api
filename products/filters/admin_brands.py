from django.db.models import Q
from rest_framework import serializers as drf_serializers



def admin_brand_list(request,queryset):
    

    is_active  = request.query_params.get("is_active")
    brand_slug = request.query_params.get("brand")
    search     = request.query_params.get("search")


    if is_active:
        is_active = is_active.lower()

        if is_active == "true":
            queryset = queryset.filter(is_active=True)
        elif is_active == "false":
            queryset = queryset.filter(is_active=False)


    if brand_slug:
        brand_slug = brand_slug.lower()

        queryset = queryset.filter(slug=brand_slug)


    if search:
        search = search.strip()

        queryset = queryset.filter(Q(slug__icontains=search)|
                                   Q(name__icontains=search)
                                  )


    return queryset