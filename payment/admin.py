from django.contrib import admin
from .models import *
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'created_by', 'product_name', 'status', 'sold', 'created_at')
    list_filter = ('sold', 'status', 'created_at', 'decrypted')
    search_fields = ('created_by__username', 'order_id', 'product__name')
    
    list_editable = ('sold',)
    list_per_page = 50  # Pagination to limit records per page
    list_max_show_all = 200  # Maximum records to show when clicking "Show all"
    
    # Optimize queries by prefetching related objects
    list_select_related = ('created_by', 'product')
    
    # Add ordering to make queries more predictable
    ordering = ('-created_at',)
    
    # Custom method to display product name efficiently
    def product_name(self, obj):
        return obj.product.name if obj.product else 'N/A'
    product_name.short_description = 'Product'
    product_name.admin_order_field = 'product__name'
    
    # Add date hierarchy for better navigation
    date_hierarchy = 'created_at'
    
    # Optimize the form for editing
    raw_id_fields = ('created_by', 'product')  # Use popup selectors instead of dropdowns

admin.site.register(Invoice, InvoiceAdmin)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ( 'created_by', 'address', 'balance')
    
    search_fields = ('created_by__username',)
    
    list_editable = ('balance',)

admin.site.register(Balance, BalanceAdmin)

class Telegram_ClientAdmin(admin.ModelAdmin):
    list_display = ( 'order_id', 'address', 'balance', 'received', 'chat_id','created_at')
    
    search_fields = ('chat_id',)
    
    list_editable = ('balance',)

    fieldsets = (
        (None, {
            'fields': ( 'order_id', 'address', 'received', 'balance', 'chat_id',)
        }),
    )
#admin.site.register(Telegram_Client, Telegram_ClientAdmin)

class Telegram_Otp_botAdmin(admin.ModelAdmin):
    list_display = ( 'order_id', 'address', 'name', 'log', 'chat_id','created_at','number','trial_used',)
    
    search_fields = ('chat_id',)
    
    list_editable = ('number','trial_used',)

    fieldsets = (
        (None, {
            'fields': ( 'order_id', 'address', 'received', 'balance', 'chat_id','name','number','log','trial_used','otp_code')
        }),
    )
#admin.site.register(Telegram_Otp_bot, Telegram_Otp_botAdmin)
admin.site.register(Addr)