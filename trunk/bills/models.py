from django.db import models
from django.db.models import Sum
from datetime import datetime

class Tenant(models.Model):
    name = models.CharField(max_length = 30)
    lease_start = models.DateField()
    lease_end = models.DateField()
    
    @property
    def cash_balance(self):
        cash_out_dict = Settle.objects.filter(payer = self).aggregate(Sum('amount'))
        cash_in_dict = Settle.objects.filter(recipient = self).aggregate(Sum('amount'))
        
        cash_out = cash_out_dict['amount__sum'] or 0
        cash_in = cash_in_dict['amount__sum'] or 0
        
        return cash_in - cash_out
    
    def __unicode__(self):
        return self.name

class Payment(models.Model):
    name = models.CharField(max_length = 30)
    price = models.DecimalField(max_digits = 8, decimal_places = 2)
    start_date = models.DateField()
    end_date = models.DateField()
    who_paid = models.ForeignKey(Tenant)
    entry_date = models.DateTimeField(auto_now_add = True, default = datetime.now())
    
    def __unicode__(self):
        return self.name


class Settle(models.Model):
    payer = models.ForeignKey(Tenant, related_name='settles_payed')
    recipient = models.ForeignKey(Tenant, related_name='settles_received')
    amount = models.DecimalField(max_digits = 8, decimal_places = 2)
    entry_date = models.DateTimeField(auto_now_add = True)

