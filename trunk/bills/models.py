from django.db import models

class Tenant(models.Model):
    name = models.CharField(max_length = 30)
    lease_start = models.DateField()
    lease_end = models.DateField()
    
    def __unicode__(self):
        return self.name

class Payment(models.Model):
    name = models.CharField(max_length = 30)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    who_paid = models.ForeignKey(Tenant)

    def __unicode__(self):
        return self.name