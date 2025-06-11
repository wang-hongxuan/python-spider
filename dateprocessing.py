import pandas as pd
import numpy as np

def clean_salary_data(df):
    # 1. 删除薪资为"面议"的行
    df = df[df['薪资'] != '面议'].copy()

    # 2. 删除包含"时"、”次“字的薪资行（处理时薪数据）
    df = df[~df['薪资'].str.contains('时', na=False)].copy()
    df = df[~df['薪资'].str.contains('次', na=False)].copy()
    # 3. 删除技能要求为空的行
    df = df.dropna(subset=['技能要求']).copy()

    # 4. 删除完全重复的行
    df = df.drop_duplicates().copy()

    # 5. 将企业性质空值填充为"其他"
    df['性质'] = df['性质'].fillna('其他')

    # 6. 处理薪资列
    def process_salary(salary):
        if not isinstance(salary, str):
            return np.nan

        # 处理日薪（如"300元/天"或"120-150元/天"）
        if '元/天' in salary:
            salary = salary.replace('元/天', '')
            if '-' in salary:  # 处理范围值
                low, high = map(float, salary.split('-'))
                monthly_avg = (low + high) / 2 * 30
                return f"{monthly_avg / 1000:.1f}k"
            else:  # 处理单个值
                return f"{float(salary) * 30 / 1000:.1f}k"

        # 去除薪资格式中的薪资计数后缀（如"·14薪"）
        if '薪' in salary:
            salary = salary.split('·')[0]

        # 处理"万"为单位的薪资（如"1.5-3万"）
        if '万' in salary:
            salary = salary.replace('万', '')
            if '-' in salary:
                low, high = map(float, salary.split('-'))
                return f"{low * 10:.1f}-{high * 10:.1f}k"
            else:
                return f"{float(salary) * 10:.1f}k"

        # 处理"元"为单位的薪资（如"7000-8000元"）
        if '元' in salary:
            salary = salary.replace('元', '')
            if '-' in salary:
                low, high = map(float, salary.split('-'))
                return f"{low / 1000:.1f}-{high / 1000:.1f}k"
            else:
                return f"{float(salary) / 1000:.1f}k"

        # 处理已经是k为单位的薪资（如"15-30k"）
        if 'k' in salary.lower():
            return salary.replace('K', 'k')

        return salary

    df['处理后的薪资'] = df['薪资'].apply(process_salary)

    # 7. 添加平均月薪列（单位为元）
    def calculate_avg(salary_str):
        if not isinstance(salary_str, str):
            return np.nan

        # 处理范围值（如"7-8k"或"15-20k"）
        if '-' in salary_str and 'k' in salary_str:
            salary_str = salary_str.replace('k', '')
            low, high = map(float, salary_str.split('-'))
            return (low + high) / 2 * 1000

        # 处理单个值（如"15k"）
        elif 'k' in salary_str:
            return float(salary_str.replace('k', '')) * 1000

        return np.nan

    df['平均月薪(元)'] = df['处理后的薪资'].apply(calculate_avg)

    # 8. 添加平均月薪k列（单位为k）
    df['平均月薪'] = df['平均月薪(元)'].apply(lambda x: f"{x / 1000:.1f}k" if pd.notnull(x) else np.nan)
    return df


# 读取原始数据
try:
    df = pd.read_csv('zhaopin_multiple_positions1.csv')
except FileNotFoundError:
    print("错误：找不到输入文件 'zhaopin_multiple_positions1.csv'")
    exit()
except Exception as e:
    print(f"读取文件时出错: {str(e)}")
    exit()

# 清洗数据
try:
    cleaned_df = clean_salary_data(df)

    # 保存清洗后的数据
    cleaned_df.to_csv('zhaopin_cleaned1.csv', index=False, encoding='utf-8-sig')
    print("数据清洗完成，已保存到 zhaopin_cleaned1.csv")

    # 显示前几行数据供检查
    print("\n清洗后的数据样例：")
    print(cleaned_df[['职位', '薪资', '处理后的薪资', '平均月薪']].head())

except Exception as e:
    print(f"数据处理过程中出错: {str(e)}")