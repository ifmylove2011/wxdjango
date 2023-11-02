import json
import logging
import random
import time

from django.http import JsonResponse
from django.shortcuts import render
from wxcloudrun.models import Counters
from bs4 import BeautifulSoup
from urllib import request
import lxml

logger = logging.getLogger('log')
head = {
    'Connection': 'keep-alive',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 QIHU 360EE'}

url_dujitang = "http://8zt.cc/api/"
url_fuzhizhantie = "https://cp.azite.cn/api/articles?sort=random&pp=1"
url_xuejieba = "https://xuejie8.cc/tag/meizitu"

'''
{
  "ToUserName": "gh_919b00572d95", // 小程序/公众号的原始ID，资源复用配置多个时可以区别消息是给谁的
  "FromUserName": "oVneZ57wJnV-ObtCiGv26PRrOz2g", // 该小程序/公众号的用户身份openid
  "CreateTime": 1651049934, // 消息时间
  "MsgType": "text", // 消息类型
  "Content": "回复文本", // 消息内容
  "MsgId": 23637352235060880 // 唯一消息ID，可能发送多个重复消息，需要注意用此ID去重
}
'''


def dujitang():
    req = request.Request(url_dujitang, headers=head)
    responese = request.urlopen(req)
    html = responese.read().decode('utf-8')
    soup = BeautifulSoup(html, 'lxml')
    body = json.loads(soup.p.string)
    dujitang_content = body['content']
    return dujitang_content


def fuzhizhantie():
    req = request.Request(url_fuzhizhantie, headers=head)
    responese = request.urlopen(req)
    html = responese.read().decode('utf-8')
    body = json.loads(html)
    return body[0]['text']


def xuejieba():
    req = request.Request(url_xuejieba, headers=head)
    responese = request.urlopen(req)
    html = responese.read().decode('utf-8')
    # print(html)
    soup = BeautifulSoup(html, 'lxml')
    tags_li = soup.find_all(class_="post-list-item item-post-style-1")
    url_xuejieba_detail = tags_li[random.randint(0, len(tags_li))].h2.a
    print(url_xuejieba_detail.string)
    print(url_xuejieba_detail.attrs['href'])
    time.sleep(1)
    req = request.Request(url_xuejieba_detail.attrs['href'], headers=head)
    responese = request.urlopen(req)
    html = responese.read().decode('utf-8')
    # print(html)
    soup = BeautifulSoup(html, 'lxml')
    tag_preview = soup.find(class_='entry-content')
    tags_img = tag_preview.find_all('img')
    print(tags_img[0].attrs['data-src'])
    return url_xuejieba_detail.string, url_xuejieba_detail.attrs['href'], tags_img[0].attrs['data-src']
    # for tag_img in tags_img:
    #     print(tags_img)


def sese(user_id, developer_id, create_time, msg_type):
    detail = xuejieba()
    rsp = JsonResponse(
        {'ToUserName': user_id, 'FromUserName': developer_id, 'CreateTime': create_time, 'MsgType': msg_type,
         'ArticleCount': 1, 'Articles': [
            {
                "Title": detail[0],
                "Description": detail[0],
                "PicUrl": detail[2],
                "Url": detail[1]
            }
        ]}, json_dumps_params={'ensure_ascii': False})
    return rsp


def receive_wx(request_wx, _):
    if request_wx.method == 'GET' or request_wx.method == 'get':
        rsp = JsonResponse({'code': -1, 'errorMsg': '请求方式错误'},
                           json_dumps_params={'ensure_ascii': False})
        logger.info('response result: {}'.format(rsp.content.decode('utf-8')))
        return rsp

    logger.info('receive wx req: {}'.format(request_wx.body))
    body_unicode = request_wx.body.decode('utf-8')
    body = json.loads(body_unicode)

    if 'action' in body and body['action'] == 'CheckContainerPath':
        rsp = JsonResponse({}, json_dumps_params={'ensure_ascii': False})
        logger.info(rsp)
        return rsp

    developer_id = body['ToUserName']
    user_id = body['FromUserName']
    create_time = int(time.time())
    msg_type = body['MsgType']
    msg_id = body['MsgId']
    rsp = JsonResponse({'code': 0, 'errorMsg': ''}, json_dumps_params={'ensure_ascii': False})

    if msg_type == 'text':
        msg = body['Content']
        if msg == '毒鸡汤':
            content = dujitang()
            rsp = JsonResponse(
                {'ToUserName': user_id, 'FromUserName': developer_id, 'CreateTime': create_time, 'MsgType': msg_type,
                 'Content': content}, json_dumps_params={'ensure_ascii': False})
        elif msg == '复读机':
            content = fuzhizhantie()
            rsp = JsonResponse(
                {'ToUserName': user_id, 'FromUserName': developer_id, 'CreateTime': create_time, 'MsgType': msg_type,
                 'Content': content}, json_dumps_params={'ensure_ascii': False})
        elif msg == '今日涩涩':
            rsp = sese(user_id, developer_id, create_time, 'news')

        logger.info('response result: {}'.format(rsp.content.decode('utf-8')))
        return rsp

    rsp = JsonResponse({'code': 0, 'errorMsg': ''}, json_dumps_params={'ensure_ascii': False})
    return rsp


def req_content(content_type):
    if content_type == '毒鸡汤':
        return dujitang()
    elif content_type == '复读机':
        return fuzhizhantie()
    else:
        return '大家都是芳芳的'


def index(request, _):
    """
    获取主页

     `` request `` 请求对象
    """

    return render(request, 'index.html')


def counter(request, _):
    """
    获取当前计数

     `` request `` 请求对象
    """

    rsp = JsonResponse({'code': 0, 'errorMsg': ''}, json_dumps_params={'ensure_ascii': False})
    if request.method == 'GET' or request.method == 'get':
        rsp = get_count()
    elif request.method == 'POST' or request.method == 'post':
        rsp = update_count(request)
    else:
        rsp = JsonResponse({'code': -1, 'errorMsg': '请求方式错误'},
                           json_dumps_params={'ensure_ascii': False})
    logger.info('response result: {}'.format(rsp.content.decode('utf-8')))
    return rsp


def get_count():
    """
    获取当前计数
    """

    try:
        data = Counters.objects.get(id=1)
    except Counters.DoesNotExist:
        return JsonResponse({'code': 0, 'data': 0},
                            json_dumps_params={'ensure_ascii': False})
    return JsonResponse({'code': 0, 'data': data.count},
                        json_dumps_params={'ensure_ascii': False})


def update_count(request):
    """
    更新计数，自增或者清零

    `` request `` 请求对象
    """

    logger.info('update_count req: {}'.format(request.body))

    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    if 'action' not in body:
        return JsonResponse({'code': -1, 'errorMsg': '缺少action参数'},
                            json_dumps_params={'ensure_ascii': False})

    if body['action'] == 'inc':
        try:
            data = Counters.objects.get(id=1)
        except Counters.DoesNotExist:
            data = Counters()
        data.id = 1
        data.count += 1
        data.save()
        return JsonResponse({'code': 0, "data": data.count},
                            json_dumps_params={'ensure_ascii': False})
    elif body['action'] == 'clear':
        try:
            data = Counters.objects.get(id=1)
            data.delete()
        except Counters.DoesNotExist:
            logger.info('record not exist')
        return JsonResponse({'code': 0, 'data': 0},
                            json_dumps_params={'ensure_ascii': False})
    else:
        return JsonResponse({'code': -1, 'errorMsg': 'action参数错误'},
                            json_dumps_params={'ensure_ascii': False})
