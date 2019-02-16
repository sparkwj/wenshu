# -*- coding: utf-8 -*-
import os
import sys
import uuid
import re
import json
import time
import random
import calendar
import execjs
import scrapy
import logging
import requests

from scrapy import signals
from twisted.internet import reactor, defer, task
from twisted.names import client
from twisted.internet import task
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.web._newclient import ResponseNeverReceived
from twisted.internet.error import DNSLookupError, ConnectionLost, TimeoutError, TCPTimedOutError, ConnectionRefusedError
from scrapy.http import Response, TextResponse

from wenshu import jshelper
from wenshu.items import TaskItem, DocItem
from wenshu.exceptions import WafVerifyError, RemindKeyError, RemindError, Vl5xTimeoutError

from netifaces import AF_INET
import netifaces as ni

logger = logging.getLogger(__name__)

class ListSpider(scrapy.Spider):
	name = 'list'
	allowed_domains = ['court.gov.cn']
	custom_settings = {
		'CONCURRENT_REQUESTS': 1024,
		'RETRY_ENABLED': True,
		'MAX_RETRY_TIMES': 3,
		'DOWNLOAD_TIMEOUT': 30,
		'DOWNLOAD_DELAY': 0,
		'CONCURRENT_REQUESTS_PER_DOMAIN': 256,
		'CONCURRENT_REQUESTS_PER_IP': 256
	}
	start_urls = []

	handle_httpstatus_all = True

	HOME_URL = 'http://wenshu.court.gov.cn'
	START_URL = 'http://wenshu.court.gov.cn/List/List?sorttype=1&conditions=searchWord+2+AJLX++案件类型:民事案件'
	LIST_CONTENT_URL = 'http://wenshu.court.gov.cn/List/ListContent'
	CODE_URL = 'http://wenshu.court.gov.cn/ValiCode/GetCode'

	CAPTCHA_URL = 'http://wenshu.court.gov.cn/User/ValidateCode/'
	CAPTCHA_VALIDATE_URL = 'http://wenshu.court.gov.cn/Content/CheckVisitCode'

	CAPTCHA_SOLVE_URL = 'http://localhost:5000/solve'
	F80COOKIES_URL = 'http://localhost:3000/f80Cookies'

	CONCURRENT_SESSIONS_PER_IP = 64

	WAF_DELAY = 310

	CHANGE_IP_ENABLED = False

	STATS_INTERVAL = 60

	DEBUG_TASK_IDS = []

	last_task = {}

	# available_proxies = {}
	# used_proxies = {}
	wenshu_servers = ['61.160.224.60']

	stats = {
		'start': time.time(),
		'speed': 0,
		'total': 0,
		'_count_queue': [],
		'_last_scraped_count': {'time': time.time(), 'count': 0}
	}

	def start_requests(self):
		self._init_stats_task()

		self.wenshu_servers = self.crawler.settings.get('WENSHU_SERVERS', [])
		for request in self.CdnRequests():
			yield request

	def CdnRequests(self):
		requests = []
		for i in range(0, len(self.wenshu_servers) if self.wenshu_servers else 1):
			for count in range(0, self.CONCURRENT_SESSIONS_PER_IP):
				request = self.ListRequest()
				request.meta['delay_request'] = random.random() * self.CONCURRENT_SESSIONS_PER_IP
				if self.wenshu_servers:
					request.meta['ip_addr'] = self.wenshu_servers[i]
				requests.append(request)
		return requests

	def ListRequest(self):
		f80s = jshelper.f80sCookie()
		f80t = jshelper.f80tCookie()
		return scrapy.Request(url = self.START_URL, headers = {'Referer': 'http://wenshu.court.gov.cn'}, cookies = {'FSSBBIl1UgzbN7N80T': f80t, 'FSSBBIl1UgzbN7N80S': f80s}, callback = self.parse_list, errback = self.other_error, dont_filter = True,  meta = {'dont_delay': True})

	def NumberRequest(self):
		post_data = {'guid': self.create_guid()}
		return scrapy.FormRequest(url = self.CODE_URL, formdata = post_data, headers = {'Referer': 'http://wenshu.court.gov.cn'}, callback = self.parse_number, errback = self.other_error)

	def parse(self, response):
		raise Exception('Unkown request!')

	def ListContentRequest(self, response):
		session = response.request.meta.get('session', None)

		task = self.last_task = self.task_pipeline.next_list_task()

		if not task:
			logger.info('No more task')
			return

		page = task.get('page', 1)
		post_data = {
			'Param': self._task_to_post_param(task),
			'Index': str(page if page else 1),
			'Page': "10",
			'Order': '法院层级',
			'Direction': 'asc',
			'vl5x': session.get('vl5x', ''),
			'number': session.get('number', ''),
			'guid': self.create_guid()
		}

		f80s = jshelper.f80sCookie()
		f80t = jshelper.f80tCookie()

		request = scrapy.FormRequest(url = self.LIST_CONTENT_URL, formdata = post_data, headers = {'Referer': 'http://wenshu.court.gov.cn'}, cookies = {'FSSBBIl1UgzbN7N80T': f80t, 'FSSBBIl1UgzbN7N80S': f80s}, callback = self.list_request_loop, errback = self.other_error, meta = {'task': task})
		request.meta['param'] = post_data['Param']
		logger.debug('Processing task: Param:{};Index:{}'.format(post_data['Param'], post_data['Index']))

		if task.get('task_id') == -1:
			request.meta['delay_request'] = 10
			session['no_task_sleep_count'] = session.get('no_task_sleep_count', 0) + 1
			if session.get('no_task_sleep_count', 0) > 5:
				raise scrapy.exceptions.CloseSpider('Finished because no more tasks!')
			else:
				logger.info('Wait 10 secs for new task...')

		return request

	def list_request_loop(self, response):
		task = response.request.meta.get('task', None)

		try:
			docs = jshelper.decryptListContent(response.text)
			doc_count = docs[0] if len(docs) > 1 else 0

			if len(docs) > 1:
				self.doc_pipeline.save_docs(docs[1:])
			
			task['doc_count'] = doc_count
			task['fails'] = 0

			self.crawler.stats.inc_value('docid_scraped_count', count = len(docs) - 1, spider=self)
					
		except Exception as e:

			task['fails'] = task.get('fails', 0) + 1
			logger.error('Parse list response error\n%(error)s\nrepsone code:%(status)d\nrequest task:\n%(task)s\nresponse text:\n%(text)s', {'error': e, 'status': response.status, 'task': task, 'text': response.text}, exc_info = True, extra = {'response': response})

		finally:

			fails = task.get('fails', 0) > 0
			if fails:
				task['status'] = 0
			elif task.get('status', 0) == -1:
				task['status'] = 1

			self.task_pipeline.update(task)
			yield self.ListContentRequest(response)

	def parse_list(self, response):
		session = response.request.meta.get('session', None)
		cookies = session.get('cookies', None)

		set_cookies = response.headers.getlist('Set-Cookie')
		if set_cookies and len(set_cookies) > 0:
			for cookie in set_cookies:
				name_value = cookie.decode().split(';')[0].split('=')
				if name_value[0] == 'vjkl5':
					vjkl5 = name_value[1]
					vl5x = jshelper.getKey(vjkl5)
					session['vjkl5'] = vjkl5
					session['vl5x'] = vl5x
					session['vl5x_time'] = time.time()

		vl5x = session.get('vl5x', None)
		if vl5x:
			yield self.NumberRequest()
		else:
			yield self.ListRequest()

	def parse_number(self, response):
		if len(response.text) >= 4 and len(response.text) < 40:
			self.last_number_time = time.time()
			number = response.text
			session = response.request.meta.get('session', None)
			session['number'] = number
			session['number_time'] = time.time()
			logger.debug('Success get code: {}'.format(response.text))
			yield self.ListContentRequest(response)
		else:
			logger.debug('Failed get code, retrying...')
			yield self.NumberRequest()

	def other_error(self, failure):
		task = failure.request.meta.get('task', None)
		if task:
			if task.get('status', 0) == -1:
				task['status'] = 0
			self.task_pipeline.update(task)

		if not (failure.check(Vl5xTimeoutError) or task):
			logger.error('%s:%s', repr(failure), failure.request.url)

		#middleware will not handle errback output, so call middleware method here, ref:
		# FIXME: don't ignore errors in spider middleware, in scraper.py
		request = self.ListRequest()
		request = self.session_ware.process_output_request(request, failure, self)
		request.meta['delay_request'] = 0.5

		if failure.check(TimeoutError, ResponseNeverReceived, ConnectionRefusedError, WafVerifyError):
			logger.error('%s:%s', repr(failure), failure.request.url)
			# request.meta['delay_request'] = self.WAF_DELAY

		yield request
	

	def _init_stats_task(self):
		self.prev_docid_scraped_count = 0
		self.multiplier = 60.0 / self.STATS_INTERVAL
		self.stats_task = task.LoopingCall(self._log)
		self.stats_task.start(self.STATS_INTERVAL)

	def _log(self):
		docid_scraped_count = self.crawler.stats.get_value('docid_scraped_count', 0)
		docrate = (docid_scraped_count - self.prev_docid_scraped_count) * self.multiplier
		self.prev_docid_scraped_count = docid_scraped_count
		msg = 'Last task date: %(year)s-%(month)s-%(day)s, Crawled %(docs)d docs (at %(docrate)d docs/min)'
		log_args = {'year': self.last_task.get('year', 0), 'month': self.last_task.get('month', 0), 'day': self.last_task.get('day', 0), 'docs': docid_scraped_count, 'docrate': docrate}
		logger.info(msg, log_args)

	@classmethod
	def from_crawler(cls, crawler, *args, **kwargs):
		spider = super(ListSpider, cls).from_crawler(crawler, *args, **kwargs)
		crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
		return spider

	def spider_closed(self, spider):
		jshelper.free()

	def create_guid(self):
		c = lambda: format(int((1 + random.random()) * 65536), 'x')[1:]
		return c() + c() + '-' + c() + '-' + c() + c() + '-' + c() + c() + c()

	#Param: 法院层级:基层法院,案件类型:民事案件,审判程序:一审,文书类型:判决书,裁判日期:2018-12-11 TO 2018-12-11,法院地域:北京市
	def _task_to_post_param(self, task):
		self.TASK_PARAM_KEY_MAP = {
			'trial_date': '裁判日期',
			'court_area': '法院地域',
			'middle_court': '中级法院',
			'basic_court': '基层法院',
			'doc_type': '文书类型',
		}
		
		day = task.get('day', None)
		month = task.get('month', None)
		year = task.get('year', None)
		start_day = day
		end_day = day
		start_month = month
		end_month = month

		if day is None:
			start_day = 1
			if month is None:
				start_month = 1
				end_month = 12
				end_day = 31
			else:
				end_day = calendar.monthrange(year, end_month)[1]

		d = {}

		for key in self.TASK_PARAM_KEY_MAP.keys():
			value = task.get(key, None)
			if key == 'trial_date':
				d[self.TASK_PARAM_KEY_MAP[key]] = '{}-{}-{} TO {}-{}-{}'.format(year, '{:02d}'.format(start_month), '{:02d}'.format(start_day), year, '{:02d}'.format(end_month), '{:02d}'.format(end_day))
			elif key == 'court_area' and value == '最高人民法院':
				d['法院层级'] = '最高法院'
			elif value is None:
				continue
			else:
				if len(value) > 0:
					d[self.TASK_PARAM_KEY_MAP[key]] = value

		court_level = task.get('court_level', None)
		if not (court_level is None):
			d['法院层级'] = court_level

		param = []
		for key in d.keys():
			param.append('{}:{}'.format(key, d[key]))

		return ','.join(param)

	# def CaptChaRequest(self):
	# 	return scrapy.Request(url = self.CAPTCHA_URL + str(random.randint(1, 9999)), headers = {'Referer': 'http://wenshu.court.gov.cn'}, callback = self.parse_captcha, errback = self.other_error, meta = {'dont_delay': True})

	# def CaptChaValidateRequest(self, captcha_code):
	# 	return scrapy.FormRequest(url = self.CAPTCHA_VALIDATE_URL, formdata = {'ValidateCode': captcha_code}, headers = {'Referer': 'http://wenshu.court.gov.cn'}, callback = self.parse_captcha_validate, errback = self.other_error, meta = {'dont_delay': True})

	# def CaptChaSovleRequest(self, prepped):
	# 	return scrapy.Request(url = self.CAPTCHA_SOLVE_URL, method = 'POST', headers = prepped.headers, body = prepped.body, callback = self.parse_captcha_solve, errback = self.other_error, meta = {'dont_delay': True})


	# def parse_captcha(self, response):
	# 	if isinstance(response, Response) and response.status == 200:
	# 		files = {'captcha_image': response.body}
	# 		prepped = requests.Request('POST', self.CAPTCHA_SOLVE_URL, files=files).prepare()
	# 		yield self.CaptChaSovleRequest(prepped)
	# 	else:
	# 		logger.info('Failed to get captcha, retrying...')
	# 		yield self.CaptChaRequest()

	# def parse_captcha_solve(self, response):
	# 	if len(response.text) > 0:
	# 		yield self.CaptChaValidateRequest(response.text)
	# 	else:
	# 		logger.error('Not recognize the captcha')
	# 		yield self.CaptChaRequest()

	# def parse_captcha_validate(self, response):
	# 	if response.text == '1':
	# 		logger.info('Success solve captcha!')
	# 		session = response.request.meta.get('session', None)
	# 		yield self.ListRequest()
	# 	else:
	# 		logger.info('Retry solve captcha...')
	# 		yield self.CaptChaRequest()

	# def F80ForListRequest(self):
	# 	return scrapy.Request(url = self.F80COOKIES_URL, callback = self.parse_f80_for_list, errback = self.other_error, meta = {'dont_delay': True})

	# def F80ForListContentRequest(self):
	# 	return scrapy.Request(url = self.F80COOKIES_URL, callback = self.parse_f80_for_list_content, errback = self.other_error, meta = {'dont_delay': True})


	# def parse_f80_for_list(self, response):
	# 	session = response.request.meta.get('session', None)
	# 	f80cookies = json.loads(response.text)
	# 	session['f80s'] = f80cookies['f80s']
	# 	session['f80t'] = f80cookies['f80t']
	# 	yield self.ListRequest(response)

	# def parse_f80_for_list_content(self, response):
	# 	session = response.request.meta.get('session', None)
	# 	f80cookies = json.loads(response.text)
	# 	session['f80s'] = f80cookies['f80s']
	# 	session['f80t'] = f80cookies['f80t']
	# 	yield self.ListContentRequest(response)


	# def HomeRequest(self):
	# 	return scrapy.Request(url = self.HOME_URL, callback = self.parse_home, errback = self.other_error, dont_filter = True,  meta = {'dont_delay': True})

	# def parse_home(self, response):
	# 	session = response.request.meta.get('session', None)
	# 	meta = response.css('#9DhefwqGPrzGxEp9hPaoag::attr(content)').extract_first()
	# 	session['meta'] = meta

	# 	ywtu = jshelper.getYWTU(meta)
	# 	session['ywtu'] = ywtu

	# 	set_cookies = response.headers.getlist('Set-Cookie')
	# 	if set_cookies and len(set_cookies) > 0:
	# 		for cookie in set_cookies:
	# 			name_value = cookie.decode().split(';')[0].split('=')
	# 			if name_value[0] in ['FSSBBIl1UgzbN7N80S', 'FSSBBIl1UgzbN7N80T']:
	# 				session[name_value[0]] = name_value[1]

	# 		yield self.ListRequest(response)

	# def parse_server_list(self, response):
	# 	if isinstance(response, Response) and response.status == 200:
	# 		print(response.text)
	# 		result = json.loads(response.text)
	# 		if result and result.get('status', False):
	# 			servers = result.get('data', {})
	# 			self.wenshu_servers = [s.get('ip') for s in servers]
	# 			logger.debug('Success to get server list: {}'.format(self.wenshu_servers))
	# 			return self.ListRequests(response)
	# 	else:
	# 		logger.error('%s:%s', repr(response), response.request.url)

	# 	raise scrapy.exceptions.CloseSpider('Error: can not get wenshu server ips')


	# def change_ip_address(self):
	# 	logger.info('Now will renew pppoe ip addr, please wait...')

	# 	while True:
	# 		last_ip_addr = ni.ifaddresses('ppp0')[AF_INET][0]['addr']
	# 		os.system('osascript ' + self.settings.get('PROJECT_ROOT') + '/scripts/renewip.scpt')
	# 		time.sleep(0.5)
	# 		new_ip_addr = ni.ifaddresses('ppp0')[AF_INET][0]['addr']
	# 		if new_ip_addr != last_ip_addr:
	# 			break
	# 	logger.info('Successed change ip!')


	# def load_available_proxies(self):
	# 	proxies = self.proxy_pipline.available_proxies()
	# 	for proxy in proxies:
	# 		if (not proxy['ip'] in self.available_proxies.keys()) and (not proxy['ip'] in self.used_proxies.keys()):
	# 			self.available_proxies[proxy['ip']] = proxy

	# def next_available_proxy(self):
	# 	for ip in self.available_proxies.keys():
	# 		if not ip in self.used_proxies.keys():
	# 			proxy = self.available_proxies.pop(ip)
	# 			self.used_proxies[proxy['ip']] = proxy
	# 			return proxy