from django.contrib import admin
from .models import Product

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description') 
    search_fields = ('name', 'description')
    list_filter = ('price',)  
    ordering = ('price',)  

admin.site.register(Product, ProductAdmin)