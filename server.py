from flask.json import JSONEncoder as _JSONEncoder
import jieba
import jieba.analyse
import numpy as np
from flask import Flask, request, jsonify,session
import pymysql
from flask_cors import *
import pandas as pd
from collections import Counter
import pickle

app = Flask(__name__, static_url_path='')#静态文件的访问路径为空，意味着可以直接通过根路径访问静态文件
app.config['JSON_AS_ASCII'] = False#Flask 在返回 JSON 数据时会以非 ASCII 编码的形式输出，避免中文等非 ASCII 字符被转义
CORS(app, supports_credentials=True)
app.secret_key = 'your_secret_key'  # 用于会话管理的密钥

# JSON 编码器 JSONEncoder，它继承自 _JSONEncoder。default 方法用于处理特殊类型的对象转换为 JSON 格式。
# 当遇到 decimal.Decimal 类型的对象时，将其转换为 float 类型。最后调用父类的 default 方法处理其他类型的对象。
class JSONEncoder(_JSONEncoder):
    def default(self, o):
        import decimal
        if isinstance(o, decimal.Decimal):
            return float(o)
        super(JSONEncoder, self).default(o)

#这行代码将自定义的 JSON 编码器 JSONEncoder 应用到 Flask 应用中，使得 Flask 在返回 JSON 数据时使用自定义的编码器。
app.json_encoder = JSONEncoder


# 视图函数，使用 @app.route('/') 装饰器将根路径 / 映射到该函数。当用户访问根路径时，函数会返回 index.html 静态文件到客户端
@app.route('/')
def index():
    return app.send_static_file("index.html")


#学历+工作经验
@app.route('/xueli', methods=['GET'])
def xueli():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor用于执行sql语句
    cursor = conn.cursor()
    # 执行sql语句，获取 demo 表中不同的学历情况，并将结果存储在 result 中，DISTINCT 关键字的作用是去除重复值
    cursor.execute("SELECT DISTINCT(education) from demo")
    # 获取所有记录列表
    result = cursor.fetchall()#将上一步执行 SQL 查询后得到的所有结果以元组的形式返回
    education = []#创建一个空的列表 education，后续会将从数据库中查询到的不同学历值添加到这个列表里
    education_data = []#存储每种学历对应的统计数据
    color_list = ['#459AF0', '#38C3B0', '#86CA5A', '#BFD44F', '#90EE90']
    # 获取到学历的五种情况：不限、大专、本科、硕士、博士,遍历 result，将学历信息添加到 education 列表中
    for field in result:
        #由于前面的查询语句 SELECT DISTINCT(education) from demo 返回的结果集中每个元组只有一个元素（即学历值），
        # 所以 field[0] 就是具体的学历值。这行代码将这个学历值添加到 education 列表中。
        # 这样，循环结束后，education 列表就包含了从数据库中查询到的所有不同的学历值
        education.append(field[0])
    # 获取到每种学历对应的个数
    #此处不仅需要学历值（education[i]），还需要根据索引获取颜色值（color_list[i]），索引是关联两个列表的桥梁
    #假设 color_list 的第 i 个颜色必须对应 education 的第 i 个学历，索引遍历确保顺序正确，此时必须使用索引遍历，才能同时操作两个列表
    for i in range(len(education)):
        cursor.execute(
            #count(*) 是一个聚合函数，它会统计符合查询条件的记录行数。* 表示统计所有列，简单来说，count(*) 会返回满足条件的记录总数。
            #只选择 education 字段的值等于 education[i] 的记录。从 education 列表中取出的第 i 个元素，也就是一个具体的学历值。
            #这里通过字符串拼接的方式将这个变量的值嵌入到 SQL 语句中。
            "SELECT count(*) from demo where education = '" + education[i] + "'")
        count = cursor.fetchall()
        education_data.append(
            #education_data 列表中的每个元素都是一个字典，包含了学历数量和颜色样式信息
            {'value': count[0][0], 'itemStyle': {'color': color_list[i]}})
    cursor.execute("SELECT DISTINCT(workYear) from demo")
    result = cursor.fetchall()
    workYear = []
    workYear_data = []
    # 获取到的几种工作经验
    for field in result:
        workYear.append(field[0])
    # 获取到每种工作经验对应的个数
    for i in workYear:
        cursor.execute(
            "SELECT count(*) from demo where workYear = '" + i + "'")
        count = cursor.fetchall()
        workYear_data.append({'value': count[0][0], 'name': i})
        #关闭游标并使用 jsonify 函数将结果以 JSON 格式返回
    cursor.close()
    return jsonify({"education": education, "education_data": education_data, "workYear_data": workYear_data})


#这个视图函数与 /xueli 视图函数类似，不同之处在于它只查询城市为北京、上海、广州、深圳(一线城市）的数据
@app.route('/xueli_first', methods=['GET'])
def xueli_first():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor
    cursor = conn.cursor()
    # 执行sql语句
    cursor.execute(
        "SELECT DISTINCT(education) from demo where city in ('北京', '上海', '广州', '深圳');")
    # 获取所有记录列表
    result = cursor.fetchall()
    education = []
    education_data = []
    color_list = ['#459AF0', '#38C3B0', '#86CA5A', '#BFD44F', '#90EE90']
    # 获取到学历的五种情况：不限、大专、本科、硕士、博士
    for field in result:
        education.append(field[0])
    # 获取到每种学历对应的个数
    for i in range(len(education)):
        cursor.execute("SELECT count(*) from demo where education = '" +
                       education[i] + "' and city in ('北京', '上海', '广州', '深圳');")
        count = cursor.fetchall()
        education_data.append(
            {'value': count[0][0], 'itemStyle': {'color': color_list[i]}})

    cursor.execute(
        "SELECT DISTINCT(workYear) from demo where city in ('北京', '上海', '广州', '深圳');")
    result = cursor.fetchall()
    workYear = []
    workYear_data = []
    # 获取到的几种工作经验
    for field in result:
        workYear.append(field[0])
    # 获取到每种工作经验对应的个数
    for i in workYear:
        cursor.execute("SELECT count(*) from demo where workYear = '" +
                       i + "' and city in ('北京', '上海', '广州', '深圳');")
        count = cursor.fetchall()
        workYear_data.append({'value': count[0][0], 'name': i})
    cursor.close()
    return jsonify({"education": education, "education_data": education_data, "workYear_data": workYear_data})


