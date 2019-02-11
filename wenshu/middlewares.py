# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

import scrapy
from scrapy import signals
from scrapy.http import Request, Response, TextResponse
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
import random
import logging
import uuid
import time

from wenshu.exceptions import WafVerifyError, RemindKeyError, RemindError, Vl5xTimeoutError

from twisted.internet import reactor
from twisted.internet.defer import Deferred
 

logger = logging.getLogger(__name__)
WENSHU_HOST = 'wenshu.court.gov.cn'

class WenshuSessionMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    SESSION_SPIDERS = ['list', 'docs', 'courts']

    WAF_LOCATION_PATTERN = 'waf_verify.htm'
    SESSION_REMIND_PATTERN = '"remind"'
    SESSION_REMIND_KEY_PATTERN = '"remind key"'

    VL5X_TIMEOUT = 200

    WAF_VERIFY = ''
    WAF_COOKIE = ''

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()

        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        s.crawler = crawler

        waf_verify = crawler.settings.get('WAF_VERIFY', None)
        if waf_verify:
            s.WAF_VERIFY = waf_verify

        waf_cookie = crawler.settings.get('WAF_COOKIE', None)
        if waf_cookie:
            s.WAF_COOKIE = s.WAF_COOKIE

        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        if not spider.name in self.SESSION_SPIDERS:
            return None

        if not (isinstance(response, TextResponse)):
            return None

        if response.request.meta.get('dont_session', False):
            return None

        session = response.request.meta.get('session', None)

        #error check
        if self.WAF_LOCATION_PATTERN in response.url:
            raise WafVerifyError('waf verify error')

        elif response.text == self.SESSION_REMIND_KEY_PATTERN:
            raise RemindKeyError('Remind key error')

        elif response.text == self.SESSION_REMIND_PATTERN:
            raise RemindError('Remind error')

        elif time.time() - session.get('vl5x_time', time.time()) > self.VL5X_TIMEOUT:
            session['vl5x_time'] = time.time()
            logger.debug('vl5x timeout')
            raise Vl5xTimeoutError('Vl5x timeout')

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for x in result:

            if spider.name in self.SESSION_SPIDERS and isinstance(x, Request):
                yield self.process_output_request(x, response, spider)
            else:
                yield x

    def process_output_request(self, request, response, spider):
        if request.meta.get('dont_session', False):
            return request

        session = response.request.meta.get('session', None) if response else None
        if not session:
            session = self._empty_session()

        request.dont_filter = True
        request.headers['Connection'] = 'keep-alive'

        #use virtual host ip
        ip_addr = None if not response else response.request.meta.get('ip_addr', None)
        if ip_addr:
            request.meta['ip_addr'] = ip_addr
        ip_addr = request.meta.get('ip_addr', None)
        if ip_addr and WENSHU_HOST in request.url:
            request = request.replace(url = request.url.replace(WENSHU_HOST, ip_addr))
            request.headers['Host'] = WENSHU_HOST

        if self.WAF_VERIFY:
            request.cookies['waf_verify'] = self.WAF_VERIFY
        if self.WAF_COOKIE:
            request.cookies['waf_cookie'] = self.WAF_VERIFY

        request.meta['cookiejar'] = session.get('id', None)

        #pass session between requests
        request.meta['session'] = session

        return request

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).

        for request in start_requests:
            
            if spider.name in self.SESSION_SPIDERS:
                yield self.process_output_request(request, None, spider)
            else:
                yield request

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.      
        logger.error('Error in process spider exception:\nresponse:\n{}\nexception:\n{}'.format(response, exception))  
        pass

    def spider_opened(self, spider):
        if spider.name in self.SESSION_SPIDERS:
            spider.session_ware = self

    def _empty_session(self):
        return {
            'id': str(uuid.uuid4()),
            'vjkl5': '',
            'vl5x': '',
            'waf_status': 0,
            'remind_status': 0,
            'remind_key_status': 0,
            'proxy': ''
        }


# write proxy downloadmiddleware
        # autoproxy = self.settings.get('autoproxy')
        # if autoproxy:
        #     if autoproxy.lower() in ('true', 'enable', 'eanbled', '1'):
        #         self.autoproxy = True
        #         self.load_available_proxies()
        #         logger.info('Auto proxy is eanbled')

        # if self.autoproxy:

        #     for i in range(0, min(self.CONCURRENT_SESSIONS, len(self.available_proxies))):

        #         proxy = self.next_available_proxy()

        #         http_proxy = '{}://{}:{}'.format(proxy.get('protocol'), proxy.get('ip'), proxy.get('port'))
        #         request = self.StartRequest()
        #         request.meta['_proxy'] = http_proxy
        #         request.meta['proxy'] = http_proxy

        #         yield request



class WenshuDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    # requests_count = 0

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        #X-Forwarded-For
        if not request.meta.get('dont_forward', False):
            x_forwarded_for = ".".join(map(str, (random.randint(1, 254) for _ in range(4))))
            request.headers['X-Forwarded-For'] = x_forwarded_for
            request.headers['X-Originating-IP'] = x_forwarded_for
            request.headers['X-Remote-IP'] = x_forwarded_for
            request.headers['X-Remote-Addr'] = x_forwarded_for
            request.headers['X-Client-IP'] = x_forwarded_for
            request.headers['Proxy-Client-IP'] = x_forwarded_for
            request.headers['Client-IP'] = x_forwarded_for
        # self.requests_count += 1
        # print('requests_count:', self.requests_count)
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        pass

class DelayedRequestsMiddleware(object):
    def process_request(self, request, spider):
        delay = request.meta.get('delay_request', None)
        if delay:
            d = Deferred()
            reactor.callLater(delay, d.callback, None)
            return d
 
class WenshuUserAgentMiddleware(UserAgentMiddleware):
 
    def __init__(self, user_agent):
        self.user_agent = user_agent
 
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            user_agent=crawler.settings.get('USER_AGENTS_LIST')
        )
 
    def process_request(self, request, spider):
        agent = random.choice(self.user_agent)
        request.headers['User-Agent'] = agent

