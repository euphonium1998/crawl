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
from selenium.webdriver.chrome.service import Service


ROOT = 'D:\\HIT\\6\\farfetch dataset\\'
CATEGORY = 'coat8\\'
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')
#-----------------------改变selenium参数---------------------------
#-----------------------设置参数 excludeSwitches-------------------
option = webdriver.ChromeOptions()
option.add_experimental_option('excludeSwitches', ['enable-automation'])
# # 去除特征值
# option.add_argument("--disable-blink-features=AutomationControlled")


service = Service('D:\\HIT\\6\\chromedriver.exe')
browser = webdriver.Chrome(service=service, options=option)
# -----------------------cdp 命令----------------------------------
browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
   "source": """
     Object.defineProperty(navigator, 'webdriver', {
       get: () => undefined
     })
   """
})



wait = WebDriverWait(browser,10)

def loadContentPage(url,browser,page):
    browser.get(url)
    wait.until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="slice-container"]/div[3]/div[2]/div[2]/div/div[1]/ul'))
    )
    html = browser.page_source
    soup = BeautifulSoup(html, features="html.parser")
    productArea = soup.find(attrs={'data-testid': 'productArea'})
    for productCard in productArea.find_all(attrs={'data-testid': 'productCard'}):
        item_url = 'https://www.farfetch.cn' + productCard['itemid']
        # loadItemPage(item_url, browser, page)
        try:
            loadItemPage(item_url,browser,page)
        except Exception as e:
            print(e)
            file = open(ROOT + CATEGORY + 'errorInfo.txt', 'a+', encoding='utf-8')
            file.write(item_url)
            file.write('\n')
            file.close()

#        print(item_url)

def loadItemPage(itemUrl,browser,page):
    print('current: ',itemUrl)
    print('the current is No.' + str(page) + ' page.')
    flag = os.path.exists(os.path.join(ROOT + CATEGORY, getId(itemUrl)))
    browser.get(itemUrl)
    time.sleep(random.randint(1, 2))
    if not flag:
        js = "return action=document.body.scrollHeight"
        height = browser.execute_script(js)
        num_sc = height
        for i in range(0, num_sc, 1000):
            js = 'window.scrollTo(0,%s)' % int(height * (i / height))
            browser.execute_script(js)
            time.sleep(random.randint(1, 2))

        wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/div/div[2]/div[1]/div'))
        )

        # wait.until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, '#content > div > div._ee30d4.ltr-1o5d34b'))
        # )

        html = browser.page_source


        itemPage = {}
        itemPage['itemInfo'] = getclothesAttrs(html, itemUrl)
        itemPage['model'] = getModelInfo(html)
        itemPage['outfit'] = getOutfit(html)
        itemPage['recommendation'] = getRecommendationItems(html)
        printClothingInfo(ROOT + CATEGORY, itemPage, html)
    else:
        print("already exist, skip")




def getclothesAttrs(html,url):
    itemInfo = {}
    itemInfo['url'] = url
    itemInfo['id'] = getId(url)
    imageLinks = []
    soup = BeautifulSoup(html, features="html.parser")

    imageset = soup.select('div._4accab > div')
    # print(len(imageset))
    for image in imageset:
        detail = image.select_one('img')
        imageLinks.append(detail['src'])

    # print(imageLinks)
    itemInfo['imageLinks'] = imageLinks


    bannerCompenent = soup.find(attrs={'class':'_071112 _beea20'})
    brand = bannerCompenent.find(attrs={'class':'_de2a9b _01a9a2 _c43773'}).text
    name = bannerCompenent.find(attrs={'class':'_20fb1a _2ef212 _b4693b'}).text

    # print(brand,name)
    itemInfo['name'] = name
    itemInfo['brand'] = brand

    keyword = ''

    for i in soup.find(attrs={'id':'panelInner-0'}):
        keyword = keyword + i.text
    # print(keyword)
    itemInfo['keyword'] = keyword
    material = ''
    material_1 = soup.find(attrs={'id':'panelInner-0'})
    material_2 = material_1.find(attrs={'class':'_aa69b4'})
    for m in material_2:
        material = material+m.text+' '

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
    soup = BeautifulSoup(html, features="html.parser")
    # for i in soup.find_all(attrs={'class':'ltr-92qs1a'}):
    #     modelLink = i
    # modelhigh = modelLink.find(attrs={'class':'ltr-4y8w0i-Body e1s5vycj0'}).text
    modelhigh = None
    try:
        modelLink = soup.find(attrs={'data-tstid': 'details-wearing'})
        modelhigh = modelLink.find(attrs={'data-tstid': 'modelFittingInformation'}).text
        height = modelhigh.split('米')[0].split('模特身高')[1]
        # print(height)
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
    except Exception as e:
        print(e)

    imageclass = soup.select_one('picture > source')
    # image = imageclass.find('img')
    model['image'] = imageclass['srcset'].split(' ')[0]
    # print(model)
    return model

def getOutfit(html):
    outfit = {}
    soup = BeautifulSoup(html, features="html.parser")
    # compeleteLink = soup.find(attrs={'id':'shopTheLook'})
    # compeleteLink = soup.select_one('div[data-tstid=shopTheLook]')
    try:
        mainImage = soup.select_one("#shopTheLook > div > div:nth-child(1) > img")
        outfit['mainImage'] = mainImage['src']
        outfit['items'] = []
        # [id,brand,name,image]
        otherLinks = soup.find_all(attrs={'data-tstid': 'shopTheLook-card'})
        for item in otherLinks:
            id = getId(item.find(attrs={'data-component': 'ProductCardLink'})['href'])
            image = item.find('img')['src']
            brand = item.find(attrs={'data-component': 'ProductCardBrandName'}).text
            name = item.find(attrs={'data-component': 'ProductCardDescription'}).text
            outfit['items'].append({'id': id, 'brand': brand, 'name': name, 'image': image})
    except Exception as e:
        print(e)

    # print(outfit)
    return outfit


