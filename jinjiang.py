import urllib.request
from user_agent.base import generate_user_agent
import gzip
import re
import os, os.path
from bs4 import BeautifulSoup
from lxml.etree import HTML
import time
import random

def url_open(url):
    iplist = ['59.39.129.179:9000','163.125.22.169:9999','49.117.167.47:9999','116.52.65.217:9999','113.121.248.114:808','110.73.161.185:8123']
    # 有些代理不可用
    proxy = urllib.request.ProxyHandler({'https':random.choice(iplist)})
    opener = urllib.request.build_opener(proxy)
    urllib.request.install_opener(opener=opener)

    header = {'User-Agent': generate_user_agent()}
    req = urllib.request.Request(url=url, headers=header)
    # 如果IP失效，有三次重新尝试的机会
    try:
        response = urllib.request.urlopen(req).read()
    except:
        try:
            response = urllib.request.urlopen(req).read()
        except:
            response = urllib.request.urlopen(req).read()
    return response

# 传入参数：小说网站某一分类页面
# 函数返回：小说作者，书名，和小说的链接地址
def get_info(url):

    '''
    # 大多数网站都对支持gzip压缩的浏览器做了gzip的压缩，在python中可以通过gzip包处理gzip压缩过的网页”
    如果使用了代理，gzip 就会出错
    '''
    # 判断网页是否经过压缩处理
    try:
        response = url_open(url)
        response = gzip.decompress(response).decode('gbk','ignore')  # 解压缩内容并解码为“gbk”，'gb2312'&'utf-8'不行！
    except OSError as e:
        print(e)
        response = url_open(url).decode('gbk','ignore')
    soup = BeautifulSoup(response, "html.parser")

    authors = soup.find_all('a', href=re.compile("oneauthor\.php\?"), target='_blank')
    author = []
    for each in authors:
        author.append(each.string)

    titles = soup.find_all('a', href=re.compile("onebook\.php\?novel"), target="_blank")
    title = []
    for each in titles:
        title.append(each.string)

    links = soup.find_all('a', href=re.compile("onebook\.php\?novel"), target="_blank")
    link = []
    for each in links:
        link.append("http://www.jjwxc.net/" + each.get('href'))
    # print(author,'\n',title,'\n',link,'\n',len(author),'\n',len(title),'\n',len(link))
    return author, title, link

# 按顺序依次获得一页的所有章节链接
# 传入参数：某本小说的链接地址
# 函数返回：章节名字 跟 链接
def get_chapter(link):
    # 判断网页是否采用了gzip压缩格式
    try:
        response = url_open(link)
        response = gzip.decompress(response).decode('gbk','ignore')
    except OSError as e:
        print(e)
        response = url_open(link).decode('gbk','ignore')

    soup = BeautifulSoup(response,'html.parser')
    chapter_link = []
    chapter_title = []
    chapters = soup.find_all('a', itemprop="url", href=re.compile("chapterid="))
    for each in chapters:
        chapter_link.append(each.get('href'))
        chapter_title.append(each.string)
    #print(chapter_title,'\n',chapter_link, '\n', len(chapter_title), '\n', len(chapter_link))
    return chapter_title, chapter_link

# 函数描述：获取一个章节的内容
# 传入参数：某一个章节的链接地址
# 函数返回：一个章节的内容
def get_content(url):
    try:
        html = url_open(url)
        response = gzip.decompress(html).decode('gbk','ignore')  # 解压缩内容并解码为“gbk”，'gb2312'&'utf-8'不行！
    except OSError as e:
        print(e)
        response = url_open(url).decode('gbk','ignore')
    html = HTML(response)
    content = html.xpath('//div[@class="noveltext"]/text()')
    #print(Content)
    return content

# 函数描述：保存一个章节的内容
# 传入参数：小说名，章节名，章节内容
def save_novel(novelname, author, chapter_title, chapter_content, folder="晋江小说"):
    if not os.path.exists(folder):
        os.mkdir(folder)
    else:
        pass
    novelname = novelname
    content = chapter_content
    with open(folder+'/'+novelname+'.txt','a+') as f:
        try:
            #f.write("\t\t\t"+novelname+ '-----' + author + '\r\n')
            f.write(chapter_title)
            for eachline in content:
                eachline = eachline.replace('\u3000','')
                eachline = eachline.replace('\u2022','')
                f.writelines(eachline+'\n')
        except:
            pass

# 函数描述：保存单本小说
# 传入参数：小说名，小说地址
def main(novelname, author, novel_url, ):
    chapter_title, chapter_link = get_chapter(novel_url)  # 获取所有章节的名字跟地址
    chapter_zip = list(zip(chapter_title, chapter_link))    #

    for each in chapter_zip:
        chapter_content = get_content(each[1])     # 获取一个章节的内容
        print("正在下载：%s --> %s" % (novelname, each[0]))
        save_novel(novelname=novelname, author=author, chapter_title=each[0], chapter_content=chapter_content)

if __name__=="__main__":
    # 翻页   如果用多个线程的话应该会快蛮多。
    for page in range(1,1000):
        print("第%d页----->"%page)
        url = "http://www.jjwxc.net/bookbase_slave.php?booktype=free&opt=&page={page}&orderstr=4&endstr=true".format(page=page)
        # 获得分类页的小说信息：作者，小说名，小说地址
        novel_authors, novel_names, novel_links = get_info(url)
        # 将小说对应信息整理
        novel_zip = list(zip(novel_names, novel_authors, novel_links))
        for novel in novel_zip:
            print("这是第 %d 本小说" %(novel_zip.index(novel)+1))
            print("\n---------------- %s -----------------\n" % novel[0])
            main(novelname=novel[0],author=novel[1],novel_url=novel[2])
            print("---------------- %s -----------------\n" % novel[0])
            #time.sleep(1)       # 每隔三秒下载一本电子书


