import os
import time
import logging
import scrapy
import asyncio
from pyppeteer import launch

def patch_pyppeteer():
    import pyppeteer.connection
    original_method = pyppeteer.connection.websockets.client.connect

    def new_method(*args, **kwargs):
        kwargs['ping_interval'] = None
        kwargs['ping_timeout'] = None
        return original_method(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_method

patch_pyppeteer()

__all__ = ['getKey', 'decryptDocID', 'decryptDocIDs', 'decryptListContent', 'f80sCookie', 'f80tCookie', 'f80tCookies', 'free']

logger = logging.getLogger(__name__)

browser = None
page = None

WENSHU_SERVER = 'wenshu.court.gov.cn' #'58.20.19.13'
f80s = None
f80t = None

JS_FILES = ['wenshu.vl5x.js', 'wenshu.docid.js', 'Base64.js', 'core-min.js', 'pako.min.js', 'rawinflate.js', 'aes.js']

async def init():
	global browser, page, f80s
	browser = await launch(headless=True, logLevel=logging.ERROR)#, handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False, autoClose=False)
	page = await browser.newPage()
	await page.setUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36")
	await page.setRequestInterception(True)
	async def intercept(request):
		if request.isNavigationRequest() or 'http://' + WENSHU_SERVER + '/4QbVtADbnLVIc/d.FxJzG50F.6152bb9.js' in request.url:
			await request.continue_()
		else:
			await request.abort()
	page.on('request', lambda req: asyncio.ensure_future(intercept(req)))

	await page.setExtraHTTPHeaders({'Host': 'wenshu.court.gov.cn'})

	inject_script = """
		(function() {
			Object.defineProperty(navigator, 'webdriver', {
				get: () => undefined,
			});
			var _native_set_interval = setInterval;
			window['setInterval'] = function(callback, repeat) {
				var match = callback.toString()
					.match(/\\){var.*?=(.*?)\\(/);
				if (match) {
					window._theFunction = match[1];
				}
			};
			var _native_set_timeout = setTimeout;
			window['setTimeout'] = function(callback, timeout) {};
			window['f80tCookie'] = function() {
				return window[window._theFunction]();
			}
		}())"""

	await page.evaluateOnNewDocument(inject_script)
	await page.goto('http://' + WENSHU_SERVER)
	await page.evaluateOnNewDocument(inject_script)
	await page.reload()

	js_all = ''
	for jsfile in JS_FILES:
		jsfile = os.path.dirname(__file__) + '/../wenshu/js/' + jsfile
		js_all += open(jsfile, encoding='utf8').read()

	wshelper = """(function(){
		var window = {};
		var document = {};
		var location = {};

		//JS_FILES

		function test(info) {
			return info;
		}

		wshelper = {
			getKey: getKey,
			decryptDocID: decryptDocID,
			decryptDocIDs: decryptDocIDs,
			decryptListContent: decryptListContent,
			f80tCookie: f80tCookie,
			f80tCookies: function(num) {
				var cookies = [];
				for (var i = 0; i < num; i++) {
					cookies.push(f80tCookie());
				}
				return cookies;
			}
		}
	}())"""
	wshelper = wshelper.replace('//JS_FILES', js_all)
	await page.evaluate(wshelper)

	cookies = await page.cookies()
	for cookie in cookies:
		if cookie['name'] == 'FSSBBIl1UgzbN7N80S':
			f80s = cookie['value']

	if not f80s:
		raise Exception("Error: get f80s failed!")

try:
	loop = asyncio.get_event_loop()
	loop.run_until_complete(init())
	logger.info('wshelper initialize success!')
except Exception as e:
	logger.error(e)
	loop.run_until_complete(browser.close())
	raise scrapy.exceptions.CloseSpider('failed to initialize pyppeteer session!')

def getKey(vjkl5):
	return loop.run_until_complete(page.evaluate("wshelper.getKey", vjkl5))

def decryptDocID(runEval, docid):
	return loop.run_until_complete(page.evaluate("wshelper.decryptDocID", runEval, docid))

def decryptDocIDs(runEval, docids):
	return loop.run_until_complete(page.evaluate("wshelper.decryptDocIDs", runEval, docids))

def decryptListContent(data):
	result = loop.run_until_complete(page.evaluate("wshelper.decryptListContent", data))
	if result[0] == -1:
		raise Exception('Error: ' + result[1])
	else:
		return result

def f80sCookie():
	return f80s

def f80tCookie():
	return loop.run_until_complete(page.evaluate("wshelper.f80tCookie()"))

def f80tCookies(num):
	return loop.run_until_complete(page.evaluate("wshelper.f80tCookies", num))

def free():
	if browser:
		loop.run_until_complete(browser.close())
		loop.stop()


# signal.pause()
# print(f80tCookie())
# free()