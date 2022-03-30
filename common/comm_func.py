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
import re

config_dir = os.path.join('./', "config")


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
    # 匹配函数调用形式的语法
    pattern_function = re.compile(r'^\${([A-Za-z_]+\w*\(.*\))}$')
    pattern_function2 = re.compile(r'^\${(.*)}$')
    # 匹配取默认值的语法
    pattern_function3 = re.compile(r'^\$\((.*)\)$')

    def my_iter(data):
        """
        递归测试用例，根据不同数据类型做相应处理，将模板语法转化为正常值
        :param data:
        :return:
        """
        if isinstance(data, (list, tuple)):
            for index, _data in enumerate(data):
                data[index] = my_iter(_data) or _data
        elif isinstance(data, dict):
            for k, v in data.items():
                data[k] = my_iter(v) or v
        elif isinstance(data, (str, bytes)):
            # m = pattern_function.match(data)
            # if not m:
            #     m = pattern_function2.match(data)
            # if m:
            #     return eval(m.group(1))
            # if not m:
            #     m = pattern_function3.match(data)
            # if m:
            #     K, k = m.group(1).split(':')
            #     return BXMDict.default_values.get(K).get(k)

            return data

    my_iter(data)
    return BXMDict(data)


async def http(domain, *args, **kwargs):
    """
    http请求处理器
    :param domain: 服务地址
    :param args:
    :param kwargs:
    :return:
    """
    method, api = args
    arguments = kwargs.get('data') or kwargs.get('params') or kwargs.get('json') or {}
    # kwargs中加入token
    # kwargs.setdefault('headers', {}).update({'token': bxmat.token})

    url = ''.join([domain, api])
    async with ClientSession() as session:
        async with session.request(method, url, **kwargs) as response:
            res = await response.text()
            return {
                'response': res,
                'url': url,
                'arguments': arguments
            }


async def one(session, case_name=''):
    """
    一份测试用例执行的全过程，包括读取.yml测试用例，执行http请求，返回请求结果
    所有操作都是异步非阻塞的
    :param session: session会话
    :param case_dir: 用例目录
    :param case_name: 用例名称
    :return:
    """
    # project_name = case_name.split(os.sep)[1]
    url_data = await yaml_load('./config', 'url.yaml')
    domain = url_data['host']
    print(case_name)
    case_dir = os.path.dirname(case_name)
    test_data = await yaml_load(dir=case_dir, file=case_name)
    result = BXMDict({
        'case_name': case_name,
        'api': test_data.args[1].replace('/', '_'),
    })
    if isinstance(test_data.kwargs, list):
        for index, each_data in enumerate(test_data.kwargs):
            step_name = each_data.pop('caseName')
            r = await http(domain, *test_data.args, **each_data)
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
                    res.setdefault(data.pop('case_name'), BXMList()).append(data)
        else:
            for test_case in test_cases:
                data = await one(session, case_name=test_case)
                res.setdefault(data.pop('case_name'), BXMList()).append(data)
        return res
