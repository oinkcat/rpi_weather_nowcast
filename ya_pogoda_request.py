# -*- coding: utf-8 -*-
import urllib.request
import http.cookiejar
import time

TEMPLATE = 'https://yandex.ru/pogoda/{0}'

def get_weather_page_content(city_code):
    global opener

    city_page = TEMPLATE.format(city_code)
    print(city_page)

    request = urllib.request.Request(city_page, headers={
        'Accept': '*/*',
        'User-Agent': 'ELinks/0.12~pre5-9 (textmode; Debian; Linux 4.1.19+ armv6l; 120x30-2)',
        'Referer': 'https://ya.ru/',
        'Connection': 'keep-alive',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en',
        'Pragma': 'no-cache'
    })

    return opener.open(request)

jar = http.cookiejar.CookieJar(http.cookiejar.DefaultCookiePolicy())
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

if __name__ == '__main__':
    while True:
        with get_weather_page_content('moscow?via=srp&lat=55.755863&lon=37.6177') as resp:
            msk_content = resp.read()
            print('FAIL' if msk_content.find(b'captcha') > -1 else 'SUCCESS')
            time.sleep(20)
