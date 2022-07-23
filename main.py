import io
import os
import random
import sys
import time
import urllib.request
from multiprocessing import Pool
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = 'https://www.farfetch.cn/cn/shopping/women/clothing-1/items.aspx?page=1&view=90&sort=3&category=136137'
ROOT = 'D:\\HIT\\6\\farfetch dataset\\'
CATEGORY = 'shirt\\'
PAGE_FIRST = 0
PAGE_LAST = 78

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')
# -----------------------改变selenium参数---------------------------
# -----------------------设置参数 excludeSwitches-------------------
option = webdriver.ChromeOptions()
# option.add_experimental_option('excludeSwitches', ['enable-automation'])
# option.add_experimental_option("debuggerAddress", "localhost:9222")

browser = webdriver.Chrome(executable_path='D:\\HIT\\6\\chromedriver.exe', options=option)
# -----------------------cdp 命令----------------------------------
browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
     Object.defineProperty(navigator, 'webdriver', {
       get: () => undefined
     })
   """
})

wait = WebDriverWait(browser, 10)


def loadContentPage(url, browser, page):
    browser.get(url)
    wait.until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="slice-container"]/div[3]/div[2]/div[2]/div/div[1]/ul'))
    )
    html = browser.page_source
    soup = BeautifulSoup(html)
    productArea = soup.find(attrs={'data-testid': 'productArea'})
    for productCard in productArea.find_all(attrs={'data-testid': 'productCard'}):
        item_url = 'https://www.farfetch.cn' + productCard['itemid']
        try:
            loadItemPage(item_url, browser, page)
        except Exception as e:
            print(e)
            file = open(ROOT + CATEGORY + 'errorInfo.txt', 'a+', encoding='utf-8')
            file.write(item_url)
            file.write('\n')
            file.close()


#        print(item_url)

def loadItemPage(itemUrl, browser, page):
    print('current: ', itemUrl)
    print('the current is No.' + str(page) + ' page.')
    flag = os.path.exists(os.path.join(ROOT + CATEGORY, getId(itemUrl)))
    browser.get(itemUrl)
    time.sleep(random.randint(3, 7))
    if not flag:
        js = "return action=document.body.scrollHeight"
        height = browser.execute_script(js)
        num_sc = height
        for i in range(0, num_sc, 1000):
            js = 'window.scrollTo(0,%s)' % int(height * (i / height))
            browser.execute_script(js)
            time.sleep(random.randint(3, 7))

        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            '#panelInner-0 > div > div:nth-child(2) > div > div:nth-child(4) > div > p:nth-child(3)'))
        )

        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            '#content > div.css-1nzbnkt-Fraction > div.css-vazfsc-Fraction > div > div > div > section > div > div.eeqshdj0.css-qgtnwj-CarouselContainer-CarouselStandard.e2e37340 > div'))
        )

        html = browser.page_source

        itemPage = {}
        itemPage['itemInfo'] = getclothesAttrs(html, itemUrl)
        itemPage['model'] = getModelInfo(html)
        itemPage['outfit'] = getOutfit(html)
        itemPage['recommendation'] = getRecommendationItems(html)
        printClothingInfo(ROOT + CATEGORY, itemPage, html)


def getclothesAttrs(html, url):
    itemInfo = {}
    itemInfo['url'] = url
    itemInfo['id'] = getId(url)
    imageLinks = []
    soup = BeautifulSoup(html)

    imageset = soup.find_all(attrs={'class': '_4accab'})
    for image in imageset:
        for i_1 in image.find_all(name='img'):
            imageLinks.append(i_1['src'])

    # print(imageLinks)
    itemInfo['imageLinks'] = imageLinks

    bannerCompenent = soup.find(attrs={'id': 'bannerComponents-Container'})
    brand = bannerCompenent.find(attrs={'class': '_af2f5c'}).text
    name = bannerCompenent.find(attrs={'data-tstid': 'cardInfo-description'}).text

    # print(brand,name)
    itemInfo['name'] = name
    itemInfo['brand'] = brand

    keyword = ''
    for i in soup.find_all(attrs={'class': '_ab46e0'}):
        keyword = keyword + i.text
    # print(keyword)
    itemInfo['keyword'] = keyword

    material = soup.find(attrs={'class': '_aa69b4'}).text
    # print(material)
    itemInfo['material'] = material
    return itemInfo


## 通过连接提取物品的id
def getId(url):
    id1 = url.split('.aspx')[0]
    id = id1.split('item-')[1]
    # print(id)
    return id


def getModelInfo(html):
    model = {}
    soup = BeautifulSoup(html)
    modelLink = soup.find(attrs={'data-tstid': 'details-wearing'})
    modelhigh = modelLink.find(attrs={'data-tstid': 'modelFittingInformation'}).text
    height = modelhigh.split('米')[0].split('模特身高')[1]
    model['height'] = height.replace(' ', '')
    clothing = []
    modelclothingLink = modelLink.find_all('a')
    # print(len(modelclothingLink))
    for cloth in modelclothingLink:
        # print('cloth',cloth)
        name = cloth.text
        id = getId(cloth['href'])
        clothing.append({'id': id, 'name': name})
    model['clothes'] = clothing

    imageclass = soup.find(attrs={'class': '_97b23b'})
    image = imageclass.find(attrs={'data-tstid': 'detailsImage'})
    model['image'] = image['src']
    # print(model)
    return model


def getOutfit(html):
    outfit = {}
    soup = BeautifulSoup(html)
    compeleteLink = soup.find(attrs={'data-tstid': 'shopTheLook'})
    mainImage = compeleteLink.find(attrs={'data-tstid': 'mainLookImage'})
    outfit['mainImage'] = mainImage['src']
    outfit['items'] = []
    # [id,brand,name,image]
    otherLinks = compeleteLink.find_all(attrs={'data-tstid': 'shopTheLook-card'})
    for item in otherLinks:
        id = getId(item.find(attrs={'data-component': 'ProductCardLink'})['href'])
        image = item.find('img')['src']
        brand = item.find(attrs={'data-component': 'ProductCardBrandName'}).text
        name = item.find(attrs={'data-component': 'ProductCardDescription'}).text
        outfit['items'].append({'id': id, 'brand': brand, 'name': name, 'image': image})

    # print(outfit)
    return outfit


def getRecommendationItems(html):
    items = {}
    items['items'] = []
    soup = BeautifulSoup(html)
    itemLinks = soup.find(attrs={'data-component': 'ProductShowcase'})
    itemCards = itemLinks.find_all(attrs={'data-component': 'ProductCard'})
    # itemCards = itemLinks.find_all(attrs={'data-component':'ProductCard'})
    for item in itemCards:
        id = getId(item.find(attrs={'data-component': "ProductCardLink"})['href'])
        image = item.find('img')['src']
        brand = item.find(attrs={'data-component': 'ProductCardBrandName'}).text
        name = item.find(attrs={'data-component': 'ProductCardDescription'}).text
        items['items'].append({'id': id, 'brand': brand, 'name': name, 'image': image})

    # print(items)
    return items


def printClothingInfo(path, itemInfo, html):
    currentpath = os.path.join(path, itemInfo['itemInfo']['id'])
    mkdir(currentpath)
    # print(currentpath)
    ## 判断文件夹中是否存在itemInfo.txt文件
    ## 若存在则判断内容是否与itemInfo相同
    ## 不存在则建立新文件并写入itemInfo并且保存图片
    itemInfoPath = os.path.join(currentpath, 'itemInfo.txt')
    source_html_path = os.path.join(currentpath, 'source_html.txt')
    if os.path.exists(itemInfoPath):
        file = open(itemInfoPath, 'r+', encoding='utf-8')
        dic = eval(file.read())  # 读取的str转换为字典
        if dic == itemInfo:
            print(True)
        else:
            print(False)
        file.close()
    else:
        file = open(itemInfoPath, 'w+', encoding='utf-8')
        file.write(str(itemInfo))
        file.close()
        source_html_file = open(source_html_path, 'w+', encoding='utf-8')
        source_html_file.write(str(html))
        source_html_file.close()
        savebaseInfo(currentpath, itemInfo['itemInfo'])
        savemodelInfo(currentpath, itemInfo['model'])
        saveoutfitInfo(currentpath, itemInfo['outfit'])
        saverecommendationInfo(currentpath, itemInfo['recommendation'])

    ## 建立baseInfo文件夹，建立baseInfo.txt并保存图片

    ## 建立model文件夹，建立model.txt并保存图片

    ## 建立outfit文件夹，建立outfit.txt并保存图片

    ## 建立recommendation文件夹，建立recommendation.txt并保存图片


def mkdir(path):
    folder = os.path.exists(path)

    if not folder:  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(path)  # makedirs 创建文件时如果路径不存在会创建这个路径
    #     print
    #     "---  new folder...  ---"
    #     print
    #     "---  OK  ---"
    #
    # else:
    #     print
    #     "---  There is this folder!  ---"


def savebaseInfo(path, baseInfo):
    baseInfoPath = os.path.join(path, 'baseInfo')
    mkdir(baseInfoPath)
    baseInfotxtPath = os.path.join(baseInfoPath, 'baseInfo.txt')
    file = open(baseInfotxtPath, 'w+', encoding='utf-8')

    file.write(str(baseInfo))
    file.close()
    saveImage(baseInfoPath, baseInfo['imageLinks'])


def savemodelInfo(path, modelInfo):
    modelInfoPath = os.path.join(path, 'modelInfo')
    mkdir(modelInfoPath)
    modelInfotxtPath = os.path.join(modelInfoPath, 'modelInfo.txt')
    file = open(modelInfotxtPath, 'w+', encoding='utf-8')
    file.write(str(modelInfo))
    file.close()
    saveImage(modelInfoPath, [modelInfo['image']])


def saveoutfitInfo(path, outfitInfo):
    outfitInfoPath = os.path.join(path, 'outfitInfo')
    mkdir(outfitInfoPath)
    outfitInfotxtPath = os.path.join(outfitInfoPath, 'outfitInfo.txt')
    file = open(outfitInfotxtPath, 'w+', encoding='utf-8')
    file.write(str(outfitInfo))
    file.close()

    urllib.request.urlretrieve(outfitInfo['mainImage'],
                               filename=os.path.join(outfitInfoPath, getImageName(outfitInfo['mainImage'])))

    for item in outfitInfo['items']:
        urllib.request.urlretrieve(item['image'], filename=os.path.join(outfitInfoPath, getImageName(item['image'])))


def saverecommendationInfo(path, recommendationInfo):
    recommendationInfoPath = os.path.join(path, 'recommendationInfo')
    mkdir(recommendationInfoPath)
    recommendationInfotxtPath = os.path.join(recommendationInfoPath, 'recommendationInfo.txt')
    file = open(recommendationInfotxtPath, 'w+', encoding='utf-8')
    file.write(str(recommendationInfo))
    file.close()

    for item in recommendationInfo['items']:
        urllib.request.urlretrieve(item['image'],
                                   filename=os.path.join(recommendationInfoPath, getImageName(item['image'])))


def saveImage(path, imageLinks):
    for imageurl in imageLinks:
        print('saving image...')
        urllib.request.urlretrieve(imageurl, filename=os.path.join(path, getImageName(imageurl)))


def getImageName(url):
    urlHead = url.split('.jpg')[0]
    fileName = urlHead.split('/')[len(urlHead.split('/')) - 1]
    # print(fileName)
    return fileName + '.jpg'


def main():
    url = URL
    url_split = url.split('page=1')
    for i in range(PAGE_FIRST, PAGE_LAST):
        url_fresh = url_split[0] + 'page=' + str(i + 1) + url_split[1]
        # print(url_fresh)
        loadContentPage(url_fresh, browser, i + 1)


if __name__ == '__main__':
    main()
    # file = open("item.txt", "r", encoding='utf-8')
    # str = file.read()
    # urlList = str.split('\n')
    # print(len(urlList))
    # print(urlList[100])
