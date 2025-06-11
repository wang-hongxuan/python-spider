import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import defaultdict
import warnings
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
from sklearn.preprocessing import MinMaxScaler

warnings.filterwarnings('ignore')

# 设置中文字体显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


#加载并预处理招聘数据
def load_data():
    try:
        df = pd.read_csv('zhaopin_cleaned.csv')
    except FileNotFoundError:
        print("错误：找不到输入文件 'zhaopin_cleaned.csv'")
        exit()
    except Exception as e:
        print(f"读取文件时出错: {str(e)}")
        exit()


    return df

#薪资分布分析
def salary_analysis(df):

    # 月薪分布直方图
    plt.figure(figsize=(12, 6))
    sns.histplot(df['平均月薪(元)'], bins=20, kde=True)
    plt.title('平均月薪分布')
    plt.xlabel('平均月薪（元）')
    plt.ylabel('频数')
    plt.show()

    # 划分薪资区间并生成饼图
    salary_bins = [0, 10000, 20000, 30000, float('inf')]
    salary_labels = ['<10k', '10-20k', '20-30k', '30k以上']
    df['薪资区间'] = pd.cut(df['平均月薪(元)'], bins=salary_bins, labels=salary_labels)

    plt.figure(figsize=(8, 8))
    salary_dist = df['薪资区间'].value_counts().sort_index()
    plt.pie(salary_dist, labels=salary_dist.index, autopct='%1.1f%%', startangle=90)
    plt.title('薪资区间分布')
    plt.show()

#公司特征分析
def company_analysis(df):
    for field in ['规模', '性质']:
        plt.figure(figsize=(8, 8))
        # 计算各类别的占比（百分比）
        counts = df[field].value_counts(normalize=True) * 100
        # 将占比小于2%的类别合并为"其他"
        small = counts[counts < 2]
        main_counts = counts[counts >= 2].copy()
        if not small.empty:
            main_counts['其他'] = small.sum()
        # 生成饼图
        main_counts.plot(kind='pie', autopct='%1.1f%%', startangle=90)
        plt.title(f'{field}分布 （合并<2%类别）')
        plt.ylabel('')
        plt.show()

#学历与薪资关系分析
def education_salary_analysis(df):
    target_positions = ['Python开发工程师', '数据分析师', 'IOS开发工程师', '人工智能', '深度学习算法工程师']
    for position in target_positions:
        position_df = df[df['岗位'] == position].dropna(subset=['学历'])
        if len(position_df) == 0:
            continue

        # 定义学历顺序
        education_order = ['学历不限', '大专', '本科', '硕士', '博士']
        # 筛选实际存在的学历类别
        existing_edu = [e for e in education_order if e in position_df['学历'].unique()]
        if not existing_edu:
            continue

        plt.figure(figsize=(10, 6))
        # 绘制无置信区间的柱状图
        sns.barplot(x='学历', y='平均月薪(元)', data=position_df, order=existing_edu, estimator=np.mean, ci=None)
        plt.title(f'{position}: 学历与平均月薪关系')
        plt.xlabel('学历')
        plt.ylabel('平均月薪（元）')
        plt.show()

#岗位技能需求分析- 针对目标岗位分别分析- 生成技能词云图和Top10技能饼图
def skills_analysis(df):

    target_positions = ['Python开发工程师', '数据分析师', 'IOS开发工程师', '人工智能', '深度学习算法工程师']
    for position in target_positions:
        position_df = df[df['岗位'] == position].dropna(subset=['技能要求'])
        if len(position_df) == 0:
            continue

        # 处理技能要求字段，提取单个技能
        skills = position_df['技能要求'].str.split(',').explode().str.strip()
        skill_counts = skills.value_counts().head(15)

        # 生成技能词云
        plt.figure(figsize=(10, 8))
        wordcloud = WordCloud(
            font_path='simhei.ttf',
            background_color='white',
            width=800,
            height=600
        ).generate_from_frequencies(skill_counts.to_dict())
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'{position}技能词云')
        plt.show()

        # 生成Top10技能饼图
        plt.figure(figsize=(10, 8))
        top_skills = skill_counts.head(10)
        plt.pie(top_skills, labels=top_skills.index, autopct='%1.1f%%', startangle=90)
        plt.title(f'{position} Top10技能需求')
        plt.show()

#技能缺口分析- 综合分析目标岗位的热门技能- 生成技能需求热力图，展示技能与岗位的关联
def skill_gap_analysis(df):

    target_positions = ['Python开发工程师', '数据分析师', 'IOS开发工程师', '人工智能', '深度学习算法工程师']
    all_skills = []

    # 收集所有岗位的技能需求
    for position in target_positions:
        position_df = df[df['岗位'] == position].dropna(subset=['技能要求'])
        if len(position_df) > 0:
            skills = position_df['技能要求'].str.split(',').explode().str.strip()
            all_skills.extend(skills)

    # 生成Top15热门技能饼图
    skill_counts = pd.Series(all_skills).value_counts().head(15)
    plt.figure(figsize=(12, 8))
    plt.pie(skill_counts, labels=skill_counts.index, autopct='%1.1f%%', startangle=90)
    plt.title('Top15热门技能需求(五类岗位综合)')
    plt.show()

    # 分析技能与岗位的关联关系
    skill_trend = pd.DataFrame()
    for position in target_positions:
        position_df = df[df['岗位'] == position].dropna(subset=['技能要求'])
        if len(position_df) > 0:
            skills = position_df['技能要求'].str.split(',').explode().str.strip()
            skill_trend[position] = skills.value_counts().head(10)

    # 生成技能-岗位热力图
    if not skill_trend.empty:
        plt.figure(figsize=(12, 8))
        sns.heatmap(skill_trend.fillna(0), cmap='YlGnBu', annot=True, fmt='.0f')
        plt.title('热门技能与岗位需求关系')
        plt.xlabel('岗位')
        plt.ylabel('技能')
        plt.show()

