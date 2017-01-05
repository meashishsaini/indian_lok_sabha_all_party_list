import scrapy
import re
from scrapy.crawler import CrawlerProcess
import scraperwiki

NAME_WITH_LINK = 1
class PartyListSpider(scrapy.Spider):
	name = "partylist"
	terms = 1

	def __init__(self, terms=1, *args, **kwargs):
		super(PartyListSpider, self).__init__(*args, **kwargs)
		self.terms = terms	

	def start_requests(self):
		for term in range(int(self.terms)-1):
			url = "http://164.100.47.194/Loksabha/Members/partyar.aspx?lsno="+str(term+1)
			yield scrapy.Request(url=url, callback=self.other_terms)
		url = "http://164.100.47.194/Loksabha/Members/PartywiseList.aspx"
		yield scrapy.Request(url=url, callback=self.current_term)

	def other_terms(self, response):
		for party in response.xpath('//*[@class="member_list_table"]/tr'):
			td = party.xpath('td')
			name_with_link_td = td[NAME_WITH_LINK]
			name = name_with_link_td.xpath('a/text()').extract_first()
			url = response.urljoin(name_with_link_td.xpath('a/@href').extract_first())
			request = scrapy.Request(url=url, callback=self.parse_terms)
			request.meta['name'] = name
			yield request

	def current_term(self, response):
		for party in response.xpath('//*[@class="member_list_table"]/tr'):
			td = party.xpath('td')
			name_with_link_td = td[NAME_WITH_LINK]
			name = name_with_link_td.xpath('a/text()').extract_first()
			target = name_with_link_td.xpath('a/@href').extract_first().replace("javascript:__doPostBack('",'').strip("',')")
			request =  scrapy.FormRequest.from_response(
				response,
				formdata={
						'__EVENTTARGET': target,
					  },
					  dont_click=True,
				callback=self.parse_terms,
				)
			request.meta['name'] = name
			yield request

	def parse_terms(self, response):
		partyname = response.xpath('//*[@id="ContentPlaceHolder1_hidParty"]/@value|//*[@id="ContentPlaceHolder1_Label2"]/text()').extract_first()
		partyname = partyname.replace("Party : ",'',1)
		partyshortname = self.remove_brackets(string=response.meta['name'].replace(partyname,'',1))
		url = response.url
		tmp = re.search("(?<=party_code=)\d+",url)
		if tmp != None:
			partyid = tmp.group()
		scraperwiki.sqlite.save(
			unique_keys=['id'],
			data={
			"id": partyid, 
			"partyname": partyname,
			"partyshortname": partyshortname,
			"link": response.url
			}
			)

	def remove_brackets(self, string):
		if string.startswith('(') and string.endswith(')'):
			return string[1:-1]
		else:
			return string

process = CrawlerProcess()
process.crawl(PartyListSpider, terms=16)
process.start()