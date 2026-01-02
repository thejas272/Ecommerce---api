from django.db.models import Q
from rest_framework import serializers as drf_serializers
from decimal import Decimal, InvalidOperation
from products import models


def admin_products_list(request,queryset):


    category_slug = request.query_params.get("category")
    brand_slug    = request.query_params.get("brand")
    search        = request.query_params.get("search")
    min_price     = request.query_params.get("min_price")
    max_price     = request.query_params.get("max_price")
    is_active     = request.query_params.get("is_active") 


    try:
        if min_price:
            min_price = Decimal(min_price)
        if max_price:
            max_price = Decimal(max_price)
    except InvalidOperation:
        raise drf_serializers.ValidationError({"price":"Invalid price format."})
    


    if category_slug:
        category_slug = category_slug.lower()

        category_instance = models.CategoryModel.objects.filter(slug=category_slug).first()

        if category_instance is not None:
            children = category_instance.get_descendants(include_self=True)
            queryset = queryset.filter(category__in=children)
        else:
            queryset = queryset.none()
    

        
    if brand_slug:
        brand_slug = brand_slug.lower()

        queryset = queryset.filter(brand__slug=brand_slug)



    if search:
        search = search.strip()

        queryset = queryset.filter(Q(slug__icontains=search)| 
                                   Q(name__icontains=search)| 
                                   Q(category__slug__icontains=search)| 
                                   Q(brand__slug__icontains=search)|
                                   Q(description__icontains=search)
                                  )



    if min_price:
        queryset = queryset.filter(price__gte=min_price)
        
    if max_price:
        queryset = queryset.filter(price__lte=max_price)




    if is_active:
        is_active = is_active.lower()

        if is_active == "false":
            queryset = queryset.filter(is_active=False)
        elif is_active == "true":
            queryset = queryset.filter(is_active=True)
    
        
    
    
    return queryset