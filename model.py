from preprocessing import getXandY# 导入自定义数据预处理函数，用于获取特征(X)和标签(Y)
import numpy as np# 用于数值计算，处理矩阵和数组，将数据转换为矩阵格式，方便机器学习模型处理
from sklearn.model_selection import train_test_split# 划分训练集和测试集，按比例（如 8:2）划分数据，用于评估模型泛化能力
from imblearn.over_sampling import RandomOverSampler# 随机过采样，解决数据不平衡问题。对少数类样本进行过采样，平衡类别分布
import pickle# 模型序列化，用于保存和加载模型
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def save_model(filename):
    print(f"开始处理 {filename}")  # 新增调试输出
    X, y = getXandY('./zhaopin_data/' + filename+'.csv')

    X = np.array(X) #将特征列表转换为numpy矩阵
    y = np.array(y) #将标签列表转换为numpy数组

    # 分割数据，将20%的数据作为测试集，其余作为训练集
    # random_state参数固定随机种子，确保每次划分结果一致（可复现性）

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=66)

    # 检查数据的类别分布
    # unique_classes：包含所有唯一的类别标签（如 [0, 1, 2, 3, 4]）。
    # class_counts：对应每个类别的样本数量（如 [100, 200, 50, 20, 5]）
    unique_classes, class_counts = np.unique(y, return_counts=True)
    original_distribution = dict(zip(unique_classes, class_counts))
    print(f"训练集中的类别分布: {original_distribution}")

    # 调整采样策略，确保目标样本数不少于原始样本数
    sampling_strategy = {}
    for class_label, count in original_distribution.items():
        if class_label == 0:
            sampling_strategy[class_label] = max(95, count)
        elif class_label == 1:
            sampling_strategy[class_label] = max(160, count)
        elif class_label == 2:
            sampling_strategy[class_label] = max(100, count)
        elif class_label == 3:
            sampling_strategy[class_label] = max(20, count)

    # 定义过采样策略
    smo = RandomOverSampler(
        sampling_strategy=sampling_strategy, random_state=66)
    X_train, y_train = smo.fit_resample(X_train, y_train)# 对训练集进行过采样

    # 1.K邻近（KNN）
    from sklearn.neighbors import KNeighborsClassifier# 导入KNN分类器
    # 创建KNN分类器
    clf = KNeighborsClassifier(
        algorithm='brute', leaf_size=1, n_neighbors=9, weights='distance')
    # 训练模型
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    print(f"{filename} KNN 准确率: {accuracy_score(y_test, y_pred)}")
    print(f"{filename} KNN 精确率: {precision_score(y_test, y_pred, average='weighted')}")
    print(f"{filename} KNN 召回率: {recall_score(y_test, y_pred, average='weighted')}")
    print(f"{filename} KNN F1 值: {f1_score(y_test, y_pred, average='weighted')}")
    # 保存模型，将模型序列化保存为文件（如java_knn.model）
    with open(filename+'_knn.model', 'wb') as fw:
        # 对象序列化的模，将模型对象转换为字节流写入文件
        pickle.dump(clf, fw)

    # 2.逻辑回归：通过逻辑函数将线性组合转换为概率，适用于二分类或多分类
    from sklearn.linear_model import LogisticRegression
    clf = LogisticRegression(multi_class='ovr', solver='newton-cg')
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    print(f"{filename} 逻辑回归 准确率: {accuracy_score(y_test, y_pred)}")
    print(f"{filename} 逻辑回归 精确率: {precision_score(y_test, y_pred, average='weighted')}")
    print(f"{filename} 逻辑回归 召回率: {recall_score(y_test, y_pred, average='weighted')}")
    print(f"{filename} 逻辑回归 F1 值: {f1_score(y_test, y_pred, average='weighted')}")
    with open(filename+'_logistic.model', 'wb') as fw:
        pickle.dump(clf, fw)

    #3.朴素贝叶斯
    from sklearn.naive_bayes import MultinomialNB
    # 使用默认参数初始化
    # MultinomialNB 类封装了多项式朴素贝叶斯算法的实现
    clf = MultinomialNB()
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    print(f"{filename} 朴素贝叶斯 准确率: {accuracy_score(y_test, y_pred)}")
    print(f"{filename} 朴素贝叶斯 精确率: {precision_score(y_test, y_pred, average='weighted')}")
    print(f"{filename} 朴素贝叶斯 召回率: {recall_score(y_test, y_pred, average='weighted')}")
    print(f"{filename} 朴素贝叶斯 F1 值: {f1_score(y_test, y_pred, average='weighted')}")
    with open(filename+'_NB.model', 'wb') as fw:
        pickle.dump(clf, fw)

filename = ['java', 'python', 'php','web','bi','android','dba','ops']

for i in filename:
    save_model(i)