#这个视图函数与 /xueli 视图函数类似，不同之处在于它只查询城市为新一线城市的数据
@app.route('/xueli_nfirst', methods=['GET'])
def xueli_nfirst():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor
    cursor = conn.cursor()
    # 执行sql语句
    cursor.execute(
        "SELECT DISTINCT(education) from demo where city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
    # 获取所有记录列表
    result = cursor.fetchall()
    education = []
    education_data = []
    color_list = ['#459AF0', '#38C3B0', '#86CA5A', '#BFD44F', '	#90EE90']
    # 获取到学历的五种情况：不限、大专、本科、硕士、博士
    for field in result:
        education.append(field[0])
    # 获取到每种学历对应的个数
    for i in range(len(education)):
        cursor.execute("SELECT count(*) from demo where education = '" +
                       education[i] + "' and city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
        count = cursor.fetchall()
        education_data.append(
            {'value': count[0][0], 'itemStyle': {'color': color_list[i]}})

    cursor.execute(
        "SELECT DISTINCT(workYear) from demo where city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
    result = cursor.fetchall()
    workYear = []
    workYear_data = []
    # 获取到的几种工作经验
    for field in result:
        workYear.append(field[0])
    # 获取到每种工作经验对应的个数
    for i in workYear:
        cursor.execute("SELECT count(*) from demo where workYear = '" + i +
                       "' and city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
        count = cursor.fetchall()
        workYear_data.append({'value': count[0][0], 'name': i})
    cursor.close()
    return jsonify({"education": education, "education_data": education_data, "workYear_data": workYear_data})


#这个视图函数与 /xueli 视图函数类似，不同之处在于它只查询城市为二线城市的数据
@app.route('/xueli_second', methods=['GET'])
def xueli_second():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor
    cursor = conn.cursor()
    # 执行sql语句
    cursor.execute("SELECT DISTINCT(education) from demo where city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
    # 获取所有记录列表
    result = cursor.fetchall()
    education = []
    education_data = []
    color_list = ['#459AF0', '#38C3B0', '#86CA5A', '#BFD44F', '	#90EE90']
    # 获取到学历的五种情况：不限、大专、本科、硕士、博士
    for field in result:
        education.append(field[0])
    # 获取到每种学历对应的个数
    for i in range(len(education)):
        cursor.execute("SELECT count(*) from demo where education = '" +
                       education[i] + "' and city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
        count = cursor.fetchall()
        education_data.append(
            {'value': count[0][0], 'itemStyle': {'color': color_list[i]}})

    cursor.execute("SELECT DISTINCT(workYear) from demo where city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
    result = cursor.fetchall()
    workYear = []
    workYear_data = []
    # 获取到的几种工作经验
    for field in result:
        workYear.append(field[0])
    # 获取到每种工作经验对应的个数
    for i in workYear:
        cursor.execute("SELECT count(*) from demo where workYear = '" + i +
                       "' and city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
        count = cursor.fetchall()
        workYear_data.append({'value': count[0][0], 'name': i})
    cursor.close()
    return jsonify({"education": education, "education_data": education_data, "workYear_data": workYear_data})


#公司福利+职位福利
@app.route('/fuli', methods=['GET'])
def fuli():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    #使用 pymysql.cursors.DictCursor 作为游标类型，这样查询结果将以字典形式返回
    #conn.cursor() 创建的是默认游标，其查询结果以 元组列表 形式返回（如 [(value1, value2), ...]），
    # 需要通过索引（如 row[0]）访问字段值。
    #pymysql.cursors.DictCursor 返回 字典列表（如 [{'field1': value1, 'field2': value2}, ...]），
    # 可通过字段名直接访问值（如 row['positionAdvantage']）。
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    cursor.execute("select positionAdvantage from `demo`")
    data_dict = []
    result = cursor.fetchall()
    for field in result:
        data_dict.append(field['positionAdvantage'])
    #将 data_dict 列表中的所有字符串连接成一个大字符串 content,236行-242行见笔记一.jieba库
    content = ''.join(data_dict)
    positionAdvantage = []
    #设置停用词文件，在关键词提取时会忽略这些停用词
    jieba.analyse.set_stop_words('./stopwords.txt')
    #使用 jieba 库的 extract_tags 方法从 content 中提取前 100 个关键词，并返回关键词及其权重，重要性得分，数值越大越重要
    tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
    #遍历提取的关键词(v)及其权重(n)
    for v, n in tags:
        #创建一个空字典
        mydict = {}
        #将关键词存储在字典的 name 键中
        mydict["name"] = v
        #将关键词的权重乘以 10000 并转换为整数，再转换为字符串，存储在字典的 value 键中
        #将浮点权重（如 0.85）转换为整数（8500），便于前端处理
        mydict["value"] = str(int(n * 10000))
        #将字典添加到 positionAdvantage 列表中
        positionAdvantage.append(mydict)
    cursor.execute("select companyLabelList from `demo`")
    #与前面提取 positionAdvantage 字段的过程类似，将 companyLabelList 字段的值存储在 data_dict 列表中
    data_dict = []
    result = cursor.fetchall()
    for field in result:
        data_dict.append(field['companyLabelList'])
    content = ''.join(data_dict)
    companyLabelList = []
    jieba.analyse.set_stop_words('./stopwords.txt')
    tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
    for v, n in tags:
        mydict = {}
        mydict["name"] = v
        mydict["value"] = str(int(n * 10000))
        companyLabelList.append(mydict)
    cursor.close()
    #职位福利，公司福利
    return jsonify({"zwfl": positionAdvantage, "gsfl": companyLabelList})


@app.route('/fuli_first', methods=['GET'])
def fuli_first():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    cursor.execute(
        "select positionAdvantage from `demo` where city in ('北京', '上海', '广州', '深圳');")
    data_dict = []
    result = cursor.fetchall()
    for field in result:
        data_dict.append(field['positionAdvantage'])
    content = ''.join(data_dict)
    positionAdvantage = []
    jieba.analyse.set_stop_words('./stopwords.txt')
    tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
    for v, n in tags:
        mydict = {}
        mydict["name"] = v
        mydict["value"] = str(int(n * 10000))
        positionAdvantage.append(mydict)

    cursor.execute(
        "select companyLabelList from `demo` where city in ('北京', '上海', '广州', '深圳');")
    data_dict = []
    result = cursor.fetchall()
    for field in result:
        data_dict.append(field['companyLabelList'])
    content = ''.join(data_dict)
    companyLabelList = []
    jieba.analyse.set_stop_words('./stopwords.txt')
    tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
    for v, n in tags:
        mydict = {}
        mydict["name"] = v
        mydict["value"] = str(int(n * 10000))
        companyLabelList.append(mydict)
    cursor.close()
    return jsonify({"zwfl": positionAdvantage, "gsfl": companyLabelList})


@app.route('/fuli_nfirst', methods=['GET'])
def fuli_nfirst():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    cursor.execute(
        "select positionAdvantage from `demo` where city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
    data_dict = []
    result = cursor.fetchall()
    for field in result:
        data_dict.append(field['positionAdvantage'])
    content = ''.join(data_dict)
    positionAdvantage = []
    jieba.analyse.set_stop_words('./stopwords.txt')
    tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
    for v, n in tags:
        mydict = {}
        mydict["name"] = v
        mydict["value"] = str(int(n * 10000))
        positionAdvantage.append(mydict)

    cursor.execute(
        "select companyLabelList from `demo` where city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
    data_dict = []
    result = cursor.fetchall()
    for field in result:
        data_dict.append(field['companyLabelList'])
    content = ''.join(data_dict)
    companyLabelList = []
    jieba.analyse.set_stop_words('./stopwords.txt')
    tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
    for v, n in tags:
        mydict = {}
        mydict["name"] = v
        mydict["value"] = str(int(n * 10000))
        companyLabelList.append(mydict)
    cursor.close()
    return jsonify({"zwfl": positionAdvantage, "gsfl": companyLabelList})


@app.route('/fuli_second', methods=['GET'])
def fuli_second():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    cursor.execute("select positionAdvantage from `demo` where city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
    data_dict = []
    result = cursor.fetchall()
    for field in result:
        data_dict.append(field['positionAdvantage'])
    content = ''.join(data_dict)
    positionAdvantage = []
    jieba.analyse.set_stop_words('./stopwords.txt')
    tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
    for v, n in tags:
        mydict = {}
        mydict["name"] = v
        mydict["value"] = str(int(n * 10000))
        positionAdvantage.append(mydict)

    cursor.execute("select companyLabelList from `demo` where city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
    data_dict = []
    result = cursor.fetchall()
    for field in result:
        data_dict.append(field['companyLabelList'])
    content = ''.join(data_dict)
    companyLabelList = []
    jieba.analyse.set_stop_words('./stopwords.txt')
    tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
    for v, n in tags:
        mydict = {}
        mydict["name"] = v
        mydict["value"] = str(int(n * 10000))
        companyLabelList.append(mydict)
    cursor.close()
    return jsonify({"zwfl": positionAdvantage, "gsfl": companyLabelList})


#城市+公司规模，查询条件：某种职业
@app.route('/qiye', methods=['GET'])
def qiye():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT(city) from demo")
    result = cursor.fetchall()
    city = []
    city_result = []
    companySize = []
    companySizeResult = []
    selected = {}
    # 获取到的城市
    for field in result:
        city.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到城市对应的个数
        #直接遍历列表中的每个元素，i 依次取到列表中的城市名（如 i = '北京'，i = '上海' 等），无需通过索引 city[i] 取值，见与59行的区别
        for i in city:
            cursor.execute(
                "SELECT count(*) from demo where city = '" + i + "'")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            city_result.append(dict)
        # 初始化最开始显示几个城市
        #对 city 列表中索引为 10 及之后的城市元素进行处理，将它们作为键添加到 selected 字典里，并且把对应的值设为 False。
        # 这通常是为了在前端页面里初始化某些城市的选中状态，也就是默认让这些城市处于未选中状态。
        for i in city[10:]:
            selected[i] = False
        # 获取到几种公司规模
        cursor.execute("SELECT DISTINCT(companySize) from demo")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute(
                #因为每个元组只有一个元素（公司规模名称），例如 field = (‘100-499人’,)
                "SELECT count(*) from demo where companySize = '" + field[0] + "'")
            count = cursor.fetchall()
            companySizeResult.append(count[0][0])
    else:
        #从 HTTP 请求的查询参数positionName中获取用户输入的职位名称，并将其转换为小写字符串（避免大小写敏感），用于后续的模糊查询
        #Flask 的 request.args 是一个类似字典的对象，专门用于存储 GET 请求的查询参数
        positionName = str(request.args['positionName']).lower()
        # 查询条件：某种职业
        # 每个城市某种职业的个数
        for i in city:
            #在 COUNT(*) 查询中添加 positionName like '%...%'（模糊查询），表示只要职位名称中包含 positionName 即可匹配，
            cursor.execute("SELECT count(*) from demo where city = '" +
                           i + "' and positionName like '%"+positionName+"%'")
            #获取查询结果。由于是 COUNT(*) 查询，结果通常是一个包含单个元组的列表，元组中只有一个元素，即统计的数量
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            city_result.append(dict)
        for i in city[10:]:
            selected[i] = False
        cursor.execute("SELECT DISTINCT(companySize) from demo")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and positionName like '%"+positionName+"%'")
            count = cursor.fetchall()
            companySizeResult.append(count[0][0])
    result = {"city": city, "city_result": city_result, "selected": selected,
              "companySize": companySize, "companySizeResult": companySizeResult}
    cursor.close()
    return jsonify(result)


@app.route('/qiye_first', methods=['GET'])
def qiye_first():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    #cursor.execute("SELECT DISTINCT(city) from demo")
    #result = cursor.fetchall()
    city = ['北京', '上海', '广州', '深圳']
    city_result = []
    companySize = []
    companySizeResult = []
    selected = {}
    # 获取到的城市
    # for field in result:
    # city.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到城市对应的个数
        for i in city:
            cursor.execute(
                "SELECT count(*) from demo where city = '" + i + "'")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            city_result.append(dict)
        # 初始化最开始显示几个城市
        for i in city[4:]:
            selected[i] = False
        # 获取到几种公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city in ('北京', '上海', '广州', '深圳');")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and city in ('北京', '上海', '广州', '深圳');")
            count = cursor.fetchall()
            companySizeResult.append(count[0][0])
    else:
        positionName = str(request.args['positionName']).lower()
        # 查询条件：某种职业
        # 每个城市某种职业的个数
        for i in city:
            cursor.execute("SELECT count(*) from demo where city = '" +
                           i + "' and positionName like '%"+positionName+"%'")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            city_result.append(dict)
        for i in city[4:]:
            selected[i] = False
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city in ('北京', '上海', '广州', '深圳');")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and positionName like '%"+positionName+"%' and city in ('北京', '上海', '广州', '深圳');")
            count = cursor.fetchall()
            companySizeResult.append(count[0][0])

    result = {"city": city, "city_result": city_result, "selected": selected,
              "companySize": companySize, "companySizeResult": companySizeResult}
    cursor.close()
    return jsonify(result)


@app.route('/qiye_nfirst', methods=['GET'])
def qiye_nfirst():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    #cursor.execute("SELECT DISTINCT(city) from demo")
    #result = cursor.fetchall()
    city = ['成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州',
            '南京', '郑州', '长沙', '东莞', '沈阳', '青岛', '合肥', '佛山']
    city_result = []
    companySize = []
    companySizeResult = []
    selected = {}
    # 获取到的城市
    # for field in result:
    # city.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到城市对应的个数
        for i in city:
            cursor.execute(
                "SELECT count(*) from demo where city = '" + i + "'")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            city_result.append(dict)
        # 初始化最开始显示几个城市
        for i in city[15:]:
            selected[i] = False
        # 获取到几种公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
            count = cursor.fetchall()
            companySizeResult.append(count[0][0])
    else:
        positionName = str(request.args['positionName']).lower()
        # 查询条件：某种职业
        # 每个城市某种职业的个数
        for i in city:
            cursor.execute("SELECT count(*) from demo where city = '" +
                           i + "' and positionName like '%"+positionName+"%'")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            city_result.append(dict)
        for i in city[15:]:
            selected[i] = False
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" + field[0] + "' and positionName like '%"+positionName +
                           "%' and city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
            count = cursor.fetchall()
            companySizeResult.append(count[0][0])

    result = {"city": city, "city_result": city_result, "selected": selected,
              "companySize": companySize, "companySizeResult": companySizeResult}
    cursor.close()
    return jsonify(result)


@app.route('/qiye_second', methods=['GET'])
def qiye_second():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    #cursor.execute("SELECT DISTINCT(city) from demo")
    #result = cursor.fetchall()
    city = ['宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州', '南宁', '长春', '南昌',
            '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊']
    city_result = []
    companySize = []
    companySizeResult = []
    selected = {}
    # 获取到的城市
    # for field in result:
    # city.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到城市对应的个数
        for i in city:
            cursor.execute(
                "SELECT count(*) from demo where city = '" + i + "'")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            city_result.append(dict)
        # 初始化最开始显示几个城市
        for i in city[30:]:
            selected[i] = False
        # 获取到几种公司规模
        cursor.execute("SELECT DISTINCT(companySize) from demo where city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
            count = cursor.fetchall()
            companySizeResult.append(count[0][0])
    else:
        positionName = str(request.args['positionName']).lower()
        # 查询条件：某种职业
        # 每个城市某种职业的个数
        for i in city:
            cursor.execute("SELECT count(*) from demo where city = '" +
                           i + "' and positionName like '%"+positionName+"%'")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            city_result.append(dict)
        for i in city[30:]:
            selected[i] = False
        cursor.execute("SELECT DISTINCT(companySize) from demo where city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" + field[0] + "' and positionName like '%"+positionName +
                           "%' and city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
            count = cursor.fetchall()
            companySizeResult.append(count[0][0])

    result = {"city": city, "city_result": city_result, "selected": selected,
              "companySize": companySize, "companySizeResult": companySizeResult}
    cursor.close()
    return jsonify(result)


#薪资，搜索条件：学历
@app.route('/xinzi', methods=['GET'])
def xinzi():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    #positionName 定义了需要统计的职位名称，小写，与后续模糊查询匹配
    positionName = ['java', 'python', 'php', 'web', 'bi',
                    'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
    # 柱状图返回列表
    zzt_list = []
    #zzt_list 是二维列表，第一行是表头，包含 “product” 和各职位名称
    zzt_list.append(['product', 'Java', 'Python', 'PHP', 'web',
                    'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
    if (len(request.args) == 0 or str(request.args['education']) == '不限'):
        #创建了一个空列表 temp_list，用于临时存储每个职位在当前薪资区间（这里是 0 - 10K）的岗位数量
        temp_list = []
        for i in positionName:
            cursor.execute(
                #截取薪资字段前两个字符，判断是否包含 “K”
                #salary：表示要进行截取操作的目标字段，1：代表截取的起始位置，2：表示要截取的字符数量
                #salary：a：10k - 20k，b：20 - 30k，c：5k - 8k，返回结果：a：10，b：20，c：5k。
                #只有c的前两个字符包含 k，c属于0-10k
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%K%' and positionName like '%"+i+"%';")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%"+i+"%';")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%"+i+"%';")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%';")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%';")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    else:
        education = str(request.args['education'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%K%' and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    result = {"zzt": zzt_list}
    cursor.close()
    return jsonify(result)


@app.route('/xinzi_first', methods=['GET'])
def xinzi_first():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    #citys = ['北京', '上海', '广州', '深圳']
    positionName = ['java', 'python', 'php', 'web', 'bi',
                    'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
    # 柱状图返回列表
    zzt_list = []
    zzt_list.append(['product', 'Java', 'Python', 'PHP', 'web',
                    'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
    if (len(request.args) == 0 or str(request.args['education']) == '不限'):
        temp_list = []
        for i in positionName:
            cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%K%' and positionName like '%" +
                           i+"%' and city in ('北京', '上海', '广州', '深圳');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" +
                           i+"%' and city in ('北京', '上海', '广州', '深圳');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" +
                           i+"%' and city in ('北京', '上海', '广州', '深圳');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and city in ('北京', '上海', '广州', '深圳');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and city in ('北京', '上海', '广州', '深圳');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    else:
        education = str(request.args['education'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('北京', '上海', '广州', '深圳') and SUBSTR(salary,1,2) like '%K%' and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('北京', '上海', '广州', '深圳') and SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('北京', '上海', '广州', '深圳') and SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('北京', '上海', '广州', '深圳') and SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('北京', '上海', '广州', '深圳') and SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    result = {"zzt": zzt_list}
    cursor.close()
    return jsonify(result)


@app.route('/xinzi_nfirst', methods=['GET'])
def xinzi_nfirst():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    #citys = ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山')
    positionName = ['java', 'python', 'php', 'web', 'bi',
                    'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
    # 柱状图返回列表
    zzt_list = []
    zzt_list.append(['product', 'Java', 'Python', 'PHP', 'web',
                    'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
    if (len(request.args) == 0 or str(request.args['education']) == '不限'):
        temp_list = []
        for i in positionName:
            cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%K%' and positionName like '%"+i +
                           "%' and city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" +
                           i+"%' and city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" +
                           i+"%' and city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    else:
        education = str(request.args['education'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山') and SUBSTR(salary,1,2) like '%K%' and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山') and SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山') and SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山') and SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山') and SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    result = {"zzt": zzt_list}
    cursor.close()
    return jsonify(result)


@app.route('/xinzi_second', methods=['GET'])
def xinzi_second():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    #citys = ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊')
    positionName = ['java', 'python', 'php', 'web', 'bi',
                    'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
    # 柱状图返回列表
    zzt_list = []
    zzt_list.append(['product', 'Java', 'Python', 'PHP', 'web',
                    'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
    if (len(request.args) == 0 or str(request.args['education']) == '不限'):
        temp_list = []
        for i in positionName:
            cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%K%' and positionName like '%"+i +
                           "%' and city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%"+i +
                           "%' and city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%"+i +
                           "%' and city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    else:
        education = str(request.args['education'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊') and SUBSTR(salary,1,2) like '%K%' and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊') and SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊') and SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊') and SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊') and SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and education = '"+education+"'")
            count = cursor.fetchall()
            temp_list += count[0]
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    result = {"zzt": zzt_list}
    cursor.close()
    return jsonify(result)


#融资
@app.route('/rongzi', methods=['GET'])
def rongzi():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT(financeStage) from demo")
    result = cursor.fetchall()
    finance = []
    finance_data = []
    # 获取到融资的几种情况
    for field in result:
        finance.append(field[0])
    # 获取到每种融资对应的个数
    for i in range(len(finance)):
        cursor.execute(
            "SELECT count(*) from demo where financeStage = '" + finance[i] + "'")
        count = cursor.fetchall()
        finance_data.append({'value': count[0][0], 'name': finance[i]})
    cursor.close()
    return jsonify({"finance": finance, "finance_data": finance_data})


@app.route('/rongzi_first', methods=['GET'])
def rongzi_first():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT(financeStage) from demo where city in ('北京', '上海', '广州', '深圳');")
    result = cursor.fetchall()
    finance = []
    finance_data = []
    # 获取到融资的几种情况
    for field in result:
        finance.append(field[0])
    # 获取到每种融资对应的个数
    for i in range(len(finance)):
        cursor.execute("SELECT count(*) from demo where financeStage = '" +
                       finance[i] + "' and city in ('北京', '上海', '广州', '深圳');")
        count = cursor.fetchall()
        finance_data.append({'value': count[0][0], 'name': finance[i]})
    cursor.close()
    return jsonify({"finance": finance, "finance_data": finance_data})


@app.route('/rongzi_nfirst', methods=['GET'])
def rongzi_nfirst():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT(financeStage) from demo where city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
    result = cursor.fetchall()
    finance = []
    finance_data = []
    # 获取到融资的几种情况
    for field in result:
        finance.append(field[0])
    # 获取到每种融资对应的个数
    for i in range(len(finance)):
        cursor.execute("SELECT count(*) from demo where financeStage = '" +
                       finance[i] + "' and city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
        count = cursor.fetchall()
        finance_data.append({'value': count[0][0], 'name': finance[i]})
    cursor.close()
    return jsonify({"finance": finance, "finance_data": finance_data})


@app.route('/rongzi_second', methods=['GET'])
def rongzi_second():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT(financeStage) from demo where city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
    result = cursor.fetchall()
    finance = []
    finance_data = []
    # 获取到融资的几种情况
    for field in result:
        finance.append(field[0])
    # 获取到每种融资对应的个数
    for i in range(len(finance)):
        cursor.execute("SELECT count(*) from demo where financeStage = '" +
                       finance[i] + "' and city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
        count = cursor.fetchall()
        finance_data.append({'value': count[0][0], 'name': finance[i]})
    cursor.close()
    return jsonify({"finance": finance, "finance_data": finance_data})


#职业类型：第一职业＋第二职业
@app.route('/poststyle', methods=['GET'])
def poststyle():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT(firstType) from demo")
    result = cursor.fetchall()
    firstType = []
    firstType_data = []
    # 获取到职位类型的几种情况
    for field in result:
        firstType.append(field[0])
    # 获取到每种职位类型对应的个数
    for i in range(len(firstType)):
        cursor.execute(
            "SELECT count(*) from demo where firstType = '" + firstType[i] + "'")
        count = cursor.fetchall()
        firstType_data.append({'value': count[0][0], 'name': firstType[i]})
    cursor.execute("SELECT DISTINCT(secondType) from demo")
    second = cursor.fetchall()
    secondType = []
    secondType_data = []
    # 获取到职位类型的几种情况
    for field in second:
        secondType.append(field[0])
    # 获取到每种职位类型对应的个数
    for i in range(len(secondType)):
        cursor.execute(
            "SELECT count(*) from demo where secondType = '" + secondType[i] + "'")
        count = cursor.fetchall()
        secondType_data.append({'value': count[0][0], 'name': secondType[i]})
    cursor.close()
    return jsonify({"firstType": firstType, "firstType_data": firstType_data, "secondType": secondType, "secondType_data": secondType_data})


@app.route('/poststyle_first', methods=['GET'])
def poststyle_first():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT(firstType) from demo where city in ('北京', '上海', '广州', '深圳');")
    result = cursor.fetchall()
    firstType = []
    firstType_data = []
    # 获取到职位类型的几种情况
    for field in result:
        firstType.append(field[0])
    # 获取到每种职位类型对应的个数
    for i in range(len(firstType)):
        cursor.execute("SELECT count(*) from demo where firstType = '" +
                       firstType[i] + "' and city in ('北京', '上海', '广州', '深圳');")
        count = cursor.fetchall()
        firstType_data.append({'value': count[0][0], 'name': firstType[i]})

    cursor.execute(
        "SELECT DISTINCT(secondType) from demo where city in ('北京', '上海', '广州', '深圳');")
    second = cursor.fetchall()
    secondType = []
    secondType_data = []
    # 获取到职位类型的几种情况
    for field in second:
        secondType.append(field[0])
    # 获取到每种职位类型对应的个数
    for i in range(len(secondType)):
        cursor.execute("SELECT count(*) from demo where secondType = '" +
                       secondType[i] + "' and city in ('北京', '上海', '广州', '深圳');")
        count = cursor.fetchall()
        secondType_data.append({'value': count[0][0], 'name': secondType[i]})
    cursor.close()
    return jsonify({"firstType": firstType, "firstType_data": firstType_data, "secondType": secondType, "secondType_data": secondType_data})


@app.route('/poststyle_nfirst', methods=['GET'])
def poststyle_nfirst():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT(firstType) from demo where city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
    result = cursor.fetchall()
    firstType = []
    firstType_data = []
    # 获取到职位类型的几种情况
    for field in result:
        firstType.append(field[0])
    # 获取到每种职位类型对应的个数
    for i in range(len(firstType)):
        cursor.execute("SELECT count(*) from demo where firstType = '" +
                       firstType[i] + "' and city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
        count = cursor.fetchall()
        firstType_data.append({'value': count[0][0], 'name': firstType[i]})

    cursor.execute(
        "SELECT DISTINCT(secondType) from demo where city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
    second = cursor.fetchall()
    secondType = []
    secondType_data = []
    # 获取到职位类型的几种情况
    for field in second:
        secondType.append(field[0])
    # 获取到每种职位类型对应的个数
    for i in range(len(secondType)):
        cursor.execute("SELECT count(*) from demo where secondType = '" +
                       secondType[i] + "' and city in ('成都', '重庆', '杭州', '武汉', '西安', '天津', '苏州', '南京', '郑州', '长沙', '东莞' ,'沈阳', '青岛', '合肥', '佛山');")
        count = cursor.fetchall()
        secondType_data.append({'value': count[0][0], 'name': secondType[i]})
    cursor.close()
    return jsonify({"firstType": firstType, "firstType_data": firstType_data, "secondType": secondType, "secondType_data": secondType_data})


@app.route('/poststyle_second', methods=['GET'])
def poststyle_second():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT(firstType) from demo where city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
    result = cursor.fetchall()
    firstType = []
    firstType_data = []
    # 获取到职位类型的几种情况
    for field in result:
        firstType.append(field[0])
    # 获取到每种职位类型对应的个数
    for i in range(len(firstType)):
        cursor.execute("SELECT count(*) from demo where firstType = '" +
                       firstType[i] + "' and city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
        count = cursor.fetchall()
        firstType_data.append({'value': count[0][0], 'name': firstType[i]})

    cursor.execute("SELECT DISTINCT(secondType) from demo where city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
    second = cursor.fetchall()
    secondType = []
    secondType_data = []
    # 获取到职位类型的几种情况
    for field in second:
        secondType.append(field[0])
    # 获取到每种职位类型对应的个数
    for i in range(len(secondType)):
        cursor.execute("SELECT count(*) from demo where secondType = '" +
                       secondType[i] + "' and city in ('宁波', '昆明', '福州', '无锡', '济南', '厦门', '大连', '哈尔滨', '温州', '石家庄', '泉州' ,'南宁', '长春', '南昌', '贵阳', '金华', '常州', '惠州', '嘉兴', '南通', '徐州', '太原', '珠海', '中山', '保定', '兰州', '台州', '绍兴', '烟台', '廊坊');")
        count = cursor.fetchall()
        secondType_data.append({'value': count[0][0], 'name': secondType[i]})
    cursor.close()
    return jsonify({"firstType": firstType, "firstType_data": firstType_data, "secondType": secondType, "secondType_data": secondType_data})


#Dashboard里的招聘数据概况
@app.route('/data', methods=['GET'])
def data():
    #limit 通常表示每页显示的记录数量
    limit = int(request.args['limit'])
    #page 表示当前请求的页码
    page = int(request.args['page'])
    #计算偏移量，因为 SQL 中的 LIMIT 子句的偏移量是从 0 开始的，所以需要将页码转换为偏移量
    page = (page-1)*limit
    conn = pymysql.connect(host='localhost', user='root',
                           password='root', port=3306, db='lagou', charset='utf8mb4')
    cursor = conn.cursor()
    #没有额外筛选条件
    #当len(request.args) == 2 时，说明请求中只有 limit 和 page 这两个参数，没有传入 education 或 positionName
    if (len(request.args) == 2):
        cursor.execute("select count(*) from demo")
        #存储满足特定条件的记录总数，它在分页查询的场景中起着关键作用，有助于前端展示数据总量以及实现分页导航功能
        count = cursor.fetchall()
        # 使用 pymysql.cursors.DictCursor 作为游标类型，这样查询结果将以字典形式返回
        # conn.cursor() 创建的是默认游标，其查询结果以 元组列表 形式返回（如 [(value1, value2), ...]），
        # 需要通过索引（如 row[0]）访问字段值。
        # pymysql.cursors.DictCursor 返回 字典列表（如 [{'field1': value1, 'field2': value2}, ...]），
        # 可通过字段名直接访问值（如 row['positionAdvantage']）。
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        # 从 demo 表中查询指定偏移量和数量的记录
        # LIMIT 20, 10是跳过前20条记录，返回接下来的10条记录
        cursor.execute("select * from demo limit "+str(page)+","+str(limit))
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field)
    # 有额外检索条件
    else:
        education = str(request.args['education'])
        positionName = str(request.args['positionName']).lower()
        # 有额外检索条件（学历＋职位），且学历为不限
        if(education == '不限'):
            cursor.execute(
                "select count(*) from demo where positionName like '%"+positionName+"%'")
            count = cursor.fetchall()
            cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute("select * from demo where positionName like '%" +
                           positionName+"%' limit " + str(page) + "," + str(limit))
            data_dict = []
            result = cursor.fetchall()
            for field in result:
                data_dict.append(field)
        # 有额外检索条件（学历＋职位），且学历有限制
        else:
            cursor.execute("select count(*) from demo where positionName like '%" +
                           positionName+"%' and education = '"+education+"'")
            count = cursor.fetchall()
            cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute("select * from demo where positionName like '%"+positionName +
                           "%' and education = '"+education+"' limit " + str(page) + "," + str(limit))
            data_dict = []
            result = cursor.fetchall()
            for field in result:
                data_dict.append(field)
    #将查询结果封装成一个字典，包含状态码 code、消息 msg、总记录数 count 和查询到的数据 data
    table_result = {"code": 0, "msg": None,
                    "count": count[0], "data": data_dict}
    cursor.close()
    conn.close()
    return jsonify(table_result)


#Dashboard里的租房数据概况，逻辑同上面的data（）
@app.route('/zufang_data', methods=['GET'])
def zufang_data():
    limit = int(request.args['limit'])
    page = int(request.args['page'])
    page = (page-1)*limit
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')

    cursor = conn.cursor()
    if (len(request.args) == 2):
        cursor.execute("select count(*) from house;")
        count = cursor.fetchall()
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute("select * from house limit "+str(page)+","+str(limit))
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field)
    else:
        city = str(request.args['city'])
        cursor.execute("select count(*) from house where city = '"+city+"';")
        count = cursor.fetchall()
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute("select * from house where city = '" +
                       city+"' limit " + str(page) + "," + str(limit))
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field)
    table_result = {"code": 0, "msg": None,
                    "count": count[0], "data": data_dict}
    cursor.close()
    conn.close()
    return jsonify(table_result)


#获取城市数据（城市名称及对应岗位数量），用于地图可视化
@app.route('/map', methods=['GET'])
def map():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT(city) from demo")
    result = cursor.fetchall()
    city = []
    city_result = []
    # 获取到的城市
    for field in result:
        city.append(field[0])
    # 获取到城市对应的个数
    for i in city:
        cursor.execute("SELECT count(*) from demo where city = '" + i + "'")
        count = cursor.fetchall()
        dict = {'value': count[0][0], 'name': i}
        city_result.append(dict)

    result = {"city": city, "city_result": city_result}
    cursor.close()
    return jsonify(result)


# 注册用户，检查用户名是否存在，存在则报错，否则插入新用户
@app.route('/addUser', methods=['POST'])
def addUser():
    # 服务器端获取json
    get_json = request.get_json()
    # 从获取的 JSON 数据中提取用户名
    name = get_json['name']
    password = get_json['password']
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(
        "select count(*) from `user` where `username` = '" + name + "'")
    count = cursor.fetchall()
    # 该昵称已存在
    if (count[0][0] != 0):
        table_result = {"code": 500, "msg": "该昵称已存在！"}
        cursor.close()
    else:
        add = conn.cursor()
        sql = "insert into `user`(username,password) values('" + \
            name+"','"+password+"');"
        add.execute(sql)
        # 提交事务，将插入操作保存到数据库
        conn.commit()
        table_result = {"code": 200, "msg": "注册成功"}
        add.close()
    conn.close()
    # 将结果字典转换为 JSON 格式并返回给客户端
    return jsonify(table_result)


# 用户登录，验证用户名和密码，返回登录结果
@app.route('/loginByPassword', methods=['POST'])
def loginByPassword():
    get_json = request.get_json()
    name = get_json['name']
    password = get_json['password']
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("select count(*) from `user` where `username` = '" +
                   name + "' and password = '" + password+"';")
    count = cursor.fetchall()
    if(count[0][0] != 0):
        session['username'] = name  # 登录成功，将会话中的用户名设置为当前登录用户
        table_result = {"code": 200, "msg": name}
        cursor.close()
    else:
        name_cursor = conn.cursor()
        name_cursor.execute(
            "select count(*) from `user` where `username` = '" + name + "';")
        name_count = name_cursor.fetchall()
        if(name_count[0][0] != 0):
            table_result = {"code": 500, "msg": "密码错误！"}
        else:
            table_result = {"code": 500, "msg": "该用户不存在，请先注册！"}
        name_cursor.close()
    conn.close()
    print(name)
    return jsonify(table_result)

#验证用户输入的用户名、原始密码以及两次新密码是否一致，同时检查用户名与当前登录用户是否匹配。
@app.route('/verifyPass', methods=['POST'])
def verifyPass():
    get_json = request.get_json()
    name = get_json['name']
    oldPsw = get_json['oldPsw']
    newPsw = get_json['newPsw']
    rePsw = get_json['rePsw']
    current_username = session.get('username')

    if name != current_username:
        return jsonify({"code": 500, "msg": "更新失败，输入的用户名与当前登录账号不匹配！"})

    if newPsw != rePsw:
        return jsonify({"code": 500, "msg": "两次新密码输入不一致"})

    try:
        conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                               charset='utf8mb4')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM `user` WHERE `username` = %s AND password = %s", (name, oldPsw))
        count = cursor.fetchone()
        if count[0] == 0:
            return jsonify({"code": 500, "msg": "原始密码错误！"})
        return jsonify({"code": 200, "username": name, "new_password": newPsw})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


# 密码修改，接收前端传来的用户名和新密码，在数据库中更新用户密码。同样会检查用户名与当前登录用户是否匹配
@app.route('/updatePass', methods=['POST'])
def updatePass():
    get_json = request.get_json()
    name = get_json['name']
    newPsw = get_json['newPsw']
    current_username = session.get('username')

    if name != current_username:
        return jsonify({"code": 500, "msg": "更新失败，输入的用户名与当前登录账号不匹配！"})

    try:
        conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                               charset='utf8mb4')
        cursor = conn.cursor()
        sql = "UPDATE `user` SET password = %s WHERE username = %s"
        cursor.execute(sql, (newPsw, name))
        conn.commit()
        table_result = {"code": 200, "msg": "密码修改成功！",
                        "username": name, "new_password": newPsw}
    except Exception as e:
        table_result = {"code": 500, "msg": f"更新失败：{str(e)}"}
        conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    return jsonify(table_result)


#修改个人信息（包括邮箱、简介、地址、电话）
@app.route('/updateUserInfo', methods=['POST'])
def updateUserInfo():
    if 'username' not in session:
        return jsonify({"code": 401, "msg": "未登录，请先登录！"})
    get_json = request.get_json()
    name = get_json['name']
    print(name)
    current_username = session['username']

    if name != current_username:
        return jsonify({"code": 500, "msg": "更新失败，输入的用户名与当前登录账号不匹配！"})

    email = get_json['email']
    content = get_json['content']
    address = get_json['address']
    phone = get_json['phone']
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("update `user` set email = '"+email+"',content = '"+content +
                   "',address = '"+address+"',phone = '"+phone+"' where username = '" + name + "';")
    conn.commit()
    table_result = {"code": 200, "msg": "更新成功！",
                    "youxiang": email, "tel": phone}
    cursor.close()
    conn.close()
    print(table_result)
    return jsonify(table_result)

# 个人信息查询（邮箱、简介、地址、电话）
@app.route('/selectUserInfo', methods=['GET'])
def selectUserInfo():
    name = str(request.args['name'])
    print(name)
    email = []
    content = []
    address = []
    phone = []
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    # 邮箱
    cursor.execute("select email from user where username = '" + name + "';")
    result = cursor.fetchall()
    for field in result:
        email.append(field[0])
    # 个人简介
    cursor.execute("select content from user where username = '" + name + "';")
    result = cursor.fetchall()
    for field in result:
        content.append(field[0])
    # 地址
    cursor.execute("select address from user where username = '" + name + "';")
    result = cursor.fetchall()
    for field in result:
        address.append(field[0])
    # 联系方式
    cursor.execute("select phone from user where username = '" + name + "';")
    result = cursor.fetchall()
    for field in result:
        phone.append(field[0])

    table_result = {"code": 200, "msg": "查询成功！", "name": name, "email": email,
                    "content": content, "address": address, "phone": phone, "tel": phone, "youxiang": email}
    cursor.close()
    conn.close()
    print(table_result)
    return jsonify(table_result)


@app.route('/predict', methods=['GET'])
def predict():
    y_data = ['0—10K', '10—20K', '20—30K', '30—40K', '40K以上']
    positionName = str(request.args['positionName']).lower()#lower()：将字符串中的所有大写字母转换为小写字母
    print(positionName)
    model = str(request.args['model'])
    print(model)

    # 以二进制只读模式（'rb'）打开该文件。使用 pickle.load() 函数从文件中加载序列化的模型对象，并将其赋值给 selected_model 变量
    with open("predict_model/"+positionName+'_'+model+'.model', 'rb') as fr:
        selected_model = pickle.load(fr)
    companySize = int(request.args['companySize'])
    workYear = int(request.args['workYear'])
    education = int(request.args['education'])
    city = int(request.args['city'])
    x = [companySize, workYear, education, city]
    # np.array() 函数将列表转换为 NumPy 数组
    x = np.array(x)
    # reshape(1, -1) 用于将一维的特征向量转换为二维数组，因为 predict() 方法通常要求输入是二维数组，
    # 其中第一维表示样本数量，第二维表示特征数量
    y = selected_model.predict(x.reshape(1, -1))
    # 根据模型预测的结果 y 作为索引，从 y_data 列表中获取对应的薪资范围，
    # 然后使用 jsonify() 函数将该薪资范围转换为 JSON 格式并返回给客户端
    return jsonify(y_data[y[0]])


@app.route('/beijing', methods=['GET'])
def beijing():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()

    district = []
    district_result = []
    companySize = []
    companySizeResult = []
    education = []
    educationResult = []
    workYear = []
    workYear_data = []
    firstType = []
    firstType_data = []
    finance = []
    finance_data = []
    leida_max_dict = []

    # 获取到的行政区
    cursor.execute("SELECT DISTINCT(district) from demo where city='北京';")
    result = cursor.fetchall()
    for field in result:
        district.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到行政区对应的个数
        for i in district:
            if i is None:  # 如果 district 是 NULL，跳过
                continue
            cursor.execute(
                "SELECT count(*) from demo where district = '" + i + "';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)

        # 获取到几种公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '北京';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute(
                "SELECT count(*) from demo where companySize = '" + field[0] + "' and city = '北京';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)

        # 获取到几种学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '北京';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            # 每种学历要求对应的个数
            cursor.execute(
                "SELECT count(*) from demo where education = '" + field[0] + "' and city = '北京';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)

        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '北京';")
        workyear = cursor.fetchall()
        # 获取到的几种工作经验
        for field in workyear:
            workYear.append(field[0])
        # 获取到每种工作经验对应的个数
        for i in workYear:
            cursor.execute(
                "SELECT count(*) from demo where workYear = '" + i + "' and city = '北京';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': i})

        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '北京';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 300})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute(
                "SELECT count(*) from demo where financeStage = '" + finance[i] + "' and city = '北京';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])

        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '北京';")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)

        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '北京';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            for i in field.keys():
                firstType.append(field[i])

        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and city = '北京';")
            count = cursor.fetchall()
            for field in count:
                for j in field.keys():
                    value = field[j]

            firstType_data.append({'value': value, 'name': firstType[i]})

        # 薪资待遇
        positionName = ['java', 'python', 'php', 'web', 'bi',
                        'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
        # 柱状图返回列表
        zzt_list = []
        #zzt_list是二维列表，第一行是表头，包含“product”和各职位名称
        zzt_list.append(
            ['product', 'Java', 'Python', 'PHP', 'web', 'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                #截取薪资字段前两个字符，判断是否包含“k”
                # salary：表示要进行截取操作的目标字段，1：代表截取的起始位置，2：表示要截取的字符数量
                # salary：a：10k - 20k，b：20 - 30k，c：5k - 8k，返回结果：a：10，b：20，c：5k。
                # 只有c的前两个字符包含 k，c属于0-10k
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" + i + "%' and city = '北京';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(
            ['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4], temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and city = '北京';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and city = '北京';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and city = '北京';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and city = '北京';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])

    else:
        positionName = str(request.args['positionName']).lower()
        print(positionName)
        # 查询条件：某种职业
        # 行政区
        for i in district:
            if i is None:  # 如果 district 是 NULL，跳过
                continue
            cursor.execute("SELECT count(*) from demo where district = '" +
                           i + "' and positionName like '%"+positionName+"%';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)
        # 公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '北京';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and positionName like '%"+positionName+"%' and city = '北京';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)
        # 学历要求，加入条件positionName
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '北京';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            cursor.execute("SELECT count(*) from demo where education = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '北京';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)
        # 工作经验
        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '北京';")
        workyear = cursor.fetchall()
        for field in workyear:
            workYear.append(field[0])
            cursor.execute("SELECT count(*) from demo where workYear = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '北京';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': field[0]})
        # 融资阶段
        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '北京';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 300})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute("SELECT count(*) from demo where financeStage = '" +
                           finance[i] + "' and positionName like '%" + positionName + "%' and city = '北京';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])
        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '北京';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            firstType.append(field[0])
        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and positionName like '%" + positionName + "%' and city = '北京';")
            count = cursor.fetchall()
            firstType_data.append({'value': count[0][0], 'name': firstType[i]})
        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '北京' and positionName like '%" + positionName + "%' ;")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)
        # 薪资待遇
        positionName_sample = ['java', 'python', 'php', 'web',
                               'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(['product', 'Java', 'Python', 'PHP', 'Web',
                        'BI', 'Android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        # <10k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" +
                       positionName + "%' and city = '北京';")
        count = cursor.fetchall()
        # print(count)
        for i in count[0].keys():
            value = count[0][i]
        print(value)
        ###########遍历所有预设职位，仅统计目标职位，其他职位薪资数量设为 0
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # print(temp_list)
        # temp_list.append(value)
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 10-20k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" +
                       positionName + "%' and city = '北京';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 20-30k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" +
                       positionName + "%' and city = '北京';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 30-40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" +
                       positionName + "%' and city = '北京';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # >40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" +
                       positionName + "%' and city = '北京';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['>40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    print(zzt_list)
    result = {"district": district, "district_result": district_result, "companySize": companySize, "companySizeResult": companySizeResult, "education": education, "educationResult": educationResult,
              "workYear_data": workYear_data, "firstType": firstType, "firstType_data": firstType_data, "leida_max_dict": leida_max_dict, "cyt": positionAdvantage, "finance": finance, "finance_data": finance_data, "zzt": zzt_list}
    cursor.close()
    return jsonify(result)


@app.route('/shanghai', methods=['GET'])
def shanghai():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()

    district = []
    district_result = []
    companySize = []
    companySizeResult = []
    education = []
    educationResult = []
    workYear = []
    workYear_data = []
    firstType = []
    firstType_data = []
    finance = []
    finance_data = []
    leida_max_dict = []

    # 获取到的行政区
    cursor.execute("SELECT DISTINCT(district) from demo where city='上海';")
    result = cursor.fetchall()
    for field in result:
        district.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到行政区对应的个数
        for i in district:
            if i is None:  # 如果 district 是 NULL，跳过
                continue
            cursor.execute(
                "SELECT count(*) from demo where district = '" + i + "';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)



        # 获取到几种公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '上海';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute(
                "SELECT count(*) from demo where companySize = '" + field[0] + "' and city = '上海';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)

        # 获取到几种学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '上海';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            # 每种学历要求对应的个数
            cursor.execute(
                "SELECT count(*) from demo where education = '" + field[0] + "' and city = '上海';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)

        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '上海';")
        workyear = cursor.fetchall()
        # 获取到的几种工作经验
        for field in workyear:
            workYear.append(field[0])
        # 获取到每种工作经验对应的个数
        for i in workYear:
            cursor.execute(
                "SELECT count(*) from demo where workYear = '" + i + "' and city = '上海';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': i})

        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '上海';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 250})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute(
                "SELECT count(*) from demo where financeStage = '" + finance[i] + "' and city = '上海';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])

        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '上海';")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)

        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '上海';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            for i in field.keys():
                firstType.append(field[i])

        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and city = '上海';")
            count = cursor.fetchall()
            for field in count:
                for j in field.keys():
                    value = field[j]

            firstType_data.append({'value': value, 'name': firstType[i]})

        # 薪资待遇
        positionName = ['java', 'python', 'php', 'web', 'bi',
                        'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(
            ['product', 'Java', 'Python', 'PHP', 'web', 'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" + i + "%' and city = '上海';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(
            ['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4], temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and city = '上海';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and city = '上海';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and city = '上海';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and city = '上海';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])

    else:
        positionName = str(request.args['positionName']).lower()
        print(positionName)
        # 查询条件：某种职业
        # 行政区
        for i in district:
            if i is None:
                continue
            cursor.execute("SELECT count(*) from demo where district = '" +
                           i + "' and positionName like '%"+positionName+"%';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)
        # 公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '上海';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and positionName like '%"+positionName+"%' and city = '上海';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)
        # 学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '上海';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            cursor.execute("SELECT count(*) from demo where education = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '上海';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)
        # 工作经验
        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '上海';")
        workyear = cursor.fetchall()
        for field in workyear:
            workYear.append(field[0])
            cursor.execute("SELECT count(*) from demo where workYear = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '上海';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': field[0]})
        # 融资阶段
        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '上海';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 250})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute("SELECT count(*) from demo where financeStage = '" +
                           finance[i] + "' and positionName like '%" + positionName + "%' and city = '上海';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])
        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '上海';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            firstType.append(field[0])
        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and positionName like '%" + positionName + "%' and city = '上海';")
            count = cursor.fetchall()
            firstType_data.append({'value': count[0][0], 'name': firstType[i]})
        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '上海' and positionName like '%" + positionName + "%' ;")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)
        # 薪资待遇
        positionName_sample = ['java', 'python', 'php', 'web',
                               'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(['product', 'Java', 'Python', 'PHP', 'web',
                        'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        # <10k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" +
                       positionName + "%' and city = '上海';")
        count = cursor.fetchall()
        # print(count)
        for i in count[0].keys():
            value = count[0][i]
        # print(value)
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # print(temp_list)
        # temp_list.append(value)
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 10-20k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" +
                       positionName + "%' and city = '上海';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 20-30k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" +
                       positionName + "%' and city = '上海';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 30-40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" +
                       positionName + "%' and city = '上海';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # >40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" +
                       positionName + "%' and city = '上海';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['>40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    print(zzt_list)
    result = {"district": district, "district_result": district_result, "companySize": companySize, "companySizeResult": companySizeResult, "education": education, "educationResult": educationResult,
              "workYear_data": workYear_data, "firstType": firstType, "firstType_data": firstType_data, "leida_max_dict": leida_max_dict, "cyt": positionAdvantage, "finance": finance, "finance_data": finance_data, "zzt": zzt_list}
    cursor.close()
    return jsonify(result)


@app.route('/guangzhou', methods=['GET'])
def guangzhou():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()

    district = []
    district_result = []
    companySize = []
    companySizeResult = []
    education = []
    educationResult = []
    workYear = []
    workYear_data = []
    firstType = []
    firstType_data = []
    finance = []
    finance_data = []
    leida_max_dict = []

    # 获取到的行政区
    cursor.execute("SELECT DISTINCT(district) from demo where city='广州';")
    result = cursor.fetchall()
    for field in result:
        district.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到行政区对应的个数
        for i in district:
            if i is None:  # 确保跳过None值
                continue
            try:
                # 使用参数化查询（推荐方式）
                cursor.execute(
                    "SELECT count(*) from demo where district = %s;",
                    (i,)
                )
                count = cursor.fetchone()[0]
                district_result.append({'value': count, 'name': i})
            except Exception as e:
                print(f"Error processing district {i}: {str(e)}")
                continue

        # 获取到几种公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '广州';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute(
                "SELECT count(*) from demo where companySize = '" + field[0] + "' and city = '广州';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)

        # 获取到几种学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '广州';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            # 每种学历要求对应的个数
            cursor.execute(
                "SELECT count(*) from demo where education = '" + field[0] + "' and city = '广州';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)

        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '广州';")
        workyear = cursor.fetchall()
        # 获取到的几种工作经验
        for field in workyear:
            workYear.append(field[0])
        # 获取到每种工作经验对应的个数
        for i in workYear:
            cursor.execute(
                "SELECT count(*) from demo where workYear = '" + i + "' and city = '广州';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': i})

        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '广州';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 150})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute(
                "SELECT count(*) from demo where financeStage = '" + finance[i] + "' and city = '广州';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])

        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '广州';")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)

        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '广州';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            for i in field.keys():
                firstType.append(field[i])

        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and city = '广州';")
            count = cursor.fetchall()
            for field in count:
                for j in field.keys():
                    value = field[j]

            firstType_data.append({'value': value, 'name': firstType[i]})

        # 薪资待遇
        positionName = ['java', 'python', 'php', 'web', 'bi',
                        'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(
            ['product', 'Java', 'Python', 'PHP', 'web', 'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" + i + "%' and city = '广州';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(
            ['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4], temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and city = '广州';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and city = '广州';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and city = '广州';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and city = '广州';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])

    else:
        positionName = str(request.args['positionName']).lower()
        # 查询条件：某种职业
        # 行政区
        for i in district:
            if i is None:
                continue
            cursor.execute("SELECT count(*) from demo where district = '" +
                           i + "' and positionName like '%"+positionName+"%';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)
        # 公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '广州';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and positionName like '%"+positionName+"%' and city = '广州';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)
        # 学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '广州';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            cursor.execute("SELECT count(*) from demo where education = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '广州';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)
        # 工作经验
        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '广州';")
        workyear = cursor.fetchall()
        for field in workyear:
            workYear.append(field[0])
            cursor.execute("SELECT count(*) from demo where workYear = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '广州';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': field[0]})
        # 融资阶段
        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '广州';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 150})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute("SELECT count(*) from demo where financeStage = '" +
                           finance[i] + "' and positionName like '%" + positionName + "%' and city = '广州';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])
        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '广州';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            firstType.append(field[0])
        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and positionName like '%" + positionName + "%' and city = '广州';")
            count = cursor.fetchall()
            firstType_data.append({'value': count[0][0], 'name': firstType[i]})
        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '广州' and positionName like '%" + positionName + "%' ;")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)
        # 薪资待遇
        positionName_sample = ['java', 'python', 'php', 'web', 'bi',
                               'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(['product', 'Java', 'Python', 'PHP', 'web',
                        'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        # <10k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" +
                       positionName + "%' and city = '广州';")
        count = cursor.fetchall()
        # print(count)
        for i in count[0].keys():
            value = count[0][i]
        # print(value)
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # print(temp_list)
        # temp_list.append(value)
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 10-20k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" +
                       positionName + "%' and city = '广州';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 20-30k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" +
                       positionName + "%' and city = '广州';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 30-40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" +
                       positionName + "%' and city = '广州';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # >40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" +
                       positionName + "%' and city = '广州';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['>40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    print(zzt_list)
    result = {"district": district, "district_result": district_result, "companySize": companySize, "companySizeResult": companySizeResult, "education": education, "educationResult": educationResult,
              "workYear_data": workYear_data, "firstType": firstType, "firstType_data": firstType_data, "leida_max_dict": leida_max_dict, "cyt": positionAdvantage, "finance": finance, "finance_data": finance_data, "zzt": zzt_list}
    cursor.close()
    return jsonify(result)


@app.route('/hangzhou', methods=['GET'])
def hangzhou():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()

    district = []
    district_result = []
    companySize = []
    companySizeResult = []
    education = []
    educationResult = []
    workYear = []
    workYear_data = []
    firstType = []
    firstType_data = []
    finance = []
    finance_data = []
    leida_max_dict = []

    # 获取到的行政区
    cursor.execute("SELECT DISTINCT(district) from demo where city='杭州';")
    result = cursor.fetchall()
    for field in result:
        district.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到行政区对应的个数
        for i in district:
            if i is None:  # 如果 district 是 NULL，跳过
                continue
            cursor.execute(
                "SELECT count(*) from demo where district = '" + i + "';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)

        # 获取到几种公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '杭州';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute(
                "SELECT count(*) from demo where companySize = '" + field[0] + "' and city = '杭州';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)

        # 获取到几种学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '杭州';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            # 每种学历要求对应的个数
            cursor.execute(
                "SELECT count(*) from demo where education = '" + field[0] + "' and city = '杭州';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)

        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '杭州';")
        workyear = cursor.fetchall()
        # 获取到的几种工作经验
        for field in workyear:
            workYear.append(field[0])
        # 获取到每种工作经验对应的个数
        for i in workYear:
            cursor.execute(
                "SELECT count(*) from demo where workYear = '" + i + "' and city = '杭州';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': i})

        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '杭州';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 100})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute(
                "SELECT count(*) from demo where financeStage = '" + finance[i] + "' and city = '杭州';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])

        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '杭州';")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)

        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '杭州';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            for i in field.keys():
                firstType.append(field[i])

        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and city = '杭州';")
            count = cursor.fetchall()
            for field in count:
                for j in field.keys():
                    value = field[j]

            firstType_data.append({'value': value, 'name': firstType[i]})

        # 薪资待遇
        positionName = ['java', 'python', 'php', 'web', 'bi',
                        'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(
            ['product', 'Java', 'Python', 'PHP', 'web', 'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" + i + "%' and city = '杭州';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(
            ['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4], temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and city = '杭州';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and city = '杭州';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and city = '杭州';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and city = '杭州';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])

    else:
        positionName = str(request.args['positionName']).lower()
        # 查询条件：某种职业
        # 行政区
        for i in district:
            if i is None:
                continue
            cursor.execute("SELECT count(*) from demo where district = '" +
                           i + "' and positionName like '%"+positionName+"%';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)
        # 公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '杭州';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and positionName like '%"+positionName+"%' and city = '杭州';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)
        # 学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '杭州';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            cursor.execute("SELECT count(*) from demo where education = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '杭州';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)
        # 工作经验
        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '杭州';")
        workyear = cursor.fetchall()
        for field in workyear:
            workYear.append(field[0])
            cursor.execute("SELECT count(*) from demo where workYear = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '杭州';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': field[0]})
        # 融资阶段
        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '杭州';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 100})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute("SELECT count(*) from demo where financeStage = '" +
                           finance[i] + "' and positionName like '%" + positionName + "%' and city = '杭州';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])
        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '杭州';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            firstType.append(field[0])
        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and positionName like '%" + positionName + "%' and city = '杭州';")
            count = cursor.fetchall()
            firstType_data.append({'value': count[0][0], 'name': firstType[i]})
        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '杭州' and positionName like '%" + positionName + "%' ;")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)
        # 薪资待遇
        positionName_sample = ['java', 'python', 'php', 'web', 'bi',
                               'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(['product', 'Java', 'Python', 'PHP', 'web',
                        'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        # <10k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" +
                       positionName + "%' and city = '杭州';")
        count = cursor.fetchall()
        # print(count)
        for i in count[0].keys():
            value = count[0][i]
        # print(value)
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # print(temp_list)
        # temp_list.append(value)
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 10-20k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" +
                       positionName + "%' and city = '杭州';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 20-30k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" +
                       positionName + "%' and city = '杭州';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 30-40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" +
                       positionName + "%' and city = '杭州';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # >40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" +
                       positionName + "%' and city = '杭州';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['>40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    print(zzt_list)
    result = {"district": district, "district_result": district_result, "companySize": companySize, "companySizeResult": companySizeResult, "education": education, "educationResult": educationResult,
              "workYear_data": workYear_data, "firstType": firstType, "firstType_data": firstType_data, "leida_max_dict": leida_max_dict, "cyt": positionAdvantage, "finance": finance, "finance_data": finance_data, "zzt": zzt_list}
    cursor.close()
    return jsonify(result)


@app.route('/shenzhen', methods=['GET'])
def shenzhen():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()

    district = []
    district_result = []
    companySize = []
    companySizeResult = []
    education = []
    educationResult = []
    workYear = []
    workYear_data = []
    firstType = []
    firstType_data = []
    finance = []
    finance_data = []
    leida_max_dict = []

    # 获取到的行政区
    cursor.execute("SELECT DISTINCT(district) from demo where city='深圳';")
    result = cursor.fetchall()
    for field in result:
        district.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到行政区对应的个数
        for i in district:
            if i is None:  # 如果 district 是 NULL，跳过
                continue
            cursor.execute(
                "SELECT count(*) from demo where district = '" + i + "';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)

        # 获取到几种公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '深圳';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute(
                "SELECT count(*) from demo where companySize = '" + field[0] + "' and city = '深圳';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)

        # 获取到几种学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '深圳';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            # 每种学历要求对应的个数
            cursor.execute(
                "SELECT count(*) from demo where education = '" + field[0] + "' and city = '深圳';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)

        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '深圳';")
        workyear = cursor.fetchall()
        # 获取到的几种工作经验
        for field in workyear:
            workYear.append(field[0])
        # 获取到每种工作经验对应的个数
        for i in workYear:
            cursor.execute(
                "SELECT count(*) from demo where workYear = '" + i + "' and city = '深圳';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': i})

        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '深圳';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 300})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute(
                "SELECT count(*) from demo where financeStage = '" + finance[i] + "' and city = '深圳';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])

        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '深圳';")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)

        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '深圳';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            for i in field.keys():
                firstType.append(field[i])

        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and city = '深圳';")
            count = cursor.fetchall()
            for field in count:
                for j in field.keys():
                    value = field[j]

            firstType_data.append({'value': value, 'name': firstType[i]})

        # 薪资待遇
        positionName = ['java', 'python', 'php', 'web', 'bi',
                        'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(
            ['product', 'Java', 'Python', 'PHP', 'web', 'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" + i + "%' and city = '深圳';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(
            ['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4], temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and city = '深圳';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and city = '深圳';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and city = '深圳';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and city = '深圳';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])

    else:
        positionName = str(request.args['positionName']).lower()
        # 查询条件：某种职业
        # 行政区
        for i in district:
            if i is None:
                continue
            cursor.execute("SELECT count(*) from demo where district = '" +
                           i + "' and positionName like '%"+positionName+"%';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)
        # 公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '深圳';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and positionName like '%"+positionName+"%' and city = '深圳';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)
        # 学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '深圳';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            cursor.execute("SELECT count(*) from demo where education = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '深圳';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)
        # 工作经验
        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '深圳';")
        workyear = cursor.fetchall()
        for field in workyear:
            workYear.append(field[0])
            cursor.execute("SELECT count(*) from demo where workYear = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '深圳';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': field[0]})
        # 融资阶段
        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '深圳';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 300})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute("SELECT count(*) from demo where financeStage = '" +
                           finance[i] + "' and positionName like '%" + positionName + "%' and city = '深圳';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])
        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '深圳';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            firstType.append(field[0])
        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and positionName like '%" + positionName + "%' and city = '深圳';")
            count = cursor.fetchall()
            firstType_data.append({'value': count[0][0], 'name': firstType[i]})
        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '深圳' and positionName like '%" + positionName + "%' ;")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)
        # 薪资待遇
        positionName_sample = ['java', 'python', 'php', 'web', 'bi',
                               'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(['product', 'Java', 'Python', 'PHP', 'web',
                        'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        # <10k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" +
                       positionName + "%' and city = '深圳';")
        count = cursor.fetchall()
        # print(count)
        for i in count[0].keys():
            value = count[0][i]
        # print(value)
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # print(temp_list)
        # temp_list.append(value)
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 10-20k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" +
                       positionName + "%' and city = '深圳';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 20-30k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" +
                       positionName + "%' and city = '深圳';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 30-40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" +
                       positionName + "%' and city = '深圳';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # >40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" +
                       positionName + "%' and city = '深圳';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['>40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    print(zzt_list)
    result = {"district": district, "district_result": district_result, "companySize": companySize, "companySizeResult": companySizeResult, "education": education, "educationResult": educationResult,
              "workYear_data": workYear_data, "firstType": firstType, "firstType_data": firstType_data, "leida_max_dict": leida_max_dict, "cyt": positionAdvantage, "finance": finance, "finance_data": finance_data, "zzt": zzt_list}
    cursor.close()
    return jsonify(result)


@app.route('/nanjing', methods=['GET'])
def nanjing():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()

    district = []
    district_result = []
    companySize = []
    companySizeResult = []
    education = []
    educationResult = []
    workYear = []
    workYear_data = []
    firstType = []
    firstType_data = []
    finance = []
    finance_data = []
    leida_max_dict = []

    # 获取到的行政区
    cursor.execute("SELECT DISTINCT(district) from demo where city='南京';")
    result = cursor.fetchall()
    for field in result:
        district.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到行政区对应的个数
        for i in district:
            cursor.execute(
                "SELECT count(*) from demo where district = '" + i + "';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)

        # 获取到几种公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '南京';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute(
                "SELECT count(*) from demo where companySize = '" + field[0] + "' and city = '南京';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)

        # 获取到几种学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '南京';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            # 每种学历要求对应的个数
            cursor.execute(
                "SELECT count(*) from demo where education = '" + field[0] + "' and city = '南京';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)

        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '南京';")
        workyear = cursor.fetchall()
        # 获取到的几种工作经验
        for field in workyear:
            workYear.append(field[0])
        # 获取到每种工作经验对应的个数
        for i in workYear:
            cursor.execute(
                "SELECT count(*) from demo where workYear = '" + i + "' and city = '南京';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': i})

        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '南京';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 10})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute(
                "SELECT count(*) from demo where financeStage = '" + finance[i] + "' and city = '南京';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])

        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '南京';")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)

        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '南京';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            for i in field.keys():
                firstType.append(field[i])

        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and city = '南京';")
            count = cursor.fetchall()
            for field in count:
                for j in field.keys():
                    value = field[j]

            firstType_data.append({'value': value, 'name': firstType[i]})

        # 薪资待遇
        positionName = ['java', 'python', 'php', 'web', 'bi',
                        'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(
            ['product', 'Java', 'Python', 'PHP', 'web', 'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" + i + "%' and city = '南京';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(
            ['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4], temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and city = '南京';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and city = '南京';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and city = '南京';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and city = '南京';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])

    else:
        positionName = str(request.args['positionName']).lower()
        # 查询条件：某种职业
        # 行政区
        for i in district:
            if i is None:
                continue
            cursor.execute("SELECT count(*) from demo where district = '" +
                           i + "' and positionName like '%"+positionName+"%';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)
        # 公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '南京';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and positionName like '%"+positionName+"%' and city = '南京';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)
        # 学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '南京';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            cursor.execute("SELECT count(*) from demo where education = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '南京';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)
        # 工作经验
        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '南京';")
        workyear = cursor.fetchall()
        for field in workyear:
            workYear.append(field[0])
            cursor.execute("SELECT count(*) from demo where workYear = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '南京';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': field[0]})
        # 融资阶段
        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '南京';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 10})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute("SELECT count(*) from demo where financeStage = '" +
                           finance[i] + "' and positionName like '%" + positionName + "%' and city = '南京';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])
        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '南京';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            firstType.append(field[0])
        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and positionName like '%" + positionName + "%' and city = '南京';")
            count = cursor.fetchall()
            firstType_data.append({'value': count[0][0], 'name': firstType[i]})
        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '南京' and positionName like '%" + positionName + "%' ;")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)
        # 薪资待遇
        positionName_sample = ['java', 'python', 'php', 'web', 'bi',
                               'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(['product', 'Java', 'Python', 'PHP', 'web',
                        'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        # <10k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" +
                       positionName + "%' and city = '南京';")
        count = cursor.fetchall()
        # print(count)
        for i in count[0].keys():
            value = count[0][i]
        # print(value)
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # print(temp_list)
        # temp_list.append(value)
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 10-20k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" +
                       positionName + "%' and city = '南京';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 20-30k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" +
                       positionName + "%' and city = '南京';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 30-40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" +
                       positionName + "%' and city = '南京';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # >40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" +
                       positionName + "%' and city = '南京';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['>40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    print(zzt_list)
    result = {"district": district, "district_result": district_result, "companySize": companySize, "companySizeResult": companySizeResult, "education": education, "educationResult": educationResult,
              "workYear_data": workYear_data, "firstType": firstType, "firstType_data": firstType_data, "leida_max_dict": leida_max_dict, "cyt": positionAdvantage, "finance": finance, "finance_data": finance_data, "zzt": zzt_list}
    cursor.close()
    return jsonify(result)


@app.route('/xian', methods=['GET'])
def xian():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()

    district = []
    district_result = []
    companySize = []
    companySizeResult = []
    education = []
    educationResult = []
    workYear = []
    workYear_data = []
    firstType = []
    firstType_data = []
    finance = []
    finance_data = []
    leida_max_dict = []

    # 获取到的行政区
    cursor.execute("SELECT DISTINCT(district) from demo where city='西安';")
    result = cursor.fetchall()
    for field in result:
        district.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到行政区对应的个数
        for i in district:
            if i is None:
                continue
            cursor.execute(
                "SELECT count(*) from demo where district = '" + i + "';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)

        # 获取到几种公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '西安';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute(
                "SELECT count(*) from demo where companySize = '" + field[0] + "' and city = '西安';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)

        # 获取到几种学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '西安';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            # 每种学历要求对应的个数
            cursor.execute(
                "SELECT count(*) from demo where education = '" + field[0] + "' and city = '西安';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)

        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '西安';")
        workyear = cursor.fetchall()
        # 获取到的几种工作经验
        for field in workyear:
            workYear.append(field[0])
        # 获取到每种工作经验对应的个数
        for i in workYear:
            cursor.execute(
                "SELECT count(*) from demo where workYear = '" + i + "' and city = '西安';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': i})

        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '西安';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 20})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute(
                "SELECT count(*) from demo where financeStage = '" + finance[i] + "' and city = '西安';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])

        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '西安';")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)

        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '西安';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            for i in field.keys():
                firstType.append(field[i])

        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and city = '西安';")
            count = cursor.fetchall()
            for field in count:
                for j in field.keys():
                    value = field[j]

            firstType_data.append({'value': value, 'name': firstType[i]})

        # 薪资待遇
        positionName = ['java', 'python', 'php', 'web', 'bi',
                        'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(
            ['product', 'Java', 'Python', 'PHP', 'web', 'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" + i + "%' and city = '西安';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(
            ['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4], temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and city = '西安';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and city = '西安';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and city = '西安';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and city = '西安';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])

    else:
        positionName = str(request.args['positionName']).lower()
        # 查询条件：某种职业
        # 行政区
        for i in district:
            cursor.execute("SELECT count(*) from demo where district = '" +
                           i + "' and positionName like '%"+positionName+"%';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)
        # 公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '西安';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and positionName like '%"+positionName+"%' and city = '西安';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)
        # 学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '西安';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            cursor.execute("SELECT count(*) from demo where education = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '西安';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)
        # 工作经验
        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '西安';")
        workyear = cursor.fetchall()
        for field in workyear:
            workYear.append(field[0])
            cursor.execute("SELECT count(*) from demo where workYear = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '西安';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': field[0]})
        # 融资阶段
        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '西安';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 20})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute("SELECT count(*) from demo where financeStage = '" +
                           finance[i] + "' and positionName like '%" + positionName + "%' and city = '西安';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])
        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '西安';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            firstType.append(field[0])
        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and positionName like '%" + positionName + "%' and city = '西安';")
            count = cursor.fetchall()
            firstType_data.append({'value': count[0][0], 'name': firstType[i]})
        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '西安' and positionName like '%" + positionName + "%' ;")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)
        # 薪资待遇
        positionName_sample = ['java', 'python', 'php', 'web', 'bi',
                               'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(['product', 'Java', 'Python', 'PHP', 'web',
                        'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        # <10k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" +
                       positionName + "%' and city = '西安';")
        count = cursor.fetchall()
        # print(count)
        for i in count[0].keys():
            value = count[0][i]
        # print(value)
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # print(temp_list)
        # temp_list.append(value)
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 10-20k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" +
                       positionName + "%' and city = '西安';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 20-30k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" +
                       positionName + "%' and city = '西安';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 30-40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" +
                       positionName + "%' and city = '西安';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # >40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" +
                       positionName + "%' and city = '西安';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['>40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    print(zzt_list)
    result = {"district": district, "district_result": district_result, "companySize": companySize, "companySizeResult": companySizeResult, "education": education, "educationResult": educationResult,
              "workYear_data": workYear_data, "firstType": firstType, "firstType_data": firstType_data, "leida_max_dict": leida_max_dict, "cyt": positionAdvantage, "finance": finance, "finance_data": finance_data, "zzt": zzt_list}
    cursor.close()
    return jsonify(result)


@app.route('/chengdu', methods=['GET'])
def chengdu():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()

    district = []
    district_result = []
    companySize = []
    companySizeResult = []
    education = []
    educationResult = []
    workYear = []
    workYear_data = []
    firstType = []
    firstType_data = []
    finance = []
    finance_data = []
    leida_max_dict = []

    # 获取到的行政区
    cursor.execute("SELECT DISTINCT(district) from demo where city='成都';")
    result = cursor.fetchall()
    for field in result:
        district.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到行政区对应的个数
        for i in district:
            if i is None:  # 如果 district 是 NULL，跳过
                continue
            cursor.execute(
                "SELECT count(*) from demo where district = '" + i + "';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)

        # 获取到几种公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '成都';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute(
                "SELECT count(*) from demo where companySize = '" + field[0] + "' and city = '成都';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)

        # 获取到几种学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '成都';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            # 每种学历要求对应的个数
            cursor.execute(
                "SELECT count(*) from demo where education = '" + field[0] + "' and city = '成都';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)

        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '成都';")
        workyear = cursor.fetchall()
        # 获取到的几种工作经验
        for field in workyear:
            workYear.append(field[0])
        # 获取到每种工作经验对应的个数
        for i in workYear:
            cursor.execute(
                "SELECT count(*) from demo where workYear = '" + i + "' and city = '成都';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': i})

        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '成都';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 120})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute(
                "SELECT count(*) from demo where financeStage = '" + finance[i] + "' and city = '成都';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])

        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '成都';")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)

        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '成都';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            for i in field.keys():
                firstType.append(field[i])

        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and city = '成都';")
            count = cursor.fetchall()
            for field in count:
                for j in field.keys():
                    value = field[j]

            firstType_data.append({'value': value, 'name': firstType[i]})

        # 薪资待遇
        positionName = ['java', 'python', 'php', 'web', 'bi',
                        'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(
            ['product', 'Java', 'Python', 'PHP', 'web', 'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" + i + "%' and city = '成都';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(
            ['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4], temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and city = '成都';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and city = '成都';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and city = '成都';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and city = '成都';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])

    else:
        positionName = str(request.args['positionName']).lower()
        # 查询条件：某种职业
        # 行政区
        for i in district:
            if i is None:
                continue
            cursor.execute("SELECT count(*) from demo where district = '" +
                           i + "' and positionName like '%"+positionName+"%';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)
        # 公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '成都';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and positionName like '%"+positionName+"%' and city = '成都';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)
        # 学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '成都';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            cursor.execute("SELECT count(*) from demo where education = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '成都';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)
        # 工作经验
        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '成都';")
        workyear = cursor.fetchall()
        for field in workyear:
            workYear.append(field[0])
            cursor.execute("SELECT count(*) from demo where workYear = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '成都';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': field[0]})
        # 融资阶段
        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '成都';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 120})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute("SELECT count(*) from demo where financeStage = '" +
                           finance[i] + "' and positionName like '%" + positionName + "%' and city = '成都';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])
        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '成都';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            firstType.append(field[0])
        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and positionName like '%" + positionName + "%' and city = '成都';")
            count = cursor.fetchall()
            firstType_data.append({'value': count[0][0], 'name': firstType[i]})
        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '成都' and positionName like '%" + positionName + "%' ;")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)
        # 薪资待遇
        positionName_sample = ['java', 'python', 'php', 'web', 'bi',
                               'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(['product', 'Java', 'Python', 'PHP', 'web',
                        'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        # <10k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" +
                       positionName + "%' and city = '成都';")
        count = cursor.fetchall()
        # print(count)
        for i in count[0].keys():
            value = count[0][i]
        # print(value)
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # print(temp_list)
        # temp_list.append(value)
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 10-20k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" +
                       positionName + "%' and city = '成都';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 20-30k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" +
                       positionName + "%' and city = '成都';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 30-40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" +
                       positionName + "%' and city = '成都';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # >40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" +
                       positionName + "%' and city = '成都';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['>40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    print(zzt_list)
    result = {"district": district, "district_result": district_result, "companySize": companySize, "companySizeResult": companySizeResult, "education": education, "educationResult": educationResult,
              "workYear_data": workYear_data, "firstType": firstType, "firstType_data": firstType_data, "leida_max_dict": leida_max_dict, "cyt": positionAdvantage, "finance": finance, "finance_data": finance_data, "zzt": zzt_list}
    cursor.close()
    return jsonify(result)


@app.route('/wuhan', methods=['GET'])
def wuhan():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()

    district = []
    district_result = []
    companySize = []
    companySizeResult = []
    education = []
    educationResult = []
    workYear = []
    workYear_data = []
    firstType = []
    firstType_data = []
    finance = []
    finance_data = []
    leida_max_dict = []

    # 获取到的行政区
    cursor.execute("SELECT DISTINCT(district) from demo where city='武汉';")
    result = cursor.fetchall()
    for field in result:
        district.append(field[0])
    if (len(request.args) == 0):
        # 没有查询条件
        # 获取到行政区对应的个数
        for i in district:
            cursor.execute(
                "SELECT count(*) from demo where district = '" + i + "';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)

        # 获取到几种公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '武汉';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            # 每种公司规模对应的个数
            cursor.execute(
                "SELECT count(*) from demo where companySize = '" + field[0] + "' and city = '武汉';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)

        # 获取到几种学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '武汉';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            # 每种学历要求对应的个数
            cursor.execute(
                "SELECT count(*) from demo where education = '" + field[0] + "' and city = '武汉';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)

        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '武汉';")
        workyear = cursor.fetchall()
        # 获取到的几种工作经验
        for field in workyear:
            workYear.append(field[0])
        # 获取到每种工作经验对应的个数
        for i in workYear:
            cursor.execute(
                "SELECT count(*) from demo where workYear = '" + i + "' and city = '武汉';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': i})

        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '武汉';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 40})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute(
                "SELECT count(*) from demo where financeStage = '" + finance[i] + "' and city = '武汉';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])

        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '武汉';")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)

        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '武汉';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            for i in field.keys():
                firstType.append(field[i])

        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and city = '武汉';")
            count = cursor.fetchall()
            for field in count:
                for j in field.keys():
                    value = field[j]

            firstType_data.append({'value': value, 'name': firstType[i]})

        # 薪资待遇
        positionName = ['java', 'python', 'php', 'web', 'bi',
                        'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']
        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(
            ['product', 'Java', 'Python', 'PHP', 'web', 'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" + i + "%' and city = '武汉';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(
            ['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4], temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" + i + "%' and city = '武汉';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" + i + "%' and city = '武汉';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" + i + "%' and city = '武汉';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        temp_list = []
        for i in positionName:
            cursor.execute(
                "SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" + i + "%' and city = '武汉';")
            count = cursor.fetchall()
            for i in count[0].keys():
                value = count[0][i]
            temp_list.append(value)
        zzt_list.append(['40以上', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])

    else:
        positionName = str(request.args['positionName']).lower()
        # 查询条件：某种职业
        # 行政区
        for i in district:
            if i is None:
                continue
            cursor.execute("SELECT count(*) from demo where district = '" +
                           i + "' and positionName like '%"+positionName+"%';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': i}
            district_result.append(dict)
        # 公司规模
        cursor.execute(
            "SELECT DISTINCT(companySize) from demo where city = '武汉';")
        company = cursor.fetchall()
        for field in company:
            companySize.append(field[0])
            cursor.execute("SELECT count(*) from demo where companySize = '" +
                           field[0] + "' and positionName like '%"+positionName+"%' and city = '武汉';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            companySizeResult.append(dict)
        # 学历要求
        cursor.execute(
            "SELECT DISTINCT(education) from demo where city = '武汉';")
        eduresult = cursor.fetchall()
        for field in eduresult:
            education.append(field[0])
            cursor.execute("SELECT count(*) from demo where education = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '武汉';")
            count = cursor.fetchall()
            dict = {'value': count[0][0], 'name': field[0]}
            educationResult.append(dict)
        # 工作经验
        cursor.execute(
            "SELECT DISTINCT(workYear) from demo where city = '武汉';")
        workyear = cursor.fetchall()
        for field in workyear:
            workYear.append(field[0])
            cursor.execute("SELECT count(*) from demo where workYear = '" +
                           field[0] + "' and positionName like '%" + positionName + "%' and city = '武汉';")
            count = cursor.fetchall()
            workYear_data.append({'value': count[0][0], 'name': field[0]})
        # 融资阶段
        cursor.execute(
            "SELECT DISTINCT(financeStage) from demo where city = '武汉';")
        result = cursor.fetchall()
        # 获取到融资的几种情况
        for field in result:
            finance.append(field[0])
            leida_max_dict.append({'name': field[0], 'max': 40})
        # 获取到每种融资对应的个数
        for i in range(len(finance)):
            cursor.execute("SELECT count(*) from demo where financeStage = '" +
                           finance[i] + "' and positionName like '%" + positionName + "%' and city = '武汉';")
            count = cursor.fetchall()
            finance_data.append(count[0][0])
        # 职位类型
        cursor.execute(
            "SELECT DISTINCT(firstType) from demo where city = '武汉';")
        result = cursor.fetchall()
        # 获取到职位类型的几种情况
        for field in result:
            firstType.append(field[0])
        # 获取到每种职位类型对应的个数
        for i in range(len(firstType)):
            cursor.execute("SELECT count(*) from demo where firstType = '" +
                           firstType[i] + "' and positionName like '%" + positionName + "%' and city = '武汉';")
            count = cursor.fetchall()
            firstType_data.append({'value': count[0][0], 'name': firstType[i]})
        # 职位福利
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(
            "select positionAdvantage from `demo` where city = '武汉' and positionName like '%" + positionName + "%' ;")
        data_dict = []
        result = cursor.fetchall()
        for field in result:
            data_dict.append(field['positionAdvantage'])
        content = ''.join(data_dict)
        positionAdvantage = []
        jieba.analyse.set_stop_words('./stopwords.txt')
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=True)
        for v, n in tags:
            mydict = {}
            mydict["name"] = v
            mydict["value"] = str(int(n * 10000))
            positionAdvantage.append(mydict)
        # 薪资待遇
        positionName_sample = ['java', 'python', 'php', 'web', 'bi',
                               'android', 'ios', '算法', '大数据', '测试', '运维', '数据库']        # 柱状图返回列表
        zzt_list = []
        zzt_list.append(['product', 'Java', 'Python', 'PHP', 'web',
                        'bi', 'android', 'ios', '算法', '大数据', '测试', '运维', '数据库'])
        # <10k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) like '%k%' and positionName like '%" +
                       positionName + "%' and city = '武汉';")
        count = cursor.fetchall()
        # print(count)
        for i in count[0].keys():
            value = count[0][i]
        # print(value)
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # print(temp_list)
        # temp_list.append(value)
        zzt_list.append(['0—10K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 10-20k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 10 AND 20 and positionName like '%" +
                       positionName + "%' and city = '武汉';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['10—20K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 20-30k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 20 AND 30 and positionName like '%" +
                       positionName + "%' and city = '武汉';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['20—30K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # 30-40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) BETWEEN 30 AND 40 and positionName like '%" +
                       positionName + "%' and city = '武汉';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['30—40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
        # >40k
        temp_list = []
        cursor.execute("SELECT COUNT(*) FROM demo WHERE SUBSTR(salary,1,2) > 40 and positionName like '%" +
                       positionName + "%' and city = '武汉';")
        count = cursor.fetchall()
        for i in count[0].keys():
            value = count[0][i]
        for num in range(len(positionName_sample)):
            if positionName == positionName_sample[num]:
                temp_list.append(value)
            else:
                temp_list.append(0)
        # temp_list.append(value)
        zzt_list.append(['>40K', temp_list[0], temp_list[1], temp_list[2], temp_list[3], temp_list[4],
                        temp_list[5], temp_list[6], temp_list[7], temp_list[8], temp_list[9], temp_list[10], temp_list[11]])
    print(zzt_list)
    result = {"district": district, "district_result": district_result, "companySize": companySize, "companySizeResult": companySizeResult, "education": education, "educationResult": educationResult,
              "workYear_data": workYear_data, "firstType": firstType, "firstType_data": firstType_data, "leida_max_dict": leida_max_dict, "cyt": positionAdvantage, "finance": finance, "finance_data": finance_data, "zzt": zzt_list}
    cursor.close()
    return jsonify(result)


@app.route('/area', methods=['GET'])
def area():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    #定义了一个列表 area_kind，其中包含了不同的房屋面积区间
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    #初始化一个空列表 area_data，用于存放每个面积区间对应的房屋数量
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute("SELECT count(*) from house where area between 0 and 20;")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 21~40㎡
    cursor.execute("SELECT count(*) from house where area between 21 and 40;")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 41~60㎡
    cursor.execute("SELECT count(*) from house where area between 41 and 60;")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 61~80㎡
    cursor.execute("SELECT count(*) from house where area between 61 and 80;")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 81~100㎡
    cursor.execute("SELECT count(*) from house where area between 81 and 100;")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120;")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140;")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160;")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180;")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200;")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    cursor.close()
    print(area_data)
    return jsonify({"area_kind": area_kind, "area_data": area_data})


@app.route('/area_first', methods=['GET'])
def area_first():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute(
        "SELECT count(*) from house where area between 0 and 20 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 21~40㎡
    cursor.execute(
        "SELECT count(*) from house where area between 21 and 40 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 41~60㎡
    cursor.execute(
        "SELECT count(*) from house where area between 41 and 60 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 61~80㎡
    cursor.execute(
        "SELECT count(*) from house where area between 61 and 80 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 81~100㎡
    cursor.execute(
        "SELECT count(*) from house where area between 81 and 100 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    cursor.close()
    print(area_data)
    return jsonify({"area_kind": area_kind, "area_data": area_data})


@app.route('/area_nfirst', methods=['GET'])
def area_nfirst():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute(
        "SELECT count(*) from house where area between 0 and 20 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 21~40㎡
    cursor.execute(
        "SELECT count(*) from house where area between 21 and 40 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 41~60㎡
    cursor.execute(
        "SELECT count(*) from house where area between 41 and 60 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 61~80㎡
    cursor.execute(
        "SELECT count(*) from house where area between 61 and 80 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 81~100㎡
    cursor.execute(
        "SELECT count(*) from house where area between 81 and 100 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    cursor.close()
    print(area_data)
    return jsonify({"area_kind": area_kind, "area_data": area_data})


@app.route('/area_second', methods=['GET'])
def area_second():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute(
        "SELECT count(*) from house where area between 0 and 20 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 21~40㎡
    cursor.execute(
        "SELECT count(*) from house where area between 21 and 40 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 41~60㎡
    cursor.execute(
        "SELECT count(*) from house where area between 41 and 60 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 61~80㎡
    cursor.execute(
        "SELECT count(*) from house where area between 61 and 80 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 81~100㎡
    cursor.execute(
        "SELECT count(*) from house where area between 81 and 100 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    area_data.append(count[0][0])
    cursor.close()
    print(area_data)
    return jsonify({"area_kind": area_kind, "area_data": area_data})


@app.route('/floor', methods=['GET'])
def floor():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT(floor) from house;")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute(
            "SELECT count(*) from house where floor = '" + floor_kind[i] + "'")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    cursor.close()
    return jsonify({"floor_kind": floor_kind, "floor_data": floor_data})


@app.route('/floor_first', methods=['GET'])
def floor_first():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT(floor) from house where city in ('北京','上海','深圳');")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute("SELECT count(*) from house where floor = '" +
                       floor_kind[i] + "' and city in ('北京','上海','深圳');")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    cursor.close()
    return jsonify({"floor_kind": floor_kind, "floor_data": floor_data})


@app.route('/floor_nfirst', methods=['GET'])
def floor_nfirst():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT(floor) from house where city in ('杭州','南京','武汉','西安','成都','重庆');")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute("SELECT count(*) from house where floor = '" +
                       floor_kind[i] + "' and city in ('杭州','南京','武汉','西安','成都','重庆');")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    cursor.close()
    return jsonify({"floor_kind": floor_kind, "floor_data": floor_data})


@app.route('/floor_second', methods=['GET'])
def floor_second():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT(floor) from house where city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute("SELECT count(*) from house where floor = '" +
                       floor_kind[i] + "' and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    cursor.close()
    return jsonify({"floor_kind": floor_kind, "floor_data": floor_data})


@app.route('/orient', methods=['GET'])
def orient():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT(orient) from house;")
    result = cursor.fetchall()
    orient_kind = []
    orient_data = []
    # 获取到朝向的几种情况
    for field in result:
        orient_kind.append(field[0])
    # 获取到每种朝向类型对应的个数
    for i in range(len(orient_kind)):
        cursor.execute(
            "SELECT count(*) from house where orient = '" + orient_kind[i] + "'")
        count = cursor.fetchall()
        orient_data.append({'value': count[0][0], 'name': orient_kind[i]})
    cursor.close()
    print(orient_data)
    return jsonify({"orient_kind": orient_kind, "orient_data": orient_data})


@app.route('/orient_first', methods=['GET'])
def orient_first():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT(orient) from house where city in ('北京','上海','深圳');")
    result = cursor.fetchall()
    orient_kind = []
    orient_data = []
    # 获取到朝向的几种情况
    for field in result:
        orient_kind.append(field[0])
    # 获取到每种朝向类型对应的个数
    for i in range(len(orient_kind)):
        cursor.execute("SELECT count(*) from house where orient = '" +
                       orient_kind[i] + "' and city in ('北京','上海','深圳');")
        count = cursor.fetchall()
        orient_data.append({'value': count[0][0], 'name': orient_kind[i]})
    cursor.close()
    print(orient_data)
    return jsonify({"orient_kind": orient_kind, "orient_data": orient_data})


@app.route('/orient_nfirst', methods=['GET'])
def orient_nfirst():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT(orient) from house where city in ('杭州','南京','武汉','西安','成都','重庆');")
    result = cursor.fetchall()
    orient_kind = []
    orient_data = []
    # 获取到朝向的几种情况
    for field in result:
        orient_kind.append(field[0])
    # 获取到每种朝向类型对应的个数
    for i in range(len(orient_kind)):
        cursor.execute("SELECT count(*) from house where orient = '" +
                       orient_kind[i] + "' and city in ('杭州','南京','武汉','西安','成都','重庆');")
        count = cursor.fetchall()
        orient_data.append({'value': count[0][0], 'name': orient_kind[i]})
    cursor.close()
    print(orient_data)
    return jsonify({"orient_kind": orient_kind, "orient_data": orient_data})


@app.route('/orient_second', methods=['GET'])
def orient_second():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT(orient) from house where city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    result = cursor.fetchall()
    orient_kind = []
    orient_data = []
    # 获取到朝向的几种情况
    for field in result:
        orient_kind.append(field[0])
    # 获取到每种朝向类型对应的个数
    for i in range(len(orient_kind)):
        cursor.execute("SELECT count(*) from house where orient = '" +
                       orient_kind[i] + "' and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
        count = cursor.fetchall()
        orient_data.append({'value': count[0][0], 'name': orient_kind[i]})
    cursor.close()
    print(orient_data)
    return jsonify({"orient_kind": orient_kind, "orient_data": orient_data})


@app.route('/price', methods=['GET'])
def price():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000',
                  '5001~6000', '6001~7000', '7001~8000', '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种价格类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000;")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000;")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000;")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000;")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000;")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000;")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000;")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000;")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000;")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000;")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # >10000
    cursor.execute("SELECT count(*) from house where price >10000;")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    cursor.close()
    print(price_data)
    return jsonify({"price_kind": price_kind, "price_data": price_data})


@app.route('/price_first', methods=['GET'])
def price_first():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000',
                  '5001~6000', '6001~7000', '7001~8000', '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种类别类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # >10000
    cursor.execute(
        "SELECT count(*) from house where price >10000 and city in ('北京','上海','深圳');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    cursor.close()
    print(price_data)
    return jsonify({"price_kind": price_kind, "price_data": price_data})


@app.route('/price_nfirst', methods=['GET'])
def price_nfirst():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000',
                  '5001~6000', '6001~7000', '7001~8000', '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种类别类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # >10000
    cursor.execute(
        "SELECT count(*) from house where price >10000 and city in ('杭州','南京','武汉','西安','成都','重庆');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    cursor.close()
    print(price_data)
    return jsonify({"price_kind": price_kind, "price_data": price_data})


@app.route('/price_second', methods=['GET'])
def price_second():
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    cursor = conn.cursor()
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000',
                  '5001~6000', '6001~7000', '7001~8000', '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种类别类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    # >10000
    cursor.execute(
        "SELECT count(*) from house where price >10000 and city in ('兰州','大连','贵阳','石家庄','太原','徐州');")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    cursor.close()
    print(price_data)
    return jsonify({"price_kind": price_kind, "price_data": price_data})


@app.route('/bj', methods=['GET'])
def bj():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor
    cursor = conn.cursor()
    # 行政区
    cursor.execute("SELECT DISTINCT(district) from house where city = '北京';")
    result = cursor.fetchall()
    district = []
    district_data = []
    for field in result:
        district.append(field[0])
    for i in range(len(district)):
        if district[i] is None:
            continue
        cursor.execute("SELECT count(*) from house where district = '" +
                       district[i] + "' and city = '北京';")
        count = cursor.fetchall()
        district_data.append({'value': count[0][0], 'name': district[i]})
    # 面积
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute(
        "SELECT count(*) from house where area between 0 and 20 and city = '北京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[0]})
    # 21~40㎡
    cursor.execute(
        "SELECT count(*) from house where area between 21 and 40 and city = '北京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[1]})
    # 41~60㎡
    cursor.execute(
        "SELECT count(*) from house where area between 41 and 60 and city = '北京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[2]})
    # 61~80㎡
    cursor.execute(
        "SELECT count(*) from house where area between 61 and 80 and city = '北京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[3]})
    # 81~100㎡
    cursor.execute(
        "SELECT count(*) from house where area between 81 and 100 and city = '北京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[4]})
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120 and city = '北京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[5]})
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140 and city = '北京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[6]})
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160 and city = '北京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[7]})
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180 and city = '北京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[8]})
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200 and city = '北京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[9]})
    # 楼层
    cursor.execute("SELECT DISTINCT(floor) from house where city = '北京';")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute("SELECT count(*) from house where floor = '" +
                       floor_kind[i] + "' and city = '北京';")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    # 价格
    max_dict = []
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000', '5001~6000', '6001~7000', '7001~8000',
                  '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种价格类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000 and city = '北京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[0], 'max': 500})
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000 and city = '北京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[1], 'max': 500})
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000 and city = '北京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[2], 'max': 500})
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000 and city = '北京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[3], 'max': 500})
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000 and city = '北京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[4], 'max': 500})
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000 and city = '北京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[5], 'max': 500})
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000 and city = '北京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[6], 'max': 500})
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000 and city = '北京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[7], 'max': 500})
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000 and city = '北京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[8], 'max': 500})
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000 and city = '北京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[9], 'max': 500})
    # >10000
    cursor.execute(
        "SELECT count(*) from house where price >10000 and city = '北京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[10], 'max': 500})

    cursor.close()
    return jsonify({"district": district, "district_data": district_data, "area_data": area_data, "floor_kind": floor_kind, "floor_data": floor_data,
                    "price_data": price_data, "max_dict": max_dict})


@app.route('/sh', methods=['GET'])
def sh():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor
    cursor = conn.cursor()
    # 行政区
    cursor.execute("SELECT DISTINCT(district) from house where city = '上海';")
    result = cursor.fetchall()
    district = []
    district_data = []
    for field in result:
        district.append(field[0])
    for i in range(len(district)):
        if district[i] is None:
            continue
        cursor.execute("SELECT count(*) from house where district = '" +
                       district[i] + "' and city = '上海';")
        count = cursor.fetchall()
        district_data.append({'value': count[0][0], 'name': district[i]})
    # 面积
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute(
        "SELECT count(*) from house where area between 0 and 20 and city = '上海';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[0]})
    # 21~40㎡
    cursor.execute(
        "SELECT count(*) from house where area between 21 and 40 and city = '上海';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[1]})
    # 41~60㎡
    cursor.execute(
        "SELECT count(*) from house where area between 41 and 60 and city = '上海';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[2]})
    # 61~80㎡
    cursor.execute(
        "SELECT count(*) from house where area between 61 and 80 and city = '上海';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[3]})
    # 81~100㎡
    cursor.execute(
        "SELECT count(*) from house where area between 81 and 100 and city = '上海';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[4]})
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120 and city = '上海';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[5]})
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140 and city = '上海';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[6]})
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160 and city = '上海';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[7]})
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180 and city = '上海';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[8]})
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200 and city = '上海';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[9]})
    # 楼层
    cursor.execute("SELECT DISTINCT(floor) from house where city = '上海';")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute("SELECT count(*) from house where floor = '" +
                       floor_kind[i] + "' and city = '上海';")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    # 价格
    max_dict = []
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000', '5001~6000', '6001~7000', '7001~8000',
                  '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种价格类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000 and city = '上海';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[0], 'max': 700})
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000 and city = '上海';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[1], 'max': 700})
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000 and city = '上海';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[2], 'max': 700})
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000 and city = '上海';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[3], 'max': 700})
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000 and city = '上海';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[4], 'max': 700})
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000 and city = '上海';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[5], 'max': 700})
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000 and city = '上海';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[6], 'max': 700})
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000 and city = '上海';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[7], 'max': 700})
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000 and city = '上海';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[8], 'max': 700})
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000 and city = '上海';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[9], 'max': 700})
    # >10000
    cursor.execute(
        "SELECT count(*) from house where price >10000 and city = '上海';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[10], 'max': 700})

    cursor.close()
    return jsonify({"district": district, "district_data": district_data, "area_data": area_data, "floor_kind": floor_kind, "floor_data": floor_data,
                    "price_data": price_data, "max_dict": max_dict})


@app.route('/sz', methods=['GET'])
def sz():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor
    cursor = conn.cursor()
    # 行政区
    cursor.execute("SELECT DISTINCT(district) from house where city = '深圳';")
    result = cursor.fetchall()
    district = []
    district_data = []
    for field in result:
        district.append(field[0])
    for i in range(len(district)):
        if district[i] is None:
            continue
        cursor.execute("SELECT count(*) from house where district = '" +
                       district[i] + "' and city = '深圳';")
        count = cursor.fetchall()
        district_data.append({'value': count[0][0], 'name': district[i]})
    # 面积
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute(
        "SELECT count(*) from house where area between 0 and 20 and city = '深圳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[0]})
    # 21~40㎡
    cursor.execute(
        "SELECT count(*) from house where area between 21 and 40 and city = '深圳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[1]})
    # 41~60㎡
    cursor.execute(
        "SELECT count(*) from house where area between 41 and 60 and city = '深圳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[2]})
    # 61~80㎡
    cursor.execute(
        "SELECT count(*) from house where area between 61 and 80 and city = '深圳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[3]})
    # 81~100㎡
    cursor.execute(
        "SELECT count(*) from house where area between 81 and 100 and city = '深圳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[4]})
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120 and city = '深圳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[5]})
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140 and city = '深圳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[6]})
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160 and city = '深圳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[7]})
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180 and city = '深圳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[8]})
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200 and city = '深圳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[9]})
    # 楼层
    cursor.execute("SELECT DISTINCT(floor) from house where city = '深圳';")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute("SELECT count(*) from house where floor = '" +
                       floor_kind[i] + "' and city = '深圳';")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    # 价格
    max_dict = []
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000', '5001~6000', '6001~7000', '7001~8000',
                  '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种价格类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000 and city = '深圳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[0], 'max': 400})
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000 and city = '深圳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[1], 'max': 400})
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000 and city = '深圳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[2], 'max': 400})
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000 and city = '深圳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[3], 'max': 400})
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000 and city = '深圳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[4], 'max': 400})
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000 and city = '深圳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[5], 'max': 400})
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000 and city = '深圳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[6], 'max': 400})
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000 and city = '深圳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[7], 'max': 400})
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000 and city = '深圳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[8], 'max': 400})
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000 and city = '深圳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[9], 'max': 400})
    # >10000
    cursor.execute(
        "SELECT count(*) from house where price >10000 and city = '深圳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[10], 'max': 400})

    cursor.close()
    return jsonify({"district": district, "district_data": district_data, "area_data": area_data, "floor_kind": floor_kind, "floor_data": floor_data,
                    "price_data": price_data, "max_dict": max_dict})


@app.route('/hz', methods=['GET'])
def hz():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor
    cursor = conn.cursor()
    # 行政区
    cursor.execute("SELECT DISTINCT(district) from house where city = '杭州';")
    result = cursor.fetchall()
    district = []
    district_data = []
    for field in result:
        district.append(field[0])
    for i in range(len(district)):
        if district[i] is None:
            continue
        cursor.execute("SELECT count(*) from house where district = '" +
                       district[i] + "' and city = '杭州';")
        count = cursor.fetchall()
        district_data.append({'value': count[0][0], 'name': district[i]})
    # 面积
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute(
        "SELECT count(*) from house where area between 0 and 20 and city = '杭州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[0]})
    # 21~40㎡
    cursor.execute(
        "SELECT count(*) from house where area between 21 and 40 and city = '杭州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[1]})
    # 41~60㎡
    cursor.execute(
        "SELECT count(*) from house where area between 41 and 60 and city = '杭州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[2]})
    # 61~80㎡
    cursor.execute(
        "SELECT count(*) from house where area between 61 and 80 and city = '杭州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[3]})
    # 81~100㎡
    cursor.execute(
        "SELECT count(*) from house where area between 81 and 100 and city = '杭州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[4]})
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120 and city = '杭州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[5]})
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140 and city = '杭州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[6]})
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160 and city = '杭州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[7]})
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180 and city = '杭州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[8]})
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200 and city = '杭州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[9]})
    # 楼层
    cursor.execute("SELECT DISTINCT(floor) from house where city = '杭州';")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute("SELECT count(*) from house where floor = '" +
                       floor_kind[i] + "' and city = '杭州';")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    # 价格
    max_dict = []
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000', '5001~6000', '6001~7000', '7001~8000',
                  '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种价格类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000 and city = '杭州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[0], 'max': 600})
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000 and city = '杭州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[1], 'max': 600})
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000 and city = '杭州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[2], 'max': 600})
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000 and city = '杭州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[3], 'max': 600})
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000 and city = '杭州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[4], 'max': 600})
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000 and city = '杭州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[5], 'max': 600})
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000 and city = '杭州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[6], 'max': 600})
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000 and city = '杭州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[7], 'max': 600})
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000 and city = '杭州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[8], 'max': 600})
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000 and city = '杭州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[9], 'max': 600})
    # >10000
    cursor.execute(
        "SELECT count(*) from house where price >10000 and city = '杭州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[10], 'max': 600})

    cursor.close()
    return jsonify({"district": district, "district_data": district_data, "area_data": area_data, "floor_kind": floor_kind, "floor_data": floor_data,
                    "price_data": price_data, "max_dict": max_dict})


@app.route('/wh', methods=['GET'])
def wh():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor
    cursor = conn.cursor()
    # 行政区
    cursor.execute("SELECT DISTINCT(district) from house where city = '武汉';")
    result = cursor.fetchall()
    district = []
    district_data = []
    for field in result:
        district.append(field[0])
    for i in range(len(district)):
        if district[i] is None:
            continue
        cursor.execute("SELECT count(*) from house where district = '" +
                       district[i] + "' and city = '武汉';")
        count = cursor.fetchall()
        district_data.append({'value': count[0][0], 'name': district[i]})
    # 面积
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute(
        "SELECT count(*) from house where area between 0 and 20 and city = '武汉';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[0]})
    # 21~40㎡
    cursor.execute(
        "SELECT count(*) from house where area between 21 and 40 and city = '武汉';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[1]})
    # 41~60㎡
    cursor.execute(
        "SELECT count(*) from house where area between 41 and 60 and city = '武汉';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[2]})
    # 61~80㎡
    cursor.execute(
        "SELECT count(*) from house where area between 61 and 80 and city = '武汉';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[3]})
    # 81~100㎡
    cursor.execute(
        "SELECT count(*) from house where area between 81 and 100 and city = '武汉';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[4]})
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120 and city = '武汉';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[5]})
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140 and city = '武汉';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[6]})
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160 and city = '武汉';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[7]})
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180 and city = '武汉';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[8]})
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200 and city = '武汉';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[9]})
    # 楼层
    cursor.execute("SELECT DISTINCT(floor) from house where city = '武汉';")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute("SELECT count(*) from house where floor = '" +
                       floor_kind[i] + "' and city = '武汉';")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    # 价格
    max_dict = []
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000', '5001~6000', '6001~7000', '7001~8000',
                  '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种价格类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000 and city = '武汉';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[0], 'max': 1000})
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000 and city = '武汉';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[1], 'max': 1000})
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000 and city = '武汉';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[2], 'max': 1000})
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000 and city = '武汉';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[3], 'max': 1000})
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000 and city = '武汉';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[4], 'max': 1000})
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000 and city = '武汉';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[5], 'max': 1000})
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000 and city = '武汉';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[6], 'max': 1000})
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000 and city = '武汉';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[7], 'max': 1000})
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000 and city = '武汉';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[8], 'max': 1000})
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000 and city = '武汉';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[9], 'max': 1000})
    # >10000
    cursor.execute(
        "SELECT count(*) from house where price >10000 and city = '武汉';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[10], 'max': 1000})

    cursor.close()
    return jsonify({"district": district, "district_data": district_data, "area_data": area_data, "floor_kind": floor_kind, "floor_data": floor_data,
                    "price_data": price_data, "max_dict": max_dict})


@app.route('/nj', methods=['GET'])
def nj():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor
    cursor = conn.cursor()
    # 行政区
    cursor.execute("SELECT DISTINCT(district) from house where city = '南京';")
    result = cursor.fetchall()
    district = []
    district_data = []
    for field in result:
        district.append(field[0])
    for i in range(len(district)):
        if district[i] is None:
            continue
        cursor.execute("SELECT count(*) from house where district = '" +
                       district[i] + "' and city = '南京';")
        count = cursor.fetchall()
        district_data.append({'value': count[0][0], 'name': district[i]})
    # 面积
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute(
        "SELECT count(*) from house where area between 0 and 20 and city = '南京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[0]})
    # 21~40㎡
    cursor.execute(
        "SELECT count(*) from house where area between 21 and 40 and city = '南京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[1]})
    # 41~60㎡
    cursor.execute(
        "SELECT count(*) from house where area between 41 and 60 and city = '南京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[2]})
    # 61~80㎡
    cursor.execute(
        "SELECT count(*) from house where area between 61 and 80 and city = '南京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[3]})
    # 81~100㎡
    cursor.execute(
        "SELECT count(*) from house where area between 81 and 100 and city = '南京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[4]})
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120 and city = '南京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[5]})
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140 and city = '南京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[6]})
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160 and city = '南京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[7]})
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180 and city = '南京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[8]})
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200 and city = '南京';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[9]})
    # 楼层
    cursor.execute("SELECT DISTINCT(floor) from house where city = '南京';")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute("SELECT count(*) from house where floor = '" +
                       floor_kind[i] + "' and city = '南京';")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    # 价格
    max_dict = []
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000', '5001~6000', '6001~7000', '7001~8000',
                  '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种价格类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000 and city = '南京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[0], 'max': 1000})
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000 and city = '南京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[1], 'max': 1000})
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000 and city = '南京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[2], 'max': 1000})
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000 and city = '南京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[3], 'max': 1000})
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000 and city = '南京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[4], 'max': 1000})
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000 and city = '南京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[5], 'max': 1000})
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000 and city = '南京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[6], 'max': 1000})
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000 and city = '南京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[7], 'max': 1000})
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000 and city = '南京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[8], 'max': 1000})
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000 and city = '南京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[9], 'max': 1000})
    # >10000
    cursor.execute(
        "SELECT count(*) from house where price >10000 and city = '南京';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[10], 'max': 1000})

    cursor.close()
    return jsonify({"district": district, "district_data": district_data, "area_data": area_data, "floor_kind": floor_kind, "floor_data": floor_data,
                    "price_data": price_data, "max_dict": max_dict})


@app.route('/lz', methods=['GET'])
def lz():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor
    cursor = conn.cursor()
    # 行政区
    cursor.execute("SELECT DISTINCT(district) from house where city = '兰州';")
    result = cursor.fetchall()
    district = []
    district_data = []
    for field in result:
        district.append(field[0])
    for i in range(len(district)):
        if district[i] is None:
            continue
        cursor.execute("SELECT count(*) from house where district = '" +
                       district[i] + "' and city = '兰州';")
        count = cursor.fetchall()
        district_data.append({'value': count[0][0], 'name': district[i]})
    # 面积
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute(
        "SELECT count(*) from house where area between 0 and 20 and city = '兰州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[0]})
    # 21~40㎡
    cursor.execute(
        "SELECT count(*) from house where area between 21 and 40 and city = '兰州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[1]})
    # 41~60㎡
    cursor.execute(
        "SELECT count(*) from house where area between 41 and 60 and city = '兰州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[2]})
    # 61~80㎡
    cursor.execute(
        "SELECT count(*) from house where area between 61 and 80 and city = '兰州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[3]})
    # 81~100㎡
    cursor.execute(
        "SELECT count(*) from house where area between 81 and 100 and city = '兰州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[4]})
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120 and city = '兰州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[5]})
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140 and city = '兰州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[6]})
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160 and city = '兰州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[7]})
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180 and city = '兰州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[8]})
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200 and city = '兰州';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[9]})
    # 楼层
    cursor.execute("SELECT DISTINCT(floor) from house where city = '兰州';")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute("SELECT count(*) from house where floor = '" +
                       floor_kind[i] + "' and city = '兰州';")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    # 价格
    max_dict = []
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000', '5001~6000', '6001~7000', '7001~8000',
                  '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种价格类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000 and city = '兰州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[0], 'max': 1200})
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000 and city = '兰州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[1], 'max': 1200})
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000 and city = '兰州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[2], 'max': 1200})
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000 and city = '兰州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[3], 'max': 1200})
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000 and city = '兰州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[4], 'max': 1200})
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000 and city = '兰州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[5], 'max': 1200})
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000 and city = '兰州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[6], 'max': 1200})
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000 and city = '兰州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[7], 'max': 1200})
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000 and city = '兰州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[8], 'max': 1200})
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000 and city = '兰州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[9], 'max': 1200})
    # >10000
    cursor.execute(
        "SELECT count(*) from house where price >10000 and city = '兰州';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[10], 'max': 1200})

    cursor.close()
    return jsonify({"district": district, "district_data": district_data, "area_data": area_data, "floor_kind": floor_kind, "floor_data": floor_data,
                    "price_data": price_data, "max_dict": max_dict})


@app.route('/gy', methods=['GET'])
def gy():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor
    cursor = conn.cursor()
    # 行政区
    cursor.execute("SELECT DISTINCT(district) from house where city = '贵阳';")
    result = cursor.fetchall()
    district = []
    district_data = []
    for field in result:
        district.append(field[0])
    for i in range(len(district)):
        if district[i] is None:
            continue
        cursor.execute("SELECT count(*) from house where district = '" +
                       district[i] + "' and city = '贵阳';")
        count = cursor.fetchall()
        district_data.append({'value': count[0][0], 'name': district[i]})
    # 面积
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute(
        "SELECT count(*) from house where area between 0 and 20 and city = '贵阳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[0]})
    # 21~40㎡
    cursor.execute(
        "SELECT count(*) from house where area between 21 and 40 and city = '贵阳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[1]})
    # 41~60㎡
    cursor.execute(
        "SELECT count(*) from house where area between 41 and 60 and city = '贵阳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[2]})
    # 61~80㎡
    cursor.execute(
        "SELECT count(*) from house where area between 61 and 80 and city = '贵阳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[3]})
    # 81~100㎡
    cursor.execute(
        "SELECT count(*) from house where area between 81 and 100 and city = '贵阳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[4]})
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120 and city = '贵阳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[5]})
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140 and city = '贵阳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[6]})
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160 and city = '贵阳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[7]})
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180 and city = '贵阳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[8]})
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200 and city = '贵阳';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[9]})
    # 楼层
    cursor.execute("SELECT DISTINCT(floor) from house where city = '贵阳';")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute("SELECT count(*) from house where floor = '" +
                       floor_kind[i] + "' and city = '贵阳';")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    # 价格
    max_dict = []
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000', '5001~6000', '6001~7000', '7001~8000',
                  '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种价格类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000 and city = '贵阳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[0], 'max': 1300})
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000 and city = '贵阳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[1], 'max': 1300})
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000 and city = '贵阳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[2], 'max': 1300})
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000 and city = '贵阳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[3], 'max': 1300})
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000 and city = '贵阳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[4], 'max': 1300})
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000 and city = '贵阳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[5], 'max': 1300})
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000 and city = '贵阳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[6], 'max': 1300})
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000 and city = '贵阳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[7], 'max': 1300})
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000 and city = '贵阳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[8], 'max': 1300})
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000 and city = '贵阳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[9], 'max': 1300})
    # >10000
    cursor.execute(
        "SELECT count(*) from house where price >10000 and city = '贵阳';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[10], 'max': 1300})

    cursor.close()
    return jsonify({"district": district, "district_data": district_data, "area_data": area_data, "floor_kind": floor_kind, "floor_data": floor_data,
                    "price_data": price_data, "max_dict": max_dict})


@app.route('/ty', methods=['GET'])
def ty():
    # 打开数据库连接
    conn = pymysql.connect(host='localhost', user='root', password='root', port=3306, db='lagou',
                           charset='utf8mb4')
    # 创建一个游标对象cursor
    cursor = conn.cursor()
    # 行政区
    cursor.execute("SELECT DISTINCT(district) from house where city = '太原';")
    result = cursor.fetchall()
    district = []
    district_data = []
    for field in result:
        district.append(field[0])
    for i in range(len(district)):
        if district[i] is None:
            continue
        cursor.execute("SELECT count(*) from house where district = '" +
                       district[i] + "' and city = '太原';")
        count = cursor.fetchall()
        district_data.append({'value': count[0][0], 'name': district[i]})
    # 面积
    area_kind = ['<=20㎡', '21~40㎡', '41~60㎡', '61~80㎡', '81~100㎡',
                 '101~120㎡', '121~140㎡', '141~160㎡', '161~180㎡', '181~200㎡']
    area_data = []
    # 获取到每种面积类别对应的个数
    # <=20㎡
    cursor.execute(
        "SELECT count(*) from house where area between 0 and 20 and city = '太原';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[0]})
    # 21~40㎡
    cursor.execute(
        "SELECT count(*) from house where area between 21 and 40 and city = '太原';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[1]})
    # 41~60㎡
    cursor.execute(
        "SELECT count(*) from house where area between 41 and 60 and city = '太原';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[2]})
    # 61~80㎡
    cursor.execute(
        "SELECT count(*) from house where area between 61 and 80 and city = '太原';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[3]})
    # 81~100㎡
    cursor.execute(
        "SELECT count(*) from house where area between 81 and 100 and city = '太原';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[4]})
    # 101~120㎡
    cursor.execute(
        "SELECT count(*) from house where area between 101 and 120 and city = '太原';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[5]})
    # 121~140㎡
    cursor.execute(
        "SELECT count(*) from house where area between 121 and 140 and city = '太原';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[6]})
    # 141~160㎡
    cursor.execute(
        "SELECT count(*) from house where area between 141 and 160 and city = '太原';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[7]})
    # 161~180㎡
    cursor.execute(
        "SELECT count(*) from house where area between 161 and 180 and city = '太原';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[8]})
    # 181~200㎡
    cursor.execute(
        "SELECT count(*) from house where area between 181 and 200 and city = '太原';")
    count = cursor.fetchall()
    area_data.append({'value': count[0][0], 'name': area_kind[9]})
    # 楼层
    cursor.execute("SELECT DISTINCT(floor) from house where city = '太原';")
    result = cursor.fetchall()
    floor_kind = []
    floor_data = []
    # 获取到楼层的几种情况
    for field in result:
        floor_kind.append(field[0])
    # 获取到每种楼层类型对应的个数
    for i in range(len(floor_kind)):
        cursor.execute("SELECT count(*) from house where floor = '" +
                       floor_kind[i] + "' and city = '太原';")
        count = cursor.fetchall()
        floor_data.append({'value': count[0][0], 'name': floor_kind[i]})
    # 价格
    max_dict = []
    price_kind = ['<=1000', '1001~2000', '2001~3000', '3001~4000', '4001~5000', '5001~6000', '6001~7000', '7001~8000',
                  '8001~9000', '9001~10000', '>10000']
    price_data = []
    # 获取到每种价格类别对应的个数
    # <=1000
    cursor.execute(
        "SELECT count(*) from house where price between 0 and 1000 and city = '太原';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[0], 'max': 1600})
    # 1001~2000
    cursor.execute(
        "SELECT count(*) from house where price between 1001 and 2000 and city = '太原';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[1], 'max': 1600})
    # 2001~3000
    cursor.execute(
        "SELECT count(*) from house where price between 2001 and 3000 and city = '太原';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[2], 'max': 1600})
    # 3001~4000
    cursor.execute(
        "SELECT count(*) from house where price between 3001 and 4000 and city = '太原';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[3], 'max': 1600})
    # 4001~5000
    cursor.execute(
        "SELECT count(*) from house where price between 4001 and 5000 and city = '太原';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[4], 'max': 1600})
    # 5001~6000
    cursor.execute(
        "SELECT count(*) from house where price between 5001 and 6000 and city = '太原';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[5], 'max': 1600})
    # 6001~7000
    cursor.execute(
        "SELECT count(*) from house where price between 6001 and 7000 and city = '太原';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[6], 'max': 1600})
    # 7001~8000
    cursor.execute(
        "SELECT count(*) from house where price between 7001 and 8000 and city = '太原';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[7], 'max': 1600})
    # 8001~9000
    cursor.execute(
        "SELECT count(*) from house where price between 8001 and 9000 and city = '太原';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[8], 'max': 1600})
    # 9001~10000
    cursor.execute(
        "SELECT count(*) from house where price between 9001 and 10000 and city = '太原';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[9], 'max': 1600})
    # >10000
    cursor.execute(
        "SELECT count(*) from house where price >10000 and city = '太原';")
    count = cursor.fetchall()
    price_data.append(count[0][0])
    max_dict.append({'name': price_kind[10], 'max': 1600})

    cursor.close()
    return jsonify({"district": district, "district_data": district_data, "area_data": area_data, "floor_kind": floor_kind, "floor_data": floor_data,
                    "price_data": price_data, "max_dict": max_dict})

if __name__ == "__main__":

    app.run(port=5000)



