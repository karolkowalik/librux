#!/bin/python
# -*- coding: utf-8 -*-
"""Skrypt pobierający dane z Librusa

Uwaga: w Librusie nalezy w ustawieniach w "Dane konta uzytkownika"
wartość pola: "Używaj nowego systemu wiadomości" ustawic na NIE
"""

import re
import io
import time
import yaml
import pathlib
from smtplib import SMTP
from email.mime.text import MIMEText
from bs4 import BeautifulSoup as soup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

cfg = dict()
try:
	with open("cfg.yaml", 'r') as stream:
		cfg = yaml.load(stream, Loader=yaml.FullLoader)
except yaml.YAMLError as exc:
	print(exc)

urls = {
'loguj': 'https://portal.librus.pl/rodzina/synergia/loguj',
'glowna': 'https://synergia.librus.pl',
}

xpath_l = {	
'dd_menu':     '//*[@id="dropdownTopRightMenuButton"]',
'dd_synergia': '//*[@id="dropdownSynergiaMenu"]/a[2]',
'login_btn':   '//*[@id="LoginBtn"]',
'wiadomosci':  '//*[@id="icon-wiadomosci"]',
'oceny':       '//*[@id="icon-oceny"]'
}

def xpath_click(browser, xpath):
	"""Click the Web GUI element and wait for responce."""
	try:
		element = WebDriverWait(browser, 10).until(
			EC.presence_of_element_located((By.XPATH, xpath))).click()
	except:
			raise
	return  


def get_librus_connection(credentails):
	"""Set Selenium driver for mobile emulation and login to Librus."""
	try:
		chrome_options = Options()
		chrome_options.add_argument('--headless')
		chrome_options.add_argument('--no-sandbox')
		chrome_options.add_argument('--disable-dev-shm-usage')
		mobile_emulation = {
			"deviceMetrics": { "width": 360, "height": 640, "pixelRatio": 3.0 },
			"userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19" 
		}

		chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
		browser = webdriver.Chrome(cfg['chromedriver_path'],chrome_options=chrome_options)

		browser.get(urls['loguj'])

		xpath_click(browser, xpath_l['dd_menu'])
		time.sleep(1)
		xpath_click(browser, xpath_l['dd_synergia'])

		iframe = browser.find_element_by_xpath('//*[@id="caLoginIframe"]')
		browser.switch_to.frame(iframe)

		for k,v in credentails.items():
			field = browser.find_element_by_name(k)
			field.send_keys(v)
					
		xpath_click(browser, xpath_l['login_btn'])
		time.sleep(1)
	except:
			raise
	return browser 

def get_new_messages(browser):
	"""Get new messages from: Wiadomosci."""
	try:
		xpath_click(browser, xpath_l['wiadomosci'])
		messages = {}
		response=soup(browser.page_source, "html.parser")
		all_msg = response.findAll(class_=re.compile("line\d+"))
		for msg in all_msg:
			msg_info = msg.find_all('td')
			if msg_info[1].has_attr('style'):
				messages[msg.input['value']] =  dict(
					link='%s%s' % (urls['glowna'],msg.a['href']),
					teacher=msg_info[1].get_text(),
					subject=msg_info[2].get_text(),
					data=msg_info[3].get_text()
					)
	except:
			raise
	return messages


def get_old_messages(browser):
	"""Get all messages from: Wiadomosci."""
	try:
		xpath_click(browser, xpath_l['wiadomosci'])
		messages = {}
		#//*[@id="formWiadomosci"]/div/div/table
		response=soup(browser.page_source, "html.parser")
		all_msg = response.findAll(class_=re.compile("line\d+"))
		for msg in all_msg:
			msg_info = msg.find_all('td')
			messages[msg.input['value']] =  dict(
				link='%s%s' % (urls['glowna'],msg.a['href']),
				teacher=msg_info[1].get_text(),
				subject=msg_info[2].get_text(),
				data=msg_info[3].get_text()
				)
	except:
			raise
	return messages


def check_mark(mark,  marks, new_marks, all_td):
	"""Get all marks from: Oceny."""
	subject = all_td[0].get_text()
	subject.strip()
	cleanr = re.compile('<.*?>')
	title = str(re.sub(cleanr, ', ', mark["title"]))
	if title not in marks.keys():
		marks[title] =  dict(
			subject=subject,
			mark_value=mark.get_text(),
			)
		new_marks[title] =  dict(
			subject=subject,
			mark_value=mark.get_text(),
			)


