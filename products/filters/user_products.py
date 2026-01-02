from django.db.models import Q
from rest_framework import serializers as drf_serializers
from decimal import Decimal, InvalidOperation
from products import models


SORT_OPTIONS = {"price_asc":"price",
               "price_desc":"-price",
               "newest":"-created_at",
               "oldest":"created_at"
              }


def user_products_list(request,queryset):

    category  = request.query_params.get("category")
    brand     = request.query_params.get("brand")
    min_price = request.query_params.get("min_price") 
    max_price = request.query_params.get("max_price")
    search    = request.query_params.get("search") 
    sort      = request.query_params.get("sort")
    in_stock  = request.query_params.get("in_stock")



    try:
        if min_price:
            min_price = Decimal(min_price)
        if max_price:
            max_price = Decimal(max_price)
    except InvalidOperation:
        raise drf_serializers.ValidationError({"price":"Invalid price format"})
    


    if category:
        category = category.lower()

        category_instance = models.CategoryModel.objects.filter(slug=category,is_active=True).first()
        
        if category_instance is not None:
            children = category_instance.get_descendants(include_self=True)

            queryset = queryset.filter(category__in=children)
        else:
            queryset = queryset.none()



    if brand:
        brand = brand.lower()

        queryset = queryset.filter(brand__slug=brand)



    if min_price and max_price and min_price > max_price:
        raise drf_serializers.ValidationError({"price":"min_price cannot be greater than max_price."})
        
    if min_price:
        queryset = queryset.filter(price__gte=min_price)
        
    if max_price:
        queryset = queryset.filter(price__lte=max_price)



        
    if search:
        search = search.strip()

        queryset = queryset.filter(Q(name__icontains=search)|
                                   Q(category__name__icontains=search)|
                                   Q(brand__name__icontains=search)|
                                   Q(slug__icontains=search)|
                                   Q(description__icontains=search)
                                   )
            

    if sort:
        sort = sort.lower()

        order_by = SORT_OPTIONS.get(sort)

        if order_by is not None:
            queryset = queryset.order_by(order_by)



    if in_stock:
        in_stock = in_stock.lower()

        if in_stock == "true":
            queryset = queryset.filter(stock__gt=0)
        elif in_stock == "false":
            queryset = queryset.filter(stock=0)


    return queryset