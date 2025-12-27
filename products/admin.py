from django.contrib import admin
from products import models
# Register your models here.




admin.site.register(models.CategoryModel)
admin.site.register(models.BrandModel)
admin.site.register(models.ProductModel)

