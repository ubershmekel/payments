from Bills.bills.models import Tenant, Payment
from django.contrib import admin

admin.site.register(Tenant)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'start_date', 'end_date', 'who_paid')

admin.site.register(Payment, PaymentAdmin)