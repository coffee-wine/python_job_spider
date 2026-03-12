import pandas as pd# 导入pandas库，用于读取和处理表格数据
import numpy as np

# 该函数是特征工程的核心部分，将原始分类数据转换为模型可处理的数值特征和标签，为后续的分类模型（如 KNN、逻辑回归）提供输入数据。
# 通过规则映射（如 “15-50 人”→1）和分桶（如薪资分 5 类），将非结构化数据转换为结构化数值，是机器学习流程中关键的数据预处理步骤。

def getXandY(filename):
    # 读取指定路径的 CSV 文件，仅加载 usecols 指定的 5 列数据
    data = pd.read_csv(filename, encoding='utf-8', usecols=['companySize', 'workYear', 'education', 'salary','city', ])
    #将dataframe类型转化为list（嵌套列表），便于逐行处理每个样本
    # data.values 返回 numpy 数组，tolist() 转换为嵌套列表，格式为 [[row1], [row2], ...]，每个子列表包含该行的 5 个特征值
    list = data.values.tolist()
    # 特征工程的目标是将原始分类数据转换为模型可处理的数值型数据，X 和 y 是机器学习模型的标准输入格式
    X = []# 存储特征矩阵，用于存储转换后的数值特征（如公司规模、工作经验等）
    y = []# 存储标签（薪资等级）
    # 对每个样本（每行数据）进行特征转换，x 存储当前样本的数值特征
    for i in list:
        print(i)#调试
        x = []
        #公司规模
        if(str(i[0]) == '少于15人'):
            x.append(0)
        if (str(i[0]) == '15-50人'):
            x.append(1)
        if (str(i[0]) == '50-150人'):
            x.append(2)
        if (str(i[0]) == '150-500人'):
            x.append(3)
        if (str(i[0]) == '500-2000人'):
            x.append(4)
        if (str(i[0]) == '2000人以上'):
            x.append(5)
        print(f"公司规模：{str(i[0])}")

        #工作经验
        if (str(i[1]) == '不限'):
            x.append(0)
        if (str(i[1]) == '在校/应届'):
            x.append(1)
        if (str(i[1]) == '1年以下'):
            x.append(2)
        if (str(i[1]) == '1-3年'):
            x.append(3)
        if (str(i[1]) == '3-5年'):
            x.append(4)
        if (str(i[1]) == '5-10年'):
            x.append(5)
        print(f"工作经验：{str(i[1])}")

        # 学历
        if (str(i[2]) == '不限'):
            x.append(0)
        if (str(i[2]) == '大专'):
            x.append(1)
        if (str(i[2]) == '本科'):
            x.append(2)
        if (str(i[2]) == '硕士'):
            x.append(3)
        if (str(i[2]) == '博士'):
            x.append(4)
        print(f"学历：{str(i[2])}")

        # 位置
        if (str(i[4]) == '北京'):
            x.append(0)
        if (str(i[4]) == '广州'):
            x.append(1)
        if (str(i[4]) == '上海'):
            x.append(2)
        if (str(i[4]) == '深圳'):
            x.append(3)
        if (str(i[4]) != '深圳' and str(i[4]) != '上海' and str(i[4]) != '广州' and str(i[4]) != '北京'):
            x.append(4)
        print(f"城市：{str(i[4])}")

        # 最低薪资
        salary_str = str(i[3]).strip()
        if salary_str == '面议' or not salary_str:
            continue  # 跳过 “面议” 或空值，不添加此行
        try:
            # 薪资字符串包含 “-”，则取其左边部分；如果只包含 “k”，则直接去除 “k”；否则将最低薪资设为 0
            if '-' in salary_str:
                salary_lower = int(salary_str.split('-')[0].replace('k', ''))
            elif 'k' in salary_str:
                salary_lower = int(salary_str.replace('k', ''))
            else:
                salary_lower = 0
        except (ValueError, IndexError):
            print(f"处理薪资 {salary_str} 时出错，跳过该样本。")
            continue

        if (salary_lower < 10):  # <10k
            y.append(0)
        elif 10 <= salary_lower < 20:
            y.append(1)
        elif 20 <= salary_lower < 30:
            y.append(2)
        elif 30 <= salary_lower < 40:
            y.append(3)
        else:
            y.append(4)

        X.append(x)

    return X,y