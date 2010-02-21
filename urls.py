from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',


    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    (r'^xmedia/(?P<path>.*)$', 'django.views.static.serve', {'document_root': r'c:\code\payments\xmedia'}),

	(r'^$', 'payments.bills.views.index'),
	
    (r'^amount_per_period/(?P<start_date>\d{1,2}-\d{1,2}-\d{4})-(?P<end_date>\d{1,2}-\d{1,2}-\d{4})/$', 'payments.bills.views.paymentsForPeriod'),
	(r'^(?:amount_per_period/\d{1,2}-\d{1,2}-\d{4}-\d{1,2}-\d{1,2}-\d{4}/)?submit/$', 'payments.bills.views.changeDate'),
)
	