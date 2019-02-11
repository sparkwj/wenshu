# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time
from scrapy import signals
from datetime import datetime, timedelta
from twisted.web._newclient import ResponseNeverReceived
from twisted.internet.error import DNSLookupError, ConnectionLost, TimeoutError, TCPTimedOutError, ConnectionRefusedError
from wenshu.exceptions import WafVerifyError, RemindKeyError, RemindError, Vl5xTimeoutError

logger = logging.getLogger(__name__)

class IPtestSpider(scrapy.Spider):
	name = 'iptest'
	allowed_domains = ['wenshu.court.gov.cn']
	start_urls = []
	custom_settings = {
		'CONCURRENT_REQUESTS': 96,
		'RETRY_ENABLED': True,
		'MAX_RETRY_TIMES': 2,
		'DOWNLOAD_TIMEOUT': 3,
		'DOWNLOAD_DELAY': 0,
		'CONCURRENT_REQUESTS_PER_IP': 64
	}

	WAF_LOCATION_PATTERN = 'waf_verify.htm'
	VALIDATE_URL = 'http://{}'
	ips = ['122.70.138.135', '61.240.144.221', '112.25.60.131', '112.25.60.187', '120.52.19.18', '112.25.60.217', '112.25.60.156', '122.70.138.177', '61.240.144.212', '61.240.144.156', '61.240.144.209', '61.240.144.200', '61.160.224.52', '112.25.60.202', '120.52.19.16', '120.52.19.10', '222.73.144.191', '112.25.60.186', '112.25.60.183', '112.25.60.220', '222.73.144.189', '122.70.138.194', '122.70.138.166', '122.70.138.151', '112.25.60.238', '122.70.138.233', '112.25.60.158', '112.25.60.236', '61.240.144.185', '61.240.144.159', '61.240.144.196', '112.25.60.141', '112.25.60.133', '120.52.19.14', '122.70.138.138', '122.70.138.168', '112.25.60.219', '122.70.138.216', '122.70.138.154', '61.160.224.36', '112.25.60.132', '120.52.19.41', '61.160.224.58', '112.25.60.138', '112.25.60.213', '222.73.144.156', '222.73.144.155', '61.240.144.198', '61.240.144.202', '61.160.224.32', '112.25.60.170', '120.52.19.79', '120.52.19.81', '36.27.212.123', '36.27.212.72', '122.70.138.152', '122.70.138.213', '61.240.144.192', '61.240.144.178', '122.70.138.132', '122.70.138.136', '222.73.144.205', '61.160.224.74', '222.73.144.172', '222.73.144.165', '112.25.60.173', '222.73.144.169', '112.25.60.162', '120.52.19.118', '120.52.19.45', '120.52.19.19', '36.27.212.106', '222.73.144.168', '61.160.224.37', '120.52.19.101', '222.73.144.161', '120.52.19.116', '120.52.19.7', '120.52.19.9', '120.52.19.12', '120.52.19.4', '120.52.19.40', '61.160.224.64', '120.52.19.8', '120.52.19.3', '36.27.212.88', '120.52.19.64', '61.160.224.66', '61.160.224.54', '61.160.224.78', '112.25.60.205', '61.160.224.69', '120.52.19.106', '120.52.19.88', '61.160.224.67', '120.52.19.99', '120.52.19.120', '61.160.224.34', '120.52.19.26', '222.73.144.204', '112.25.60.198', '36.27.212.82', '122.70.138.134', '120.52.19.78', '120.52.19.66', '120.52.19.94', '36.27.212.89', '36.27.212.112', '222.73.144.222', '112.25.60.222', '36.27.212.76', '122.70.138.161', '122.70.138.219', '61.240.144.164', '112.25.60.146', '122.70.138.184', '112.25.60.177', '61.240.144.175', '122.70.138.186', '61.240.144.167', '61.240.144.168', '120.52.19.6', '61.240.144.160', '112.25.60.160', '61.240.144.179', '112.25.60.152', '112.25.60.134', '120.52.19.76', '112.25.60.164', '36.27.212.110', '120.52.19.93', '61.240.144.219', '120.52.19.95', '120.52.19.103', '61.160.224.40', '61.160.224.61', '61.240.144.220', '120.52.19.82', '122.70.138.250', '122.70.138.190', '61.240.144.152', '112.25.60.197', '61.240.144.157', '120.52.19.121', '61.240.144.173', '222.73.144.194', '112.25.60.174', '112.25.60.161', '112.25.60.166', '112.25.60.169', '112.25.60.172', '36.27.212.105', '61.240.144.222', '120.52.19.29', '120.52.19.122', '36.27.212.79', '120.52.19.90', '120.52.19.65', '120.52.19.47', '122.70.138.173', '112.25.60.189', '61.160.224.48', '120.52.19.11', '222.73.144.162', '122.70.138.189', '122.70.138.182', '120.52.19.31', '120.52.19.100', '36.27.212.109', '120.52.19.68', '222.73.144.167', '120.52.19.92', '61.240.144.233', '61.240.144.217', '222.73.144.210', '61.160.224.84', '61.160.224.73', '120.52.19.42', '120.52.19.24', '112.25.60.229', '61.240.144.230', '36.27.212.93', '122.70.138.175', '61.160.224.75'] + ['182.140.227.166', '61.160.224.60', '61.240.144.201', '221.204.14.198', '112.25.60.196', '119.84.14.194', '222.73.144.179', '122.70.138.199', '120.52.19.18', '58.20.19.13', '36.27.212.88', '123.129.232.222']
	result_ips = []
	last_start_time = time.time()
	ip = ''

	def start_requests(self):
		self.ip = self.ips.pop()
		for i in range(0, 64):
			yield self.ValidateRequest(self.ip)

	def ValidateRequest(self, ip):
		return scrapy.Request(url = self.VALIDATE_URL.format(self.ip), headers = {'Host': 'wenshu.court.gov.cn', 'Referer': 'http://wenshu.court.gov.cn'}, callback = self.validate_result, errback = self.validate_error, dont_filter = True, meta = {'ip': self.ip, 'dont_retry': True, 'dont_session': True})

	def validate_result(self, response):
		ipchanged = response.request.meta.get('ip', '') != self.ip
		if ipchanged:
			return

		ipchanged = False
		if self.WAF_LOCATION_PATTERN in response.url:
			print('================', '360waf, gave up ip:' + self.ip)
			if len(self.ips) == 0: return
			self.ip = self.ips.pop()
			ipchanged = True
		elif time.time() - self.last_start_time > 400:
			print('================', 'seems ok, ip:' + self.ip)
			self.result_ips.append(self.ip)
			if len(self.ips) == 0: return
			self.ip = self.ips.pop()
			ipchanged = True
		if ipchanged:
			self.last_start_time = time.time()
			for i in range(0, 64):
				yield self.ValidateRequest(self.ip)
		else:
			yield self.ValidateRequest(self.ip)

	def validate_error(self, failure):
		ipchanged = failure.request.meta.get('ip', '') != self.ip
		if ipchanged:
			return

		ipchanged = False
		if failure.check(TimeoutError, ResponseNeverReceived, ConnectionRefusedError):
			logger.error('%s:%s', repr(failure), failure.request.url)
			print('================', 'gave up ip:' + self.ip)
			if len(self.ips) == 0: return
			self.ip = self.ips.pop()
			ipchanged = True

		if ipchanged:
			self.last_start_time = time.time()
			for i in range(0, 64):
				yield self.ValidateRequest(self.ip)
		else:
			yield self.ValidateRequest(self.ip)

	@classmethod
	def from_crawler(cls, crawler, *args, **kwargs):
		spider = super(IPtestSpider, cls).from_crawler(crawler, *args, **kwargs)
		crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
		return spider

	def spider_closed(self, spider):
		print('============', self.result_ips)
