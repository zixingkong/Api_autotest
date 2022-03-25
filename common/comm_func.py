# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     common
   Description :
   date：          2022/3/25
-------------------------------------------------
"""
import yaml
import os
from aiohttp import ClientSession
import aiofiles
from collections import UserDict


class BXMDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


class BXMList(list):
    pass


async def yaml_load(dir='', file=''):
    """
    异步读取yaml文件，并转义其中的特殊值
    :param file:
    :return:
    """
    if dir:
        file = os.path.join(dir, file)
    async with aiofiles.open(file, 'r', encoding='utf-8', errors='ignore') as f:
        data = await f.read()

    data = yaml.safe_load(data)
    return BXMDict(data)


async def http(*args, **kwargs):
    """
    http请求处理器
    :param domain: 服务地址
    :param args:
    :param kwargs:
    :return:
    """
    method, api = args
    arguments = kwargs.get('data') or kwargs.get('params') or kwargs.get('json') or {}
    url = 'https://httpbin.org'
    async with ClientSession() as session:
        async with session.request(method, url, **kwargs) as response:
            res = await response.text()
            return {
                'response': res,
                'url': url,
                'arguments': arguments
            }


async def one(session, case_dir='/Users/wyy/code/github/python/Api_autotest/testcase', case_name=''):
    """
    一份测试用例执行的全过程，包括读取.yml测试用例，执行http请求，返回请求结果
    所有操作都是异步非阻塞的
    :param session: session会话
    :param case_dir: 用例目录
    :param case_name: 用例名称
    :return:
    """
    test_data = await yaml_load(dir=case_dir, file=case_name)
    print(test_data)
    result = BXMDict({
        'case_dir': os.path.dirname(case_name),
        'api': test_data.args[1].replace('/', '_'),
    })
    if isinstance(test_data.kwargs, list):
        for index, each_data in enumerate(test_data.kwargs):
            step_name = each_data.pop('caseName')
            r = await http(*test_data.args, **each_data)
            r.update({'case_name': step_name})
            result.setdefault('responses', BXMList()).append({
                'response': r,
                'validator': test_data.validator[index]
            })
    else:
        step_name = test_data.kwargs.pop('caseName')
        r = await http(session, *test_data.args, **test_data.kwargs)
        r.update({'case_name': step_name})
        result.setdefault('responses', BXMList()).append({
            'response': r,
            'validator': test_data.validator
        })

    return result


async def entrace(test_cases, loop, semaphore=None):
    """
    http执行入口
    :param test_cases:
    :param semaphore:
    :return:
    """
    res = BXMDict()
    # 在CookieJar的update_cookies方法中，如果unsafe=False并且访问的是IP地址，客户端是不会更新cookie信息
    # 这就导致session不能正确处理登录态的问题
    # 所以这里使用的cookie_jar参数使用手动生成的CookieJar对象，并将其unsafe设置为True
    async with ClientSession(loop=loop) as session:
        if semaphore:
            async with semaphore:
                for test_case in test_cases:
                    data = await one(session, case_name=test_case)
                    res.setdefault(data.pop('case_dir'), BXMList()).append(data)
        else:
            for test_case in test_cases:
                data = await one(session, case_name=test_case)
                res.setdefault(data.pop('case_dir'), BXMList()).append(data)
        print(res)
        return res
