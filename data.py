import random
import requests#发送 HTTP 请求，获取网页内容
import math#计算总页数
import time
import pandas as pd
import pymysql
from sqlalchemy import create_engine
from fake_useragent import UserAgent# 生成随机User-Agent（反爬

# 获取页面 JSON 数据，构造请求头和请求体，通过 Session 保持 Cookie，模拟浏览器行为获取拉勾网职位数据（JSON 格式）
def get_json(url, num):
    url_search = 'https://www.lagou.com/jobs/list_python/p-city_0?&cl=false&fromSearch=true&labelWords=&suginput='
    # 初始化随机User-Agent生成器
    UA = UserAgent()
    headers = {
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        'User-Agent': UA.random,
        'Host': 'www.lagou.com',
        # 请求来源页面（防反爬）
        'Referer': 'https://www.lagou.com/jobs/list_%E6%95%B0%E6%8D%AE%E5%88%86%E6%9E%90?labelWords=&fromSearch=true&suginput=',
        # 标识请求为 Ajax 异步请求，符合拉勾网数据接口的调用规范，减少被反爬系统误判的可能
        'X-Requested-With': 'XMLHttpRequest',
         'Cookie':'user_trace_token=20210218203227-35e936a1-f40f-410d-8400-b87f9fb4be0f; _ga=GA1.2.331665492.1613651550; LGUID=20210218203230-39948353-de3f-4545-aa01-43d147708c69; LG_HAS_LOGIN=1; hasDeliver=0; privacyPolicyPopup=false; showExpriedIndex=1; showExpriedCompanyHome=1; showExpriedMyPublish=1; RECOMMEND_TIP=true; index_location_city=%E5%85%A8%E5%9B%BD; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1613651550,1613652253,1613806244,1614497914; _putrc=52ABCFBE36E5D0BD123F89F2B170EADC; gate_login_token=ea312e017beac7fe72547a32956420b07d6d5b1816bc766035dd0f325ba92b91; JSESSIONID=ABAAAECAAEBABII8D8278DB16CB050FD656DD1816247B43; login=true; unick=%E7%94%A8%E6%88%B72933; WEBTJ-ID=20210228%E4%B8%8B%E5%8D%883:38:37153837-177e7932b7f618-05a12d1b3d5e8c-53e356a-1296000-177e7932b8071; sensorsdata2015session=%7B%7D; _gid=GA1.2.1359196614.1614497918; __lg_stoken__=bb184dd5d959320e9e61d943e802ac98a8538d44699751621e807e93fe0ffea4c1a57e923c71c93a13c90e5abda7a51873c2e488a4b9d76e67e0533fe9e14020734016c0dcf2; X_MIDDLE_TOKEN=90b85c3630b92280c3ad7a96c881482e; LGSID=20210228161834-659d6267-94a3-4a5c-9857-aaea0d5ae2ed; TG-TRACK-CODE=index_navigation; SEARCH_ID=092c1fd19be24d7cafb501684c482047; X_HTTP_TOKEN=fdb10b04b25b767756070541617f658231fd72d78b; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2220600756%22%2C%22first_id%22%3A%22177b521c02a552-08c4a0f886d188-73e356b-1296000-177b521c02b467%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24os%22%3A%22Linux%22%2C%22%24browser%22%3A%22Chrome%22%2C%22%24browser_version%22%3A%2288.0.4324.190%22%2C%22lagou_company_id%22%3A%22%22%7D%2C%22%24device_id%22%3A%22177b521c02a552-08c4a0f886d188-73e356b-1296000-177b521c02b467%22%7D; _gat=1; Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1614507066; LGRID=20210228181106-f2d71d85-74fe-4b43-b87e-d78a33c872ad',
        # 'Cookie':'user_trace_token=20250416181329-0209aabc-d673-4d7d-9fc8-9917f5caba4f; _ga=GA1.2.87972330.1744798411; LGUID=20250416181331-8d03b418-582f-493a-b857-2b3b20255dca; __lg_stoken__=5019782f7be21973b6d1c6d5a41e11fe4766cff3dfbca8ff94a4a843e17fc76ee8ecee6349e35f654d8c4fccb58ce1f4560d8fd70c8b6228aa32265629e0cfb16b0599be0174; sensorsdata2015session=%7B%7D; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1744798411,1745996956,1746435671; HMACCOUNT=B14BC5A6CE70D3CB; _gid=GA1.2.359980972.1746435671; PRE_UTM=; PRE_HOST=; PRE_LAND=https%3A%2F%2Fwww.lagou.com%2Fjobs%2Flist%5F%25E6%2595%25B0%25E6%258D%25AE%25E5%2588%2586%25E6%259E%2590%3FlabelWords%3D%26fromSearch%3Dtrue%26suginput%3D; LGSID=20250505170111-3577279d-3361-4bf3-92e0-46da62feea04; PRE_SITE=https%3A%2F%2Fwww.lagou.com%2Fcommon-sec%2Fsecurity-check.html%3Fseed%3DD2B46291AB0E2730976B0603186455404A34E590B3C151673FDB673094E8DDFC96E3835150F61E2ED0D57339356CF4D0%26ts%3D17464356705593%26name%3D5019782f7be2%26callbackUrl%3Dhttps%253A%252F%252Fwww.lagou.com%252Fjobs%252Flist%5F%2525E6%252595%2525B0%2525E6%25258D%2525AE%2525E5%252588%252586%2525E6%25259E%252590%253FlabelWords%253D%2526fromSearch%253Dtrue%2526suginput%253D%26srcReferer%3D; X_MIDDLE_TOKEN=f23a739914e94640600c1efd6973e521; _gat=1; sm_auth_id=nerxis7rs7eoji78; gate_login_token=v1####cbfc0c194ec38a7458ed7b556042afc68a5ab854d98d129bd04dbc592752621f; LG_LOGIN_USER_ID=v1####22118c7acaec6c791b77c83958d171ec0bf93256e2fea40626cb2403f95a9283; LG_HAS_LOGIN=1; _putrc=77C8FF424E3D54F0123F89F2B170EADC; login=true; unick=%E7%94%A8%E6%88%B70517; privacyPolicyPopup=false; X_HTTP_TOKEN=f2f6a3232d5d2f5e38963464713195922ca3fd379d; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2227684037%22%2C%22%24device_id%22%3A%221963e16ea6319d-08cc9c18e731a5-26011c51-921600-1963e16ea648fa%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24os%22%3A%22Windows%22%2C%22%24browser%22%3A%22Chrome%22%2C%22%24browser_version%22%3A%22135.0.0.0%22%2C%22lagou_company_id%22%3A%22%22%7D%2C%22first_id%22%3A%221963e16ea6319d-08cc9c18e731a5-26011c51-921600-1963e16ea648fa%22%7D; Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1746436983; _ga_DDLTLJDLHH=GS1.2.1746435673.3.1.1746436983.60.0.0',
        'Origin': 'https://www.lagou.com',
    }
    # 请求体（页码、搜索关键词）
    data = {
        'first': 'true',#首次请求标识
        'pn': num,#页码
        'kd': 'python'}#搜索关键词
    #创建Session保持Cookie
    s = requests.Session()
    print('建立session：', s, '\n\n')
    # 首次请求获取Cookie，get函数是向指定的 URL 发送 HTTP GET 请求。在 HTTP 协议中，GET 请求通常用于从服务器获取资源
    # timeout=3用于设置请求的超时时间， 3 秒内若未得到服务器响应，就会触发超时异常
    s.get(url=url_search, headers=headers, timeout=3)
    # 提取并复用Cookie
    cookie = s.cookies
    print('获取cookie：', cookie, '\n\n')
    res = requests.post(url, headers=headers, data=data, cookies=cookie, timeout=3)
    #捕获4xx/5xx错误，如反爬封禁返回的错误状态码
    res.raise_for_status()
    res.encoding = 'utf-8'
    page_data = res.json()
    print('请求响应结果：', page_data, '\n\n')
    # 返回JSON格式的页面数据
    return page_data

