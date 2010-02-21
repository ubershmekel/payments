from payments.bills.models import Tenant, Payment, Settle
from django.contrib import admin

admin.site.register(Tenant)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'start_date', 'end_date', 'who_paid', 'entry_date')

admin.site.register(Payment, PaymentAdmin)

class SettleAdmin(admin.ModelAdmin):
    list_display = ('payer', 'recipient', 'amount', 'entry_date')

admin.site.register(Settle, SettleAdmin)