def get_marks(browser, student):
	"""Get all marks from: Oceny."""
	xpath_click(browser, xpath_l['oceny'])
	response=soup(browser.page_source, "html.parser")
	marks = {}
	new_marks = {}
	marks_filename = '%s.yaml' % (student)
	try:
		with open(marks_filename, 'r') as stream:
			marks = yaml.load(stream, Loader=yaml.FullLoader)
	except FileNotFoundError:
		marks = {}
	secondtable = response.findAll('table', {'class': 'decorated'})[1]
	all_rows = secondtable.findAll("tr", class_=re.compile("^line\d$"))
	for row in all_rows:
		td = row.find("td", {'class': 'screen-only'})
		try:
			all_td = td.find_next_siblings("td")
			semester_one_marks = all_td[1].findAll("a")
			for mark in semester_one_marks:
				check_mark(mark, marks, new_marks, all_td)
			semester_two_marks = all_td[5].findAll("a")
			for mark in semester_two_marks:
				check_mark(mark, marks, new_marks, all_td)
		except (AttributeError, TypeError, IndexError):
			td = ''   
	with io.open(marks_filename, 'w', encoding='utf8') as outfile:
		yaml.dump(marks, outfile, default_flow_style=False, allow_unicode=True)
	return new_marks


def get_message_body(browser,message):
	"""Get idividual message."""
	try:
		browser.get(message['link'])
		response=soup(browser.page_source, "html.parser")
		body =  u'%s' % response.find_all('div',class_="container-message-content")[0]
	except:
		raise
	return body


def set_smtp_connection():
	"""Set SMTP connection."""
	try:
		server = SMTP(cfg['email']['smtp_host'], cfg['email']['port'])
		server.set_debuglevel(0)
		server.ehlo()
		server.starttls()
		server.login(cfg['email']['username'], cfg['email']['password'])
	except:
		raise
	return server


def gen_msg_email(message):
	"""Generate email body for a message."""
	try:
		content = """
<h3>Nauczyciel: %s</h3>
<small>data: %s</small><br>

<div style="border: 1px solid; padding: 10px; box-shadow: 5px 10px 8px #888888; background-color: Ivory;">
%s
</div> """ % (message['teacher'],message['data'],message['body'])
		msg = MIMEText(content, 'html', 'utf-8')
		msg["From"] = "Librus %s <%s>" % (message['student'], cfg['email']['username'])
		msg['To'] = ", ".join(cfg['email']['to'])
		msg['subject'] = "[%s] %s" % (message['student'], message['subject'])
		msg['Content-Type'] = "text/html; charset=utf-8"
	except:
		raise
	return msg


def gen_mark_email(marks, student):
	"""Generate email body for a set of new marks."""
	content = ""
	for desc in marks.keys():
		content += "<em><b>%s</b>: %s</em><br><small>Opis: <i>%s</i></small><br>\n" % ( marks[desc]['subject'],marks[desc]['mark_value'],desc)
	msg = MIMEText(content, 'html', 'utf-8')
	msg["From"] = "Librus %s <%s>" % (student, cfg['email']['username'])
	msg['To'] = ", ".join(cfg['email']['to'])
	msg['subject'] = "[%s] %s" % (student, 'Nowe oceny')
	msg['Content-Type'] = "text/html; charset=utf-8"
	return msg


def main():
	"""Main Loop."""
	smtp_con = set_smtp_connection()
	for student,credentails in cfg['students'].items():
		print("[INFO]: Pobieranie ocen dla studenta: %s" % student)
		browser_con = get_librus_connection(credentails)
		marks = get_marks(browser_con, student)
		if len(marks):
			msg = gen_mark_email(marks, student)
			smtp_con.sendmail(cfg['email']['username'], cfg['email']['to'], msg.as_string())
			print("\t[INFO]: Wysylanie wiadomosci z ocenami")
		print("[INFO]: Pobieranie wiadomosci dla studenta: %s" % student)
		messages = get_new_messages(browser_con)
		#messages = get_old_messages(browser_con)
		for k,v in messages.items():
			messages[k]['student'] = student
			messages[k]['body'] = get_message_body(browser_con,v)
			msg = gen_msg_email(v)
			print("\t[INFO]: Wysylanie wiadomosci od nauczyciela: %s" % messages[k]['teacher'])
			smtp_con.sendmail(cfg['email']['username'], cfg['email']['to'], msg.as_string())
	smtp_con.quit()


if __name__ == '__main__':
	main()


