from django.db import models
from django.utils.text import slugify


# Create your models here.

class CategoryModel(models.Model):
    name   = models.CharField(max_length=100, unique=True, null=False, blank=False)
    parent = models.ForeignKey('self', related_name='children', on_delete=models.CASCADE, null=True, blank=True)
    slug   = models.SlugField(max_length=120, unique=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.is_active}" 
    

    def save(self,*args,**kwargs):
        if not self.slug or self.pk:
            self.slug = slugify(self.name)
        
        return super().save(*args,**kwargs)
    

    

class BrandModel(models.Model):
    name = models.CharField(max_length=100, unique=True, null=False, blank=False)
    slug = models.SlugField(max_length=120, unique=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.is_active}"
    
    def save(self,*args,**kwargs):
        if not self.slug or self.pk:
            self.slug = slugify(self.name)
        
        return super().save(*args,**kwargs)
    




class ProductModel(models.Model):
    name     = models.CharField(max_length=200, null=False, blank=False)
    category = models.ForeignKey(CategoryModel, related_name='products', on_delete=models.PROTECT, null=False, blank=False)
    brand    = models.ForeignKey(BrandModel, related_name='products', on_delete=models.PROTECT, null=False, blank=False)  
    slug     = models.SlugField(max_length=120, unique=True)

    description = models.TextField(null=True, blank=True)
    price       = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    stock       = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.category.name} - {self.brand.name}"
    

    class Meta:
        constraints = [models.UniqueConstraint(fields = ["name","brand"],
                                               name="unique_product_name_per_brand"
                                              )
                      ]
    

    def save(self,*args,**kwargs):
        if not self.slug or self.pk:
            self.slug = slugify(self.name)
        
        return super().save(*args,**kwargs)