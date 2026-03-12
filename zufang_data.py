import requests#发送 HTTP 请求，获取网页内容
from pyquery import PyQuery as pq#PyQuery库（以pq别名引用）解析 HTML 内容，方便提取数据
from fake_useragent import UserAgent# 生成随机User-Agent（反爬
import time# 控制请求延迟（反爬）
import pandas as pd #数据处理与存储（DataFrame、CSV、数据库）
import random# 生成随机数（用于随机延迟）
import pymysql
from sqlalchemy import create_engine#pymysql和sqlalchemy库用于连接 MySQL 数据库，并将数据写入数据库表
# from datetime import datetime

# 初始化随机User-Agent生成器
UA = UserAgent()
headers = {
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Cookie': 'lianjia_uuid=6383a9ce-19b9-47af-82fb-e8ec386eb872; UM_distinctid=1777521dc541e1-09601796872657-53e3566-13c680-1777521dc5547a; _smt_uid=601dfc61.4fcfbc4b; _ga=GA1.2.894053512.1612577894; _jzqc=1; _jzqckmp=1; _gid=GA1.2.1480435812.1614959594; Hm_lvt_9152f8221cb6243a53c83b956842be8a=1614049202,1614959743; csrfSecret=lqKM3_19PiKkYOfJSv6ldr_c; activity_ke_com=undefined; ljisid=6383a9ce-19b9-47af-82fb-e8ec386eb872; select_nation=1; crosSdkDT2019DeviceId=-kkiavn-2dq4ie-j9ekagryvmo7rd3-qjvjm0hxo; Hm_lpvt_9152f8221cb6243a53c83b956842be8a=1615004691; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%221777521e37421a-0e1d8d530671de-53e3566-1296000-1777521e375321%22%2C%22%24device_id%22%3A%221777521e37421a-0e1d8d530671de-53e3566-1296000-1777521e375321%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fwww.baidu.com%2Flink%22%2C%22%24latest_referrer_host%22%3A%22www.baidu.com%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_utm_source%22%3A%22guanwang%22%2C%22%24latest_utm_medium%22%3A%22pinzhuan%22%2C%22%24latest_utm_campaign%22%3A%22wybeijing%22%2C%22%24latest_utm_content%22%3A%22biaotimiaoshu%22%2C%22%24latest_utm_term%22%3A%22biaoti%22%7D%7D; lianjia_ssid=7a179929-0f9a-40a4-9537-d1ddc5164864; _jzqa=1.3310829580005876700.1612577889.1615003848.1615013370.6; _jzqy=1.1612577889.1615013370.2.jzqsr=baidu|jzqct=%E9%93%BE%E5%AE%B6.jzqsr=baidu; select_city=440300; srcid=eyJ0Ijoie1wiZGF0YVwiOlwiZjdiNTI1Yjk4YjI3MGNhNjRjMGMzOWZkNDc4NjE4MWJkZjVjNTZiMWYxYTM4ZTJkNzMxN2I0Njc1MDEyY2FiOWMzNTIzZTE1ZjEyZTE3NjlkNTRkMTA2MWExZmIzMWM5YzQ3ZmQxM2M3NTM5YTQ1YzM5OWU0N2IyMmFjM2ZhZmExOGU3ZTc1YWU0NDQ4NTdjY2RiMjEwNTQyMDQzM2JiM2UxZDQwZWQwNzZjMWQ4OTRlMGRkNzdmYjExZDQwZTExNTg5NTFkODIxNWQzMzdmZTA4YmYyOTFhNWQ2OWQ1OWM4ZmFlNjc0OTQzYjA3NDBjNjNlNDYyNTZiOWNhZmM4ZDZlMDdhNzdlMTY1NmM0ZmM4ZGI4ZGNlZjg2OTE2MmU4M2MwYThhNTljMGNkODYxYjliNGYwNGM0NzJhNGM3MmVmZDUwMTJmNmEwZWMwZjBhMzBjNWE2OWFjNzEzMzM4M1wiLFwia2V5X2lkXCI6XCIxXCIsXCJzaWduXCI6XCJhYWEyMjhiNVwifSIsInIiOiJodHRwczovL20ubGlhbmppYS5jb20vY2h1enUvc3ovenVmYW5nL3BnJTdCJTdELyIsIm9zIjoid2ViIiwidiI6IjAuMSJ9',
    'Host': 'sz.lianjia.com',
    'Referer': 'https://sz.lianjia.com/zufang/', # 请求来源页面（防反爬）
    # 初始User-Agent（后续会被覆盖）
    # User-Agent（用户代理）是客户端在网络请求中发送给服务器的一个标识字段，
    # 用于告知服务器当前请求的客户端类型、版本、操作系统、设备环境等信息。它是 HTTP 协议中的一个重要组成部分
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
}

