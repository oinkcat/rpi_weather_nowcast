""" Get weather information from Yandex Nowcast Info """
# -*- coding: utf-8 -*-
import sys
import os
import bs4

def get_nowcast(city_code):
	""" Get nowcast information from Yandex Weather """

	with request_content(city_code) as flo:
		soup = bs4.BeautifulSoup(flo, 'html.parser')

	nowcast_node = soup.select('.maps-widget-fact__title')[0]
	nowcast_alert = nowcast_node.text

	return nowcast_alert

def request_content(city_code):
	url = 'https://yandex.ru/pogoda/{}'.format(city_code)
	os.system('wget -O pogoda.html {} 2> /dev/null'.format(url))

	return open('./pogoda.html')

def parse_nowcast(nowcast):
	time = 1
	negation = False
	will_start = False
	will_end = False
	parts = nowcast.split()

	for tok in parts:
		if tok.isnumeric():
			time = int(tok)
		elif 'час' in tok:
			time *= 60
		elif tok == 'не':
			negation = True
		elif tok == 'закончится' or tok == 'прекратится':
			will_end = True
		elif tok == 'ожидается' or tok == 'начнется':
			will_start = True
		elif tok == 'карту':
			time = -1

	return {
		'minutes': time,
		'going': will_end,
		'starting': will_start and not negation,
		'ending': will_end and not negation
	}

def get_info():
	""" Get current nowcast information """

	try:
		nowcast_text = get_nowcast(str())
		nowcast_info = parse_nowcast(nowcast_text)
		return {
			'raw': nowcast_text,
			'info': nowcast_info
		}
	except:
		return None

def test_from_file(filename):
	with open(filename) as ifp:
		for line in ifp.readlines():
			text = line.strip().lower()
			print(text)
			info = parse_nowcast(text)
			print(info)

def test_current():
	current_nowcast = get_nowcast(str())
	print(current_nowcast)
	current_info = parse_nowcast(current_nowcast)
	print(current_info)

if __name__ == '__main__':
	if len(sys.argv) > 1:
		test_from_file(sys.argv[1])
	else:
		test_current()