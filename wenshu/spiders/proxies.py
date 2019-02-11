# -*- coding: utf-8 -*-
import scrapy
import re
import time
import sqlite3
import socket, struct

from wenshu.items import ProxyItem


class ProxiesSpider(scrapy.Spider):

	name = 'proxies'
	allowed_domains = ['www.kuaidaili.com', 'www.xicidaili.com']
	start_urls = []
	custom_settings = {
		'CONCURRENT_REQUESTS': 64,
		'DOWNLOAD_TIMEOUT': 10
	}
	VALIDATE_URL = 'https://wenshu.court.gov.cn'
	VALIDATE_TITLE = '首页 - 中国裁判文书网'
	VALIDATE_TIMMEOUT = 20
	validated_iplist = []

	def start_requests(self):

		proxies = self.proxy_pipline.all_proxies()

		for item in proxies:
			yield self.ValidateRequest(item[3], item[1], item[2], item[7])

		for page in range(1, 8):
			yield scrapy.Request(
				url = 'https://www.xicidaili.com/nn/{}'.format(page),
				headers = {'Referer': 'https://www.xicidaili.com'},
				callback = self.parse_xicidaili,
				dont_filter = True
				)
			yield scrapy.Request(
				url = 'https://www.kuaidaili.com/free/inha/{}/'.format(page),
				headers = {'Referer': 'https://www.kuaidaili.com'},
				callback = self.parse_kuaidaili,
				dont_filter = True
				)

			time.sleep(2)


	def ValidateRequest(self, protocol, ip, port, source = ''):
		proxy = '{}://{}:{}'.format(protocol, ip, port)
		return scrapy.Request(
			url = self.VALIDATE_URL,
			headers = {'Referer': self.VALIDATE_URL},
			callback = self.parse_validate,
			dont_filter = True,
			meta = {
				'dont_retry': True,
				'proxy': proxy,
				'dont_redirect': True,
				'ip': ip,
				'port': port,
				'protocol': protocol,
				'source': source
			},
			errback = self.parse_validate_error
			)

	def parse_xicidaili(self, response):
		rows = response.xpath('//table[@id="ip_list"]/tr')
		for row in rows[1:]:
			ip = row.xpath('td[2]/text()').extract_first()
			port = row.xpath('td[3]/text()').extract_first()
			protocol = row.xpath('td[6]/text()').extract_first().lower()
			if not self.validated(ip):
				yield self.ValidateRequest(protocol, ip, port, response.url)

	def parse_kuaidaili(self, response):
		rows = response.xpath('//div[@id="list"]/table/tbody/tr')
		for row in rows[1:]:
			ip = row.xpath('td[1]/text()').extract_first()
			port = row.xpath('td[2]/text()').extract_first()
			protocol = row.xpath('td[4]/text()').extract_first().lower()
			if not self.validated(ip):
				yield self.ValidateRequest(protocol, ip, port, response.url)

	def parse_validate(self, response):
		title = response.xpath('//title/text()').extract_first()
		if self.VALIDATE_TITLE in title:
			item = ProxyItem()
			item['valid'] = 1
			item['fails'] = 0
			item['ip'] = response.request.meta.get('ip', '')
			item['port'] = response.request.meta.get('port', 0)
			item['protocol'] = response.request.meta.get('protocol', '')
			item['source'] = response.request.meta.get('source', '')
			yield item
		else:
			self.proxy_pipline.fail(response.request.meta.get('ip', ''))

	def parse_validate_error(self, failure):
		ip = failure.request.meta.get('ip', '')
		self.proxy_pipline.fail(ip)

	@classmethod
	def validated(cls, ip):
		l = cls.ip2long(ip)
		finded = l in cls.validated_iplist
		cls.validated_iplist.append(l)
		if finded:
			print('here we find repeat ip:', ip)
		return finded

	@classmethod
	def ip2long(cls, ip):
		packedIP = socket.inet_aton(ip)
		return struct.unpack("!L", packedIP)[0]