# 计算总页数，通过在拉勾网输入关键字信息，可以发现最多显示30页信息,每页最多显示15个职位信息
def get_page_num(count):
    # 总职位数÷每页15条，向下取整
    page_num = math.ceil(count / 15)
    # 拉勾网最多显示30页
    if page_num > 29:
        return 29
    else:
        return page_num

# 提取职位详情,从 JSON 数据中提取 15 个职位字段，整理为二维列表，便于后续存储
def get_page_info(jobs_list):
    page_info_list = []
    for i in jobs_list:  # 循环每一页所有职位信息
        job_info = []
        job_info.append(i['companyFullName'])
        job_info.append(i['companyShortName'])
        job_info.append(i['companySize'])
        job_info.append(i['financeStage'])
        job_info.append(i['district'])
        job_info.append(i['positionName'])
        job_info.append(i['workYear'])
        job_info.append(i['education'])
        job_info.append(i['salary'])
        job_info.append(i['positionAdvantage'])
        job_info.append(i['industryField'])
        job_info.append(i['firstType'])
        #列表中的所有字符串连接成一个大字符串
        job_info.append(",".join(i['companyLabelList']))
        job_info.append(i['secondType'])
        job_info.append(i['city'])
        page_info_list.append(job_info)
    return page_info_list

# 数据去重
def unique(old_list):
    newList = []
    for x in old_list:
        if x not in newList :
            newList.append(x)
    return newList

def main():
    # 数据库连接信息
    connect_info = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format("root", "root", "localhost", "3306",
                                                                        "lagou")
    # 创建数据库引擎
    engine = create_engine(connect_info)
    url = ' https://www.lagou.com/jobs/positionAjax.json?needAddtionalResult=false'
    # 获取第一页数据
    first_page = get_json(url, 1)
    # 总职位数，content里面的positionResult里面的totalCount
    total_page_count = first_page['content']['positionResult']['totalCount']
    # 计算总页数
    num = get_page_num(total_page_count)
    total_info = []
    time.sleep(10)
    for page in range(1, num + 1):
        # 获取每一页的职位相关的信息
        page_data = get_json(url,page)  # 获取响应json
        jobs_list = page_data['content']['positionResult']['result']  # 获取每页的所有python相关的职位信息
        page_info = get_page_info(jobs_list)
        total_info += page_info
        print('已经爬取到第{}页，职位总数为{}'.format(num, len(total_info)))
        time.sleep(random.uniform(15,25))
    #数据去重并转换为DataFrame，字段与提取顺序一致
    df = pd.DataFrame(data=unique(total_info),
                      columns=['companyFullName', 'companyShortName', 'companySize', 'financeStage',
                               'district', 'positionName', 'workYear', 'education',
                               'salary', 'positionAdvantage', 'industryField',
                               'firstType', 'companyLabelList', 'secondType', 'city'])
    df.to_csv('python.csv', index=True)
    print('职位信息已保存本地')
    df.to_sql(name='demo', con=engine, if_exists='append', index=False)
    print('职位信息已保存数据库')

if __name__ == '__main__':
    main()