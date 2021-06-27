import requests
import lxml.etree
import os
import time


def gethtml(url, headers):
    resp = requests.get(url, headers=headers)
    return resp.content


def parsehtml(html):
    ids = []
    tree = lxml.etree.HTML(html)
    items = tree.xpath('//div[@class="c" and @id]')
    for i in items:
        ids.append(i.attrib['id'].split('_')[-1])
    return ids


def getpage(baseurl):
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.56',
               'cookie': '_T_WM=30861df37808c3c443275940766e7352;SUBP'
                         '=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFHKG0M1QDaWuLjJGbS'
                         '.GDY5NHD95QEeKnEeh5EeKB0Ws4DqcjGqcveBJvawBtt;SUB=_2A25NmyS6DeRhGeRP41AR8CzNzz'
                         '-IHXVvZEzyrDV6PUJbktANLRf8kW1NUBLi-x4mUnJAuvA_52KWuBiDMDwY84YT; SSOLoginState=1621054698; '
                         '_T_WL=1; _WEIBO_UID=2182002143'}
    resp = requests.get(baseurl, headers=headers)
    tree = lxml.etree.HTML(resp.content)
    input_ = tree.xpath('//*[@id="pagelist"]/form/div/input[1]')[0]
    page = int(input_.attrib['value'])
    return page


def getimageurl(url, headers):
    resp = requests.get(url, headers=headers)
    tree = lxml.etree.HTML(resp.content)
    items = tree.xpath('//div[@class="c"]')
    if len(items) > 2:
        urls = []
        for i in range(1, len(items) - 1):
            a = items[i].xpath('a[contains(text(),"原图")]')
            urls.append(a[0].attrib['href'])
        return urls
    else:
        print(f'{url}: picture not found')


def getandsaveimage(url, headers):
    resp = requests.get(url, headers=headers)
    imagename = url.split('?')[-1]
    pathname = os.path.join(basepath, f'{imagename}.jpg')
    if os.path.exists(pathname):
        print(f'image {pathname} 已存在')
    else:
        with open(pathname, 'wb') as f:
            f.write(resp.content)
            print(f'{url} saved')


def getallid(baseurl, headers, page):
    allid = []
    filename = os.path.join(basepath, 'all_id.txt')
    if os.path.exists(filename):
        print(f'{filename} 已存在，可直接使用')
        with open(filename) as f:
            for row in f:
                allid.append(row.strip())
    else:
        for i in range(1, page + 1):
            print(f'current allid counts: {len(allid)}, search ids in page {i}...')
            url = baseurl + f'?page={i}'
            html = gethtml(url, headers)
            ids = parsehtml(html)
            allid.extend(ids)
        with open(filename, 'w') as f:
            for i in allid:
                f.write(i + '\n')
    return allid


def getallimageurl(imageurl, headers, allid):
    allimageurl = []
    filename = os.path.join(basepath, 'all_image_url.txt')
    if os.path.exists(filename):
        print(f'{filename} 已存在，可直接使用')
        with open(filename) as f:
            for row in f:
                allimageurl.append(row.strip())
    else:
        for i in allid:
            urls = getimageurl(imageurl.format(i), headers)
            if urls is not None:
                allimageurl.extend(urls)
        with open(filename, 'w') as f:
            for i in allimageurl:
                f.write(i + '\n')
    return allimageurl


def main(user):
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.56',
               'cookie': '_T_WM=30861df37808c3c443275940766e7352;SUBP'
                         '=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFHKG0M1QDaWuLjJGbS'
                         '.GDY5NHD95QEeKnEeh5EeKB0Ws4DqcjGqcveBJvawBtt;SUB=_2A25NmyS6DeRhGeRP41AR8CzNzz'
                         '-IHXVvZEzyrDV6PUJbktANLRf8kW1NUBLi-x4mUnJAuvA_52KWuBiDMDwY84YT; SSOLoginState=1621054698; '
                         '_T_WL=1; _WEIBO_UID=2182002143'}
    baseurl = f'https://weibo.cn/{user}'
    page = getpage(baseurl)
    allid = getallid(baseurl, headers, page)
    imageurl = 'https://weibo.cn/mblog/picAll/{}'
    allimageurl = getallimageurl(imageurl, headers, allid)
    for i in reversed(allimageurl):
        getandsaveimage('https://weibo.cn' + i, headers)


if __name__ == '__main__':
    print('start time:', time.ctime())
    user = 'chyhuiying'
    name = '尘时柒'
    os.chdir('weibocrawlerimage')
    dirname = f'{user.replace("/", "_")}-{name}'
    try:
        os.mkdir(dirname)
    except FileExistsError:
        print(f'文件夹[{dirname}] 已存在')
    basepath = os.path.join(os.getcwd(), dirname)
    main(user)
    print('end time:', time.ctime())
