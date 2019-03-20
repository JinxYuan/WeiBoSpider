# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
import json
from ..items import *


class WeibocnSpider(scrapy.Spider):
    name = 'weibocn'
    allowed_domains = ['m.weibo.cn']
    user_url = 'https://m.weibo.cn/api/container/getIndex?uid={uid}&type=uid&value={uid}&containerid=100505{uid}'
    follow_url = 'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_followers_-_{uid}&page={page}'
    fan_url = 'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_{uid}&page={page}'
    weibo_url = 'https://m.weibo.cn/api/container/getIndex?uid={uid}&type=uid&page={page}&containerid=107603{uid}'
    start_users = ['1783286485', '1195242865', '1644461042', '1663363857']

    def start_requests(self):
        for uid in self.start_users:
            yield Request(self.user_url.format(uid=uid), callback=self.parse_user)

    def parse_user(self, response):
        """用户信息"""
        # self.logger.debug(response)
        result = json.loads(response.text)
        if result.get('data').get('userInfo'):
            user_info = result.get('data').get('userInfo')
            user_item = UserItem()
            field_map = {
                'id': 'id', 'name': 'screen_name', 'avatar': 'profile_image_url', 'cover': 'cover_image_phone',
                'gender': 'gender', 'description': 'description', 'fans_count': 'followers_count',
                'follows_count': 'follow_count', 'weibos_count': '', 'verified': 'verified',
                'verified_reason': 'verified_reason', 'verified_type': 'verified_type'
            }
            for field, attr in field_map.items():
                user_item[field] = user_info.get(attr)
            yield user_item
            uid = user_info.get('id')
            # 关注请求
            yield Request(self.follow_url.format(uid=uid, page=1), callback=self.parse_follows, meta={'page': 1,
                                                                                                      'uid': uid})
            # 粉丝请求
            yield Request(self.fan_url.format(uid=uid, page=1), callback=self.parse_fans, meta={'page': 1, 'uid': uid})
            # 微博请求
            yield Request(self.weibo_url.format(uid=uid, page=1), callback=self.parse_weibos, meta={'page': 1,
                                                                                                    'uid': uid})

    def parse_follows(self, response):
        """关注"""
        result = json.loads(response.text)
        if result.get('ok') and result.get('data').get('cards') and len(result.get('data').get('cards'))\
                and result.get('data').get('cards')[-1].get('card_group'):
            follows = result.get('data').get('cards')[-1].get('card_group')
            for follow in follows:
                if follow.get('user'):
                    uid = follow.get('user').get('id')
                    yield Request(self.user_url.format(uid=uid), callback=self.parse_user)
            uid = response.meta.get('uid')
            user_relation_item = UserRelationItem()
            follows = [{'id': follow.get('user').get('id'), 'name': follow.get('user').get('screen_name')}
                       for follow in follows]
            user_relation_item['id'] = uid
            user_relation_item['follows'] = follows
            user_relation_item['fans'] = []
            yield user_relation_item
            # 下一页
            page = response.meta.get('page') + 1
            yield Request(self.follow_url.format(uid=uid, page=page), callback=self.parse_follows,
                          meta={'page': page, 'uid': uid})

    def parse_fans(self, response):
        result = json.loads(response.text)
        if result.get('ok') and result.get('data').get('cards') and len(result.get('data').get('cards'))\
                and result.get('data').get('cards')[-1].get('card_group'):
            fans = result.get('data').get('cards')[-1].get('card_group')
            for fan in fans:
                if fan.get('user'):
                    uid = fan.get('user').get('id')
                    yield Request(self.user_url.format(uid=uid), callback=self.parse_user)
            uid = response.meta.get('uid')
            user_relation_item = UserRelationItem()
            fans = [{'id': fan.get('user').get('id'), 'name': fan.get('user').get('screen_name')} for fan in fans]
            user_relation_item['id'] = uid
            user_relation_item['fans'] = fans
            user_relation_item['follows'] = []
            yield user_relation_item
            # 下一页
            page = response.meta.get('page') + 1
            yield Request(self.fan_url.format(uid=uid, page=page), callback=self.parse_fans,
                          meta={'uid': uid, 'page': page})

    def parse_weibos(self, response):
        result = json.loads(response.text)
        if result.get('ok') and result.get('data').get('cards'):
            weibos = result.get('data').get('cards')
            for weibo in weibos:
                mblog = weibo.get('mblog')
                if mblog:
                    weibo_item = WeiboItem()
                    field_map = {'id': 'id', 'attitudes_count': 'attitudes_count', 'comments_count': 'comments_count',
                                 'reposts_count': 'reposts_count', 'picture': 'original_pic', 'pictures': 'pics',
                                 'source': 'source', 'text': 'text', 'raw_text': 'raw_text',
                                 'thumbnail': 'thumbnail_pic'}
                    for field, attr in field_map.items():
                        weibo_item[field] = mblog.get(attr)
                        weibo_item['user'] = response.meta.get('uid')
                        yield weibo_item
                    # 下一页
                    uid = response.meta.get('uid')
                    page = response.meta.get('page') + 1
                    yield Request(self.weibo_url.format(uid=uid, page=page), callback=self.parse_weibos,
                                  meta={'uid': uid, 'page': page})

    def parse(self, response):
        pass
