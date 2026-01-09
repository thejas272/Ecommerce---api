from django.db import models
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey
from django.db.models.functions import Lower
# Create your models here.

class CategoryModel(MPTTModel):
    name   = models.CharField(max_length=100, null=False, blank=False)
    parent = TreeForeignKey('self', related_name='children', on_delete=models.CASCADE, null=True, blank=True)
    slug   = models.SlugField(max_length=120)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta:
        constraints = [models.UniqueConstraint(Lower("name"),
                                               name="unique_category_name"
                                              ),
                       models.UniqueConstraint(Lower("slug"),
                                                name="unique_slug_per_category"
                                              )
                      ]

    def __str__(self):
        return f"{self.name}" 
    

    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        return super().save(*args,**kwargs)
    

    

class BrandModel(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    slug = models.SlugField(max_length=120)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        constraints = [models.UniqueConstraint(Lower("name"),
                                              name="unique_brand_name"
                                              ),
                       models.UniqueConstraint(Lower("slug"),
                                               name="unique_slug_per_brand"
                                              )
                      ]

    def __str__(self):
        return f"{self.name}"
    
    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        return super().save(*args,**kwargs)
    




class ProductModel(models.Model):
    name     = models.CharField(max_length=200, null=False, blank=False)
    category = models.ForeignKey(CategoryModel, related_name='products', on_delete=models.PROTECT, null=False, blank=False)
    brand    = models.ForeignKey(BrandModel, related_name='products', on_delete=models.PROTECT, null=False, blank=False)  
    slug     = models.SlugField(max_length=120)

    description = models.TextField(null=True, blank=True)
    price       = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    stock       = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"
    

    class Meta:
        constraints = [models.UniqueConstraint(Lower("name"),"brand",
                                               name="unique_product_name_per_brand"
                                              ),
                       models.UniqueConstraint(Lower("slug"),
                                                name="unique_slug_per_product"
                                              )
                      ]
    

    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        return super().save(*args,**kwargs)