# -*- coding: utf-8 -*-
import scrapy
import logging
import json
from scrapy import signals
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CdnsSpider(scrapy.Spider):
    name = 'cdns'
    allowed_domains = ['site.ip138.com', 'wenshu.court.gov.cn']
    start_urls = []
    custom_settings = {
        'CONCURRENT_REQUESTS': 96,
        'RETRY_ENABLED': True,
        'MAX_RETRY_TIMES': 2,
        'DOWNLOAD_TIMEOUT': 3,
        'DOWNLOAD_DELAY': 0,
        'CONCURRENT_REQUESTS_PER_IP': 16
    }

    _scraped_cdns = []
    VALIDATE_TITLE = '中国裁判文书网'
    VALIDATE_URL = 'http://{}'

    _fails_count = 0

    _start_domains = ['wenshu.court.gov.cn', 'www.360.net', 'anyu.360.net', 'butian.360.cn', 'm.bobao.360.cn', 'b.360.cn', 'webscan.360.cn', 'zhongce.360.cn', 'wangzhan.360.cn', 'www.ahcz.gov.cn', 'www.sxzwfw.gov.cn', 'www.gz.gdciq.gov.cn', 'nngaj.gov.cn', 'www.ningjiang.gov.cn', 'loudong.360.cn']
    _scraped_domains = []
    _scraped_ips = []
    _scraped_cdn_prefixs = []


    def start_requests(self):
        self.crawler.signals.connect(self.spider_closed, signal=signals.spider_closed)
        # yield self.ValidateRequest('61.240.144.174')
        for domain in self._start_domains:
            self._scraped_domains.append(domain)
            yield self.CurrentIPsOfDomainRequest(domain)
            yield self.HistoryIPsOfDomainRequest(domain)

    def CurrentIPsOfDomainRequest(self, domain):
        return scrapy.Request(url = 'http://site.ip138.com/domain/read.do?domain={}'.format(domain), headers = {'Referer': 'http://site.ip138.com/{}'.format(domain)}, callback = self.current_ips_of_domain, meta = {'dont_session': True, 'domain': domain})

    def HistoryIPsOfDomainRequest(self, domain):
        return scrapy.Request(url = 'http://site.ip138.com/{}'.format(domain), headers = {'Referer': 'http://site.ip138.com'}, callback = self.history_ips_of_domain, meta = {'dont_session': True, 'domain': domain})

    def DomainsOfIPRequest(self, ip):
        return scrapy.Request(url = 'http://site.ip138.com/{}'.format(ip), headers = {'Referer': 'http://site.ip138.com/'}, callback = self.domains_of_ip, meta = {'dont_session': True, 'ip': ip})

    def ValidateRequest(self, ip):
        return scrapy.Request(url = self.VALIDATE_URL.format(ip), headers = {'Host': 'wenshu.court.gov.cn', 'Referer': 'http://wenshu.court.gov.cn'}, callback = self.validate_result, errback = self.validate_error, dont_filter = True, meta = {'ip': ip, 'dont_retry': True, 'dont_redirect': True, 'dont_session': True})

    def current_ips_of_domain(self, response):
        result = json.loads(response.text)
        if result and result.get('status', False):
            data = result.get('data', {})
            for item in data:
                ip = item.get('ip')
                if not (ip in self._scraped_ips):
                    self._scraped_ips.append(ip)
                    yield self.ValidateRequest(ip)

    def history_ips_of_domain(self, response):
        ips = response.css('.panel a::text').extract()
        for ip in ips:
            if not (ip in self._scraped_ips):
                self._scraped_ips.append(ip)
                yield self.ValidateRequest(ip)

    def domains_of_ip(self, response):
        dates = response.css('#list span.date::text').extract()
        domains = response.css('#list a::text').extract()
        if len(dates) != len(domains):
            print(dates)
            print(domains)
            logger.error('dates not equals domains!')
        for i in range(0, len(dates) - 1):
            date = dates[i].split('-----')[1]
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
                if date  > datetime.today() - timedelta(days=300):
                    domain = domains[i]
                    if not (domain in self._scraped_domains):
                        self._scraped_domains.append(domain)
                        yield self.CurrentIPsOfDomainRequest(domain)
                        yield self.HistoryIPsOfDomainRequest(domain)
                        logger.debug('scrape domain:     {}'.format(domain))
            except Exception as e:
                logger.error(e)

    def validate_result(self, response):
        title = response.xpath('//title/text()').extract_first()
        if title and (self.VALIDATE_TITLE in title):
            ip = response.meta['ip']
            if not (ip in self._scraped_cdns):
                self._scraped_cdns.append(ip)
                yield self.DomainsOfIPRequest(ip)
                logger.info(response.meta['download_slot'] + '  - GOOD')
        else:
            pass

    def validate_error(self, failure):
        # pass
        # self._fails_count += 1
        # if self._fails_count > 100:
        #     print(self._scraped_cdns)
        #     raise scrapy.exceptions.CloseSpider('Finished!')
        pass
        # logger.error('%s:%s', repr(failure), failure.request.url)

    def spider_closed(self, spider):
        final_cdns = ['182.140.227.166', '61.160.224.60', '61.240.144.201', '221.204.14.198', '112.25.60.196', '119.84.14.194']
        for ip in final_cdns + self._scraped_cdns:
            ip_prefix = '.'.join(ip.split('.')[0:3])
            if not (ip_prefix in self._scraped_cdn_prefixs):
                self._scraped_cdn_prefixs.append(ip_prefix)
                if not (ip in final_cdns):
                    final_cdns.append(ip)
        print(final_cdns)
        print(self._scraped_cdns)
        print(self._scraped_domains)
