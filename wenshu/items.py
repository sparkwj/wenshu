# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class WenshuItem(scrapy.Item):
	pass

class ProxyItem(scrapy.Item):
	ip = scrapy.Field()
	port = scrapy.Field()
	protocol = scrapy.Field()
	fails = scrapy.Field()
	valid = scrapy.Field()
	lastupdate = scrapy.Field()
	source = scrapy.Field()

class TaskItem(scrapy.Item):
	task_id = scrapy.Field()

	cursor = scrapy.Field()

	status = scrapy.Field()
	fails = scrapy.Field()
	doc_count = scrapy.Field()

	year = scrapy.Field()
	month = scrapy.Field()
	day = scrapy.Field()
	court_area = scrapy.Field()
	middle_court = scrapy.Field()
	basic_court = scrapy.Field()
	court_level = scrapy.Field()
	doc_type = scrapy.Field()
	page = scrapy.Field()

class DocItem(scrapy.Item):
	auto_id = scrapy.Field() #自动id
	doc_id = scrapy.Field() #文档id
	case_name = scrapy.Field() #案件名称
	case_no = scrapy.Field() #案号
	case_content = scrapy.Field() #文档正文

	status = scrapy.Field() #状态
	fails = scrapy.Field()

	trial_date = scrapy.Field() #裁判日期
	upload_date = scrapy.Field() #上传日期
	publish_date = scrapy.Field() #发布日期

	case_type = scrapy.Field() #案件类型
	case_type_id = scrapy.Field() #案件类型id
	trial_round = scrapy.Field() #审判程序

	province = scrapy.Field() #省份
	doc_type = scrapy.Field() #文书类型

	court_id = scrapy.Field() #法院ID
	court_name = scrapy.Field() #法院名称
	court_type = scrapy.Field() #法院层级
	court_province = scrapy.Field() #法院省份
	court_city = scrapy.Field() #法院地市
	court_area = scrapy.Field() #法院区域
	court_country = scrapy.Field() #法院区县

	lawsuit_record_body = scrapy.Field() #诉讼记录段原文
	case_base_summary = scrapy.Field() #案件基本情况段原文
	additional_summary = scrapy.Field() #附加原文
	participate_body = scrapy.Field() #诉讼参与人信息部分原文
	trial_summary = scrapy.Field() #裁判要旨段原文
	trial_result_body = scrapy.Field() #判决结果段原文
	text_header_body = scrapy.Field() #文本首部段落原文
	text_footer_body = scrapy.Field() #文本尾部原文

	close_type = scrapy.Field() #结案方式
	secret_reason = scrapy.Field() #不公开理由
	effect_level = scrapy.Field() #效力层级
	doc_full_type = scrapy.Field() #文书全文类型
	correct_doc = scrapy.Field() #补正文书
	raw_DocContent = scrapy.Field() #DocContent

# 审判程序: "再审审查与审判监督"

# 文书ID: "FcKOwrEVRDEIw4NWcsKAH8Kgw4QJw6w/w5LDpSo3fsKSOsOiwopJw4/DqljCmcOKw609DsOewq/CscOHw6fCnsOSwptpFMK9w5tCPEBvUsOMVE/DrsKZUDbDscKZwpXDhQxrw7V6wrfC…"

# 案件名称: "郇年春、网络科技时代海口实验学校与郇年春、网络科技时代海口实验学校项目转让合同纠纷申请再审民事裁定书"

# 案件类型: "2"

# 案号: "（2015）民申字第761号"

# 法院名称: "最高人民法院"

# 裁判日期: "2015-06-01"

# 裁判要旨段原文: "综上所述，郇年春的再审申请不符合《中华人民共和国民事诉讼法》第二百条第六项规定的情形。本院依照《中华人民共和国民事诉讼法》第二百零四条第一款之规定，裁定如下"

# Object Prototype


