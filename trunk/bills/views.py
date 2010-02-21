# -*- coding: utf-8 -*-

from datetime import time, datetime, timedelta, date
from models import Payment, Tenant
from django.shortcuts import render_to_response
from django import forms
from django.contrib.admin import widgets
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from settings import DEBUG
from pprint import pprint, pformat

class TimeSpan:
	def __init__(self, start_date, end_date):
		self.start_date = start_date
		self.end_date = end_date
		self.people = 0
		self.cost = 0

	def days(self):
		return (self.end_date - self.start_date).days + 1

	def __contains__(self, other):
		if isinstance(other, TimeSpan):
			return self.start_date <= other.start_date and other.end_date <= self.end_date
		if isinstance(other, date):
			return self.start_date <= other <= self.end_date
		raise TypeError("Timespan can contain TimeSpan or date objects only")

	def __repr__(self):
		return '<TimeSpan (%s-%s): %.2f for %d' % (self.start_date, self.end_date, self.cost, self.people)

class Timeline:
	"Creates a timeline with days as the base unit"
	def __init__(self, timespan=None):
		self.timespans = []
		
		if not isinstance(timespan, TimeSpan):
			raise TypeError("Timelines are only for TimeSpan instances.")
		
		if timespan is not None:
			self.timespans.append(timespan)
	
	def get_start_date(self):
		return self.timespans[0].start_date

	def get_end_date(self):
		return self.timespans[-1].end_date		
	
	def __iter__(self):
		return iter(self.timespans)
	
	def add(self, timespan):
		self._slice_start(timespan.start_date)
		self._slice_end(timespan.end_date)

	def _slice_start(self, split_date):
		if split_date < self.get_start_date():
			self.timespans.insert(0, TimeSpan(split_date, self.get_start_date() - timedelta(1)))
			return
		for i, ts in enumerate(self.timespans):
			if split_date in ts:
				if split_date == ts.start_date:
					return
				self.timespans.pop(i)
				self.timespans.insert(i, TimeSpan(split_date, ts.end_date))
				self.timespans.insert(i, TimeSpan(ts.start_date, split_date - timedelta(1)))
				return

	def _slice_end(self, split_date):
		if split_date > self.get_end_date():
			self.timespans.append(TimeSpan(self.get_end_date() + timedelta(1), split_date))
			return
		for i, ts in enumerate(self.timespans):
			if split_date in ts:
				if split_date == ts.end_date:
					return
				self.timespans.pop(i)
				self.timespans.insert(i, TimeSpan(split_date + timedelta(1), ts.end_date))
				self.timespans.insert(i, TimeSpan(ts.start_date, split_date))
				return

	def __repr__(self):
		return pformat(self.timespans)

class PaymentSummary:
	def __init__(self, start_date, end_date):
		self.start_date = start_date
		self.end_date = end_date
		raw_payments = Payment.objects.exclude(start_date__gt = end_date).exclude(end_date__lt = start_date)
		self.tenants = set(Tenant.objects.exclude(lease_start__gt = end_date).exclude(lease_end__lt = start_date)).union([p.who_paid for p in raw_payments])
		self.tenants = list(self.tenants)
		for tenant in self.tenants:
			tenant.costs = 0
			tenant.payed = 0
		self.payments = self._enrich_payments(raw_payments)
		self.timeline = self.createTimeline()
		if DEBUG:
			pprint(self.timeline)
		self._calculate_costs_for_tenants()
		self._calculate_debts()

	def createTimeline(self):
		timeline = Timeline(TimeSpan(self.start_date, self.end_date))
		
		for p in self.payments:
			paymentTimeSpan = TimeSpan(p.start_date, p.end_date)
			timeline.add(paymentTimeSpan)
		for t in self.tenants:
			tenantTimeSpan = TimeSpan(t.lease_start, t.lease_end)
			timeline.add(tenantTimeSpan)
		
		for p in self.payments:
			paymentTimeSpan = TimeSpan(p.start_date, p.end_date)
			for ts in timeline:
				if ts in paymentTimeSpan:
					ts.cost += p.price / paymentTimeSpan.days() * ts.days()
		
		for t in self.tenants:
			tenantTimeSpan = TimeSpan(t.lease_start, t.lease_end)
			for ts in timeline:
				if ts in tenantTimeSpan:
					ts.people += 1
		
		return timeline
	
	def total_costs(self):
		"Start date and end date must already be part of the timeline"
		totalTS = TimeSpan(self.start_date, self.end_date)
		return sum([ts.cost for ts in self.timeline if ts in totalTS])
		
	def _calculate_costs_for_tenants(self):
		for tenant in self.tenants:
			relevantTimeSpan = TimeSpan(max(tenant.lease_start, self.start_date), min(tenant.lease_end, self.end_date))
			costForTenant = 0
			for ts in self.timeline:
				if ts in relevantTimeSpan:
					costForTenant += ts.cost / ts.people
			tenant.costs = costForTenant
			
	def _calculate_debts(self):
		for tenant in self.tenants:
			tenant.debts = tenant.costs - tenant.payed + tenant.cash_balance
			

	def _enrich_payments(self, payments):
		for payment in payments:
			amountPerDay = payment.price / ((payment.end_date - payment.start_date).days + 1) # dates are inclusive
			payment.relevant_start_date = max(self.start_date, payment.start_date)
			payment.relevant_end_date = min(self.end_date, payment.end_date)
			days_relevant = (payment.relevant_end_date - payment.relevant_start_date).days + 1
			payment.cost = days_relevant * amountPerDay
			tenant = self.tenants[self.tenants.index(payment.who_paid)]
			tenant.payed += payment.cost
		return payments

		
