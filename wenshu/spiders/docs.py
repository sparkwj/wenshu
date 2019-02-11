# -*- coding: utf-8 -*-
import uuid
import re
import json
import time
import logging
import random
import time
import execjs
import scrapy
from scrapy.http import Response, TextResponse

logger = logging.getLogger(__name__)


class DocsSpider(scrapy.Spider):
	name = 'docs'
	allowed_domains = ['wenshu.court.gov.cn']
	start_urls = []

	# custom_settings = {
	# 	'CONCURRENT_REQUESTS_PER_IP': 1,
	# 	'DOWNLOAD_DELAY': 5
	# }

	DOC_KEY_MAP = {
		"法院ID": "court_id",
		"案号": "case_no",
		"法院地市": "court_city",
		"法院省份": "court_province",
		"文本首部段落原文": "text_header_body",
		"法院区域": "court_area",
		"案件名称": "case_name",
		"法院名称": "court_name",
		"裁判要旨段原文": "trial_summary",
		"DocContent": "raw_DocContent",
		"补正文书": "correct_doc",
		"诉讼记录段原文": "lawsuit_record_body",
		"判决结果段原文": "trial_result_body",
		"文本尾部原文": "text_footer_body",
		"上传日期": "upload_date",
		"案件类型": "case_type_id",
		"诉讼参与人信息部分原文": "participate_body",
		"审判程序": "trial_round",
		"法院区县": "court_country",
		"文书类型": "doc_type",
		"文书全文类型": "doc_full_type",
		"裁判日期": "trial_date",
		"结案方式": "close_type",
		"效力层级": "effect_level",
		"不公开理由": "secret_reason",
		"案件基本情况段原文": "case_base_summary",
		"附加原文": "additional_summary"
	}

	DOC_PATTERN = r'.*?caseinfo=JSON\.stringify\(({.*?})\);\$\(document.*?jsonHtmlData\s=\s.*?(.*?);\s+var'

	DOC_URL = "http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?DocID="

	CONCURRENT_REQUESTS_PER_PROXY = 16

	handle_httpstatus_all = True

	def start_requests(self):
		for x in range(0, self.CONCURRENT_REQUESTS_PER_PROXY):
			time.sleep(random.random())
			request = self.DocRequest()
			if not request: break
			yield request

	def CaptChaRequest(self):
		return scrapy.Request(url = self.CAPTCHA_URL + str(random.randint(1, 9999)), callback = self.parse_captcha, errback = self.other_error, meta = {'dont_delay': True})

	def CaptChaValidateRequest(self, captcha_code):
		return scrapy.FormRequest(url = self.CAPTCHA_VALIDATE_URL, formdata = {'ValidateCode': captcha_code}, callback = self.parse_captcha_validate, errback = self.other_error, meta = {'dont_delay': True})

	def CaptChaSovleRequest(self, prepped):
		return scrapy.Request(url = self.CAPTCHA_SOLVE_URL, method = 'POST', headers = prepped.headers, body = prepped.body, callback = self.parse_captcha_solve, errback = self.other_error, meta = {'dont_delay': True})

	def DocRequest(self):
		doc = self.doc_pipeline.next_doc_task()
		if doc is None:
			raise scrapy.exceptions.CloseSpider('All docs all scraped!')

		url = self.DOC_URL + doc.get('doc_id', '')
		return scrapy.Request(
			url = url,
			headers = {'Referer': url},
			dont_filter = True,
			callback = self.parse_doc,
			errback = self.parse_doc,
			meta = {
				'referer': url,
				'handle_httpstatus_all': True,
				'doc': doc
			}
		)

	def parse_doc(self, response):

		# print('===================', response.request.meta)

		# print('=============', self.session_ware._get_session(response))

		remind_status = self.session_ware.get_remind_status(response)
		doc = response.request.meta['doc']

		try:

			if not (isinstance(response, TextResponse)) or response.status != 200:
				return

			if not remind_status == 0:
				return

			elif re.match('^window.location', response.text):
				if remind_status == 0:
					self.session_ware.set_remind_status(response, 1)
				logger.info('Meet captcha, will try to solve')
				return

			match = re.match(self.DOC_PATTERN, response.text, re.S)

			json_string = match.group(1)
			json_string = json_string.replace('\r', '').replace('\n', '').replace('\t', '')
			data = json.loads(json_string)

			for key in self.DOC_KEY_MAP.keys():
				doc[self.DOC_KEY_MAP[key]] = data.get(key, None)


			json_string = match.group(2)
			json_string = json_string.replace('\r', '').replace('\n', '').replace('\t', '')
			json_string = eval(json_string)

			data = json.loads(json_string)

			doc['publish_date'] = data.get('PubDate')
			doc['case_content'] = data.get('Html', response.text)


			upload_date = doc.get('upload_date', '')
			match = re.match(r'/Date\((.*?)\)/', upload_date)
			if match:
				upload_date = match.group(1)
				upload_date = time.localtime(int(upload_date)/1000.0)
				doc['upload_date'] = time.strftime('%Y-%m-%d', upload_date)

			doc['case_content'] =  doc.get('case_content', '').replace('01lydyh01', "'")

			doc['fails'] = 0
			doc['status'] = 1

		except:
			doc['fails'] = int(doc.get('fails', 0)) + 1
			logger.error('Error parse doc response:\n{}'.format(response.text), exc_info=True, extra={'response': response})

		finally:

			if doc.get('status', 0) == -1:
				doc['status'] = 0
			yield doc

			if remind_status == 1:
				self.session_ware.set_remind_status(response, -1)
				yield self.CaptChaRequest();

			yield self.DocRequest()



	def parse_captcha(self, response):
		if isinstance(response, Response) and response.status == 200:
			files = {'captcha_image': response.body}
			prepped = requests.Request('POST', self.CAPTCHA_SOLVE_URL, files=files).prepare()
			yield self.CaptChaSovleRequest(prepped)
		else:
			logger.info('Failed to get captcha, retrying...')
			yield self.CaptChaRequest()

	def parse_captcha_validate(self, response):
		if response.text == '1':
			logger.info('Success solve remind!')
			self.session_ware.set_remind_status(response, 0)
		else:
			logger.info('Retry solve captcha...')
			yield self.CaptChaRequest()

	def parse_captcha_solve(self, response):
		if len(response.text) > 0:
			yield self.CaptChaValidateRequest(response.text)
		else:
			logger.error('Not recognize the captcha')
			yield self.CaptChaRequest()

	def other_error(self, failure):
		raise scrapy.exceptions.CloseSpider(failure.getErrorMessage())
		