#高级技能分析- 计算技能稀缺性评分（结合出现频率和薪资溢价）- 生成技能稀缺性散点图 挖掘技能组合关联规则
def enhanced_skills_analysis(df):

    target_positions = ['Python开发工程师', '数据分析师', 'IOS开发工程师', '人工智能', '深度学习算法工程师']
    all_skills = defaultdict(int)

    # 统计各技能在所有岗位中的出现次数
    for position in target_positions:
        position_df = df[df['岗位'] == position].dropna(subset=['技能要求'])
        if len(position_df) == 0:
            continue

        skills = position_df['技能要求'].str.split(',').explode().str.strip()
        skill_counts = skills.value_counts().to_dict()
        for skill, count in skill_counts.items():
            all_skills[skill] += count

    # 计算技能稀缺性评分（出现频率 * 薪资溢价）
    skill_stats = []
    for skill in all_skills:
        has_skill = df[df['技能要求'].str.contains(skill, na=False)]
        if len(has_skill) > 0:
            no_skill = df[~df['技能要求'].str.contains(skill, na=False)]
            # 计算掌握该技能带来的平均薪资溢价
            salary_premium = has_skill['平均月薪(元)'].mean() - no_skill['平均月薪(元)'].mean()
            skill_stats.append({
                '技能': skill,
                '出现频率': len(has_skill),
                '平均薪资溢价': salary_premium,
                '稀缺性评分': (len(has_skill) / len(df)) * salary_premium
            })

    # 生成技能稀缺性散点图
    skill_df = pd.DataFrame(skill_stats).sort_values('稀缺性评分', ascending=False).head(20)
    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        data=skill_df.head(15),
        x='出现频率',
        y='平均薪资溢价',
        size='稀缺性评分',
        hue='技能',
        sizes=(100, 500)
    )
    plt.title('技能稀缺性分析\n(气泡大小表示稀缺性评分)')
    plt.xlabel('出现频率')
    plt.ylabel('薪资溢价(元)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

    # 使用关联规则挖掘技能组合
    skill_transactions = df['技能要求'].dropna().str.split(',').apply(lambda x: [s.strip() for s in x]).tolist()
    te = TransactionEncoder()
    te_ary = te.fit(skill_transactions).transform(skill_transactions)
    skill_matrix = pd.DataFrame(te_ary, columns=te.columns_)
    frequent_itemsets = apriori(skill_matrix, min_support=0.05, use_colnames=True)
    frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(len)
    print("\n最常见的技能组合（支持度>5%）:")
    print(frequent_itemsets[frequent_itemsets['length'] > 1].sort_values('support', ascending=False).head(10))


#岗位竞争分析- 评估目标岗位的竞争程度- 分析招聘人数、薪资、经验要求和学历门槛- 生成岗位竞争指标热力图
def position_competition_analysis(df):

    target_positions = ['Python开发工程师', '数据分析师', 'IOS开发工程师', '人工智能', '深度学习算法工程师']
    competition_df = df[df['岗位'].isin(target_positions)].copy()

    # 计算各岗位的竞争指标
    comp_metrics = competition_df.groupby('岗位').agg({
        '招聘人数': 'mean',  # 平均招聘人数（需求规模）
        '平均月薪(元)': 'mean',  # 平均薪资
        '经验': lambda x: x.str.contains('不限', na=False).mean(),  # 经验要求宽松度
        '学历': lambda x: x.isin(['大专', '本科']).mean()  # 低学历比例（门槛）
    }).rename(columns={
        '招聘人数': '平均招聘人数',
        '经验': '经验宽松度',
        '学历': '低学历比例'
    })

    # 标准化指标值以便比较
    scaler = MinMaxScaler()
    comp_metrics_norm = pd.DataFrame(scaler.fit_transform(comp_metrics), columns=comp_metrics.columns,index=comp_metrics.index)

    # 生成岗位竞争热力图
    plt.figure(figsize=(10, 6))
    sns.heatmap(
        comp_metrics_norm.T,
        cmap='YlOrRd',
        annot=True,
        fmt='.2f',
        vmin=0,
        vmax=1
    )
    plt.title('岗位竞争指标对比热力图\n(数值越大：薪资越高/门槛越低，竞争越激烈)')
    plt.xlabel('岗位')
    plt.ylabel('竞争指标')
    plt.tight_layout()
    plt.show()


def main():
    df = load_data()
    print("数据基本信息:")
    print(f"总记录数: {len(df)}")
    print(f"平均月薪范围: {df['平均月薪(元)'].min() / 1000:.1f}k - {df['平均月薪(元)'].max() / 1000:.1f}k")
    print("\n前5条数据:")
    print(df.head())

    # 依次执行各项分析
    salary_analysis(df)
    company_analysis(df)
    education_salary_analysis(df)
    skills_analysis(df)
    skill_gap_analysis(df)
    enhanced_skills_analysis(df)
    position_competition_analysis(df)


if __name__ == "__main__":
    main()