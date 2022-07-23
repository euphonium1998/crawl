import requests
import time

URL = "https://www.farfetch.cn/cn/plpslice/listing-api/products-facets?page=1&view=90&sort=3&category=136099" \
          "&pagetype=Shopping&rootCategory=Women&pricetype=FullPrice&c-category=135967"
PAGE_FIRST = 0
PAGE_LAST = 78

def main():
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36 Edg/103.0.1264.37"}
    url_split = URL.split('page=1')
    file = open("item.txt", "a+", encoding='utf-8')

    for i in range(PAGE_FIRST, PAGE_LAST):
        url_fresh = url_split[0] + 'page=' + str(i + 1) + url_split[1]
        print('page[' + str(i+1) + ']')
        resp = requests.get(url_fresh, headers=headers)
        time.sleep(1)
        items = resp.json()['listingItems']['items']
        for item in items:
            file.write("https://www.farfetch.cn" + item['url'] + '\n')
    file.close()


if __name__ == '__main__':
    main()