#爬虫类定义
class Lianjia_Crawer:

    def __init__(self, txt_path):
        super(Lianjia_Crawer, self).__init__()
        self.file = str(txt_path)# 存储CSV文件的路径
        self.df = pd.DataFrame(
            columns=['title', 'district', 'area', 'orient', 'floor', 'price', 'city'])

    def run(self):
        '''启动脚本'''
        connect_info = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(
            "root", "root", "localhost", "3306", "lagou")
        # 创建数据库引擎
        engine = create_engine(connect_info)
        for i in range(100):
            url = "https://sz.lianjia.com/zufang/pg{}/".format(str(i))
            # 解析单个页面
            self.parse_url(url)
            #每次解析后随机延迟（模拟人类浏览行为，避免 IP 封禁）
            time.sleep(random.randint(2, 5))
            print('正在爬取的 url 为 {}'.format(url))
        print('爬取完毕！！！！！！！！！！！！！！')
        # 保存到CSV文件
        self.df.to_csv(self.file, encoding='utf-8')
        print('租房信息已保存至本地')
        # 保存到MySQL数据库（数据追加，不覆盖已有数据）
        self.df.to_sql(name='house', con=engine,
                       if_exists='append', index=False)
        print('租房信息已保存数据库')

    # 页面解析方法
    def parse_url(self, url):
        # 更新为随机Chrome的User-Agent（反爬）
        headers['User-Agent'] = UA.random
        # 发送GET请求
        res = requests.get(url, headers=headers)
        # 声明pq对象,用pyquery解析HTML内容
        doc = pq(res.text)
        # 遍历每个房源条目
        for i in doc('.content__list--item .content__list--item--main'):
            try:
                pq_i = pq(i)# 解析单个房源的HTML
                # 房屋标题
                title = pq_i('.content__list--item--title a').text()
                # 具体信息, # 详情字段（格式："南山-科技园/50㎡/南/中楼层"）
                houseinfo = pq_i('.content__list--item--des').text()
                # 行政区,
                address = str(houseinfo).split('/')[0]
                # 取行政区主名称（
                district = str(address).split('-')[0]
                # 房屋面积#
                full_area = str(houseinfo).split('/')[1]
                # 去除单位“㎡”
                area = str(full_area)[:-1]
                # 朝向
                orient = str(houseinfo).split('/')[2]
                # 楼层
                floor = str(houseinfo).split('/')[-1]
                # 价格
                price = pq_i('.content__list--item-price').text()
                # 城市
                city = '深圳'
                data_dict = {'title': title, 'district': district, 'area': area,
                             'orient': orient, 'floor': floor, 'price': price, 'city': city}
                # 追加数据行
                self.df = self.df.append(data_dict, ignore_index=True)
                print([title, district, area, orient, floor, price, city])
            # 捕获解析异常（如字段缺失）
            except Exception as e:
                print(e)
                print("索引提取失败，请重试！！！！！！！！！！！！！")


if __name__ == "__main__":
    # 存储文件路径
    txt_path = "zufang_shenzhen.csv"
    # txt_path = "test.csv"
    # 创建爬虫实例
    Crawer = Lianjia_Crawer(txt_path)
    Crawer.run()  # 启动爬虫脚本