def getRecommendationItems(html):
    items = {}
    items['items'] = []
    soup = BeautifulSoup(html, features="html.parser")
    itemLinks = soup.find(attrs={'class': '_a31960'})
    itemCards = soup.select('div[data-component=CarouselSlide]')
    # itemCards = itemLinks.find_all(attrs={'data-component':'ProductCard'})
    for item in itemCards:
        id = getId(item.find(attrs={'data-component':"ProductCardLink"})['href'])
        image = item.find('img')['src']
        brand = item.find(attrs={'data-component': 'ProductCardBrandName'}).text
        name = item.find(attrs={'data-component': 'ProductCardDescription'}).text
        items['items'].append({'id':id, 'brand':brand, 'name':name, 'image':image})

    # print(items)
    return items


def printClothingInfo(path,itemInfo,html):
    currentpath = os.path.join(path,itemInfo['itemInfo']['id'])
    mkdir(currentpath)
    # print(currentpath)
    ## 判断文件夹中是否存在itemInfo.txt文件
    ## 若存在则判断内容是否与itemInfo相同
    ## 不存在则建立新文件并写入itemInfo并且保存图片
    itemInfoPath = os.path.join(currentpath,'itemInfo.txt')
    source_html_path = os.path.join(currentpath,'source_html.txt')
    if os.path.exists(itemInfoPath):
        file = open(itemInfoPath, 'r+',encoding='utf-8')
        dic = eval(file.read())  # 读取的str转换为字典
        if dic == itemInfo:
            print(True)
        else:
            print(False)
        file.close()
    else:
        file = open(itemInfoPath, 'w+',encoding='utf-8')
        file.write(str(itemInfo))
        file.close()
        source_html_file = open(source_html_path, 'w+',encoding='utf-8')
        source_html_file.write(str(html))
        source_html_file.close()
        savebaseInfo(currentpath,itemInfo['itemInfo'])
        savemodelInfo(currentpath,itemInfo['model'])
        saveoutfitInfo(currentpath,itemInfo['outfit'])
        saverecommendationInfo(currentpath,itemInfo['recommendation'])

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

def savebaseInfo(path,baseInfo):
    baseInfoPath = os.path.join(path,'baseInfo')
    mkdir(baseInfoPath)
    baseInfotxtPath = os.path.join(baseInfoPath, 'baseInfo.txt')
    file = open(baseInfotxtPath, 'w+',encoding='utf-8')

    file.write(str(baseInfo))
    file.close()
    saveImage(baseInfoPath,baseInfo['imageLinks'])

def savemodelInfo(path,modelInfo):
    modelInfoPath = os.path.join(path,'modelInfo')
    mkdir(modelInfoPath)
    modelInfotxtPath = os.path.join(modelInfoPath, 'modelInfo.txt')
    file = open(modelInfotxtPath, 'w+',encoding='utf-8')
    file.write(str(modelInfo))
    file.close()
    saveImage(modelInfoPath,[modelInfo['image']])

def saveoutfitInfo(path,outfitInfo):
    outfitInfoPath = os.path.join(path,'outfitInfo')
    mkdir(outfitInfoPath)
    outfitInfotxtPath = os.path.join(outfitInfoPath, 'outfitInfo.txt')
    file = open(outfitInfotxtPath, 'w+',encoding='utf-8')
    file.write(str(outfitInfo))
    file.close()

    if outfitInfo != {}:
        urllib.request.urlretrieve(outfitInfo['mainImage'], filename=os.path.join(outfitInfoPath, getImageName(outfitInfo['mainImage'])))

        for item in outfitInfo['items']:
            urllib.request.urlretrieve(item['image'], filename=os.path.join(outfitInfoPath, getImageName(item['image'])))


def saverecommendationInfo(path, recommendationInfo):
    recommendationInfoPath = os.path.join(path, 'recommendationInfo')
    mkdir(recommendationInfoPath)
    recommendationInfotxtPath = os.path.join(recommendationInfoPath, 'recommendationInfo.txt')
    file = open(recommendationInfotxtPath, 'w+',encoding='utf-8')
    file.write(str(recommendationInfo))
    file.close()



    for item in recommendationInfo['items']:
        urllib.request.urlretrieve(item['image'], filename=os.path.join(recommendationInfoPath, getImageName(item['image'])))







def saveImage(path,imageLinks):
    for imageurl in imageLinks:
        print('saving image...')
        urllib.request.urlretrieve(imageurl, filename=os.path.join(path,getImageName(imageurl)))



def getImageName(url):
        urlHead = url.split('.jpg')[0]
        fileName = urlHead.split('/')[len(urlHead.split('/'))-1]
        # print(fileName)
        return fileName+'.jpg'







def main():
    url = 'https://www.farfetch.com/cn/shopping/women/clothing-1/items.aspx?page=1&view=90&sort=3&category=136497'
    url_split = url.split('page=1')
    for i in range(0, 7):
        url_fresh = url_split[0] + 'page=' + str(i + 1) + url_split[1]
        # print(url_fresh)
        loadContentPage(url_fresh,browser,i+1)

if __name__== '__main__':
    main()
    # browser.get('https://www.baidu.com')