class DateForm(forms.Form):
	start_date = forms.DateField(label = u'תאריך התחלה', widget = widgets.AdminDateWidget, input_formats=['%d-%m-%Y',])
	end_date = forms.DateField(label = u'תאריך סוף', widget = widgets.AdminDateWidget, input_formats=['%d-%m-%Y',])

def changeDate(request):
	form = DateForm(request.POST)
	if form.is_valid():
		return HttpResponseRedirect(reverse(paymentsForPeriod,
			args=[form.cleaned_data[u'start_date'].strftime('%d-%m-%Y'), form.cleaned_data[u'end_date'].strftime('%d-%m-%Y')]))
	return HttpResponseRedirect('..')

def index(self):
	return render_to_response('index.html', {'dateForm': DateForm()})
	
def paymentsForPeriod(request, start_date, end_date):
	dateForm = DateForm(initial = {'start_date': start_date, 'end_date': end_date})
	start_date = datetime.strptime(start_date, '%d-%m-%Y').date()
	end_date = datetime.strptime(end_date, '%d-%m-%Y').date()
	summary = PaymentSummary(start_date, end_date)

	total = summary.total_costs()
	

	return render_to_response('payments_per_period.html', {'dateForm': dateForm,
														'payments': summary.payments,
														'total': total,
														'tenants': summary.tenants,
														'start_date': start_date,
														'end_date': end_date,
														 })

def runTests():
	'''
	Test Timeline outputs:
		[<TimeSpan (2009-01-01-2039-04-23): 0.00 for 0]
		[<TimeSpan (2009-01-01-2019-02-16): 0.00 for 0,
		 <TimeSpan (2019-02-17-2029-03-19): 0.00 for 0,
		 <TimeSpan (2029-03-20-2039-04-23): 0.00 for 0]
		[<TimeSpan (2009-01-01-2019-02-16): 0.00 for 0,
		 <TimeSpan (2019-02-17-2019-02-17): 0.00 for 0,
		 <TimeSpan (2019-02-18-2029-03-19): 0.00 for 0,
		 <TimeSpan (2029-03-20-2039-04-23): 0.00 for 0]
		[<TimeSpan (2009-01-01-2019-02-16): 0.00 for 0,
		 <TimeSpan (2019-02-17-2019-02-17): 0.00 for 0,
		 <TimeSpan (2019-02-18-2029-03-18): 0.00 for 0,
		 <TimeSpan (2029-03-19-2029-03-19): 0.00 for 0,
		 <TimeSpan (2029-03-20-2039-04-23): 0.00 for 0,
		 <TimeSpan (2039-04-24-2039-04-25): 0.00 for 0]	
	'''
	a = date(2009, 1, 1)
	b = date(2019, 2, 17)
	c = date(2029, 3, 19)
	d = date(2039, 4, 23)
	e = date(2039, 4, 25)
	
	timeline = Timeline(TimeSpan(a, d))
	print timeline
	timeline.add(TimeSpan(b, c))
	print timeline
	timeline.add(TimeSpan(a, b))
	print timeline
	timeline.add(TimeSpan(c, e))
	print timeline

if __name__ == "__main__":
	runTests()
