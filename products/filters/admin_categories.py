from django.db.models import Q
from rest_framework import serializers as drf_serializers



def admin_category_list(request,queryset):

    
    is_active     = request.query_params.get("is_active")
    parent        = request.query_params.get("parent")
    category_slug = request.query_params.get("category")
    search        = request.query_params.get("search")


    if is_active:
        is_active = is_active.lower()

        if is_active == "true":
            queryset = queryset.filter(is_active=True)
        elif is_active == "false":
            queryset = queryset.filter(is_active=False)


        
    if parent:
        parent = parent.lower()
        
        if parent == "null":
            queryset = queryset.filter(level=0)
        else:
            category   = queryset.filter(slug=parent).first()
            if category is None:
                queryset = queryset.none()
            else:
                queryset = category.get_children()  


    if category_slug:
        category_slug = category_slug.lower()

        queryset = queryset.filter(slug=category_slug)


        
    if search:
        search = search.strip()
        
        queryset = queryset.filter(Q(slug__icontains=search)|
                                   Q(name__icontains=search)
                                  )

    
    return queryset