# $(function () {
#     $("#con_llcs").html("浏览：8942次")
# });
# $(function () {
#     var caseinfo = JSON.stringify({
#         "法院ID": "0",
#         "案件基本情况段原文": "",
#         "附加原文": null,
#         "审判程序": "再审审查与审判监督",
#         "案号": "（2014）民抗字第27号",
#         "法院地市": null,
#         "法院省份": null,
#         "文本首部段落原文": "",
#         "法院区域": null,
#         "文书ID": "a0c0e8f9-9ccc-4e1d-88ad-0318863351ed",
#         "案件名称": "康定县折多山沙石有限责任公司与四川康定机场有限责任公司沙石买卖合同纠纷抗诉民事裁定书",
#         "法院名称": "最高人民法院",
#         "裁判要旨段原文": "",
#         "法院区县": null,
#         "DocContent": "",
#         "补正文书": "2",
#         "诉讼记录段原文": "申诉人康定县折多山沙石有限责任公司因与被申诉人四川康定机场有限责任公司沙石买卖合同纠纷一案，不服四川省高级人民法院（2010）川民终字第30号民事判决，向检察机关申诉。最高人民检察院作出高检民抗（2013）61号民事抗诉书，以原审判决认定的基本事实缺乏证据证明与适用法律确有错误为由对本案提出抗诉",
#         "判决结果段原文": "",
#         "文本尾部原文": "",
#         "上传日期": "\/Date(1398761239000)\/",
#         "案件类型": "2",
#         "诉讼参与人信息部分原文": "",
#         "文书类型": null,
#         "文书全文类型": null,
#         "裁判日期": null,
#         "结案方式": null,
#         "效力层级": null,
#         "不公开理由": null
#     });
#     $(document).attr("title", "康定县折多山沙石有限责任公司与四川康定机场有限责任公司沙石买卖合同纠纷抗诉民事裁定书");
#     $("#tdSource").html("康定县折多山沙石有限责任公司与四川康定机场有限责任公司沙石买卖合同纠纷抗诉民事裁定书 （2014）民抗字第27号");
#     $("#hidDocID").val("a0c0e8f9-9ccc-4e1d-88ad-0318863351ed");
#     $("#hidCaseName").val("康定县折多山沙石有限责任公司与四川康定机场有限责任公司沙石买卖合同纠纷抗诉民事裁定书");
#     $("#hidCaseNumber").val("（2014）民抗字第27号");
#     $("#hidCaseInfo").val(caseinfo);
#     $("#hidCourt").val("最高人民法院");
#     $("#hidCaseType").val("2");
#     $("#HidCourtID").val("0");
#     $("#hidRequireLogin").val("0");
# });
# $(function () {});
# $(function () {
#     var jsonHtmlData = "{\"Title\":\"康定县折多山沙石有限责任公司与四川康定机场有限责任公司沙石买卖合同纠纷抗诉民事裁定书\",\"PubDate\":\"2014-04-29\",\"Html\":\"<a type='dir' name='WBSB'></a><div style='TEXT-ALIGN: center; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 0cm; FONT-FAMILY: 宋体; FONT-SIZE: 22pt;'>中华人民共和国最高人民法院</div><div style='TEXT-ALIGN: center; LINE-HEIGHT: 30pt; MARGIN: 0.5pt 0cm; FONT-FAMILY: 仿宋; FONT-SIZE: 26pt;'>民 事 裁 定 书</div><div style='TEXT-ALIGN: right; LINE-HEIGHT: 30pt; MARGIN: 0.5pt 0cm;  FONT-FAMILY: 仿宋;FONT-SIZE: 16pt; '>（2014）民抗字第27号</div><a type='dir' name='DSRXX'></a><div style='LINE-HEIGHT: 25pt;TEXT-ALIGN:justify;TEXT-JUSTIFY:inter-ideograph; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>抗诉机关：中华人民共和国最高人民检察院。</div><div style='LINE-HEIGHT: 25pt;TEXT-ALIGN:justify;TEXT-JUSTIFY:inter-ideograph; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>申诉人（一审原告、反诉被告，二审上诉人）：康定县折多山沙石有限责任公司。</div><div style='LINE-HEIGHT: 25pt;TEXT-ALIGN:justify;TEXT-JUSTIFY:inter-ideograph; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>法定代表人：姚世军，董事长。</div><div style='LINE-HEIGHT: 25pt;TEXT-ALIGN:justify;TEXT-JUSTIFY:inter-ideograph; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>被申诉人（一审被告、反诉原告，二审被上诉人）：四川康定机场有限责任公司。</div><div style='LINE-HEIGHT: 25pt;TEXT-ALIGN:justify;TEXT-JUSTIFY:inter-ideograph; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>法定代表人：谭亨，总经理。</div><a type='dir' name='CPYZ'></a><div style='LINE-HEIGHT: 25pt;TEXT-ALIGN:justify;TEXT-JUSTIFY:inter-ideograph; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>申诉人康定县折多山沙石有限责任公司因与被申诉人四川康定机场有限责任公司沙石买卖合同纠纷一案，不服四川省高级人民法院（2010）川民终字第30号民事判决，向检察机关申诉。最高人民检察院作出高检民抗（2013）61号民事抗诉书，以原审判决认定的基本事实缺乏证据证明与适用法律确有错误为由对本案提出抗诉。依照《中华人民共和国民事诉讼法》第二百零六条、第二百一十一条之规定，裁定如下：</div><a type='dir' name='PJJG'></a><div style='LINE-HEIGHT: 25pt;TEXT-ALIGN:justify;TEXT-JUSTIFY:inter-ideograph; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>一、本案指令四川省高级人民法院再审；</div><div style='LINE-HEIGHT: 25pt;TEXT-ALIGN:justify;TEXT-JUSTIFY:inter-ideograph; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>二、再审期间，中止原判决的执行。</div><a type='dir' name='WBWB'></a><div style='TEXT-ALIGN: right; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 72pt 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>审判长　何　抒</div><div style='TEXT-ALIGN: right; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 72pt 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>审判员　李桂顺</div><div style='TEXT-ALIGN: right; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 72pt 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>审判员　王云飞</div><br/><div style='TEXT-ALIGN: right; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 72pt 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>二〇一四年四月十五日</div><div style='TEXT-ALIGN: right; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 72pt 0.5pt 0cm;FONT-FAMILY: 仿宋; FONT-SIZE: 16pt;'>书记员　许冬冬</div>\"}";
#     var jsonData = eval("(" + jsonHtmlData + ")");
#     $("#contentTitle").html(jsonData.Title);
#     $("#tdFBRQ").html("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;发布日期：" + jsonData.PubDate);
#     var jsonHtml = jsonData.Html.replace(/01lydyh01/g, "\'");
#     $("#DivContent").html(jsonHtml);

#     //初始化全文插件
#     Content.Content.InitPlugins();
#     //全文关键字标红
#     Content.Content.KeyWordMarkRed();
# });