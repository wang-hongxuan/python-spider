from DrissionPage import ChromiumPage
from pprint import pprint
import csv
import time
from random import uniform

# 定义岗位URL列表和对应的岗位名称
position_urls = [
    ('https://www.zhaopin.com/sou/jl489/kw01800U80EG06G03F01N5U02JQ4/p2', 'Python开发工程师'),
    ('https://www.zhaopin.com/sou/jl489/kw数据分析/p2', '数据分析师'),
    ('https://www.zhaopin.com/sou/jl489/kw014G0JO0AC/p2', 'IOS开发工程师'),
    ('https://www.zhaopin.com/sou/jl489/kw人工智能/p2', '人工智能'),
    ('https://www.zhaopin.com/sou/jl489/kw深度学习/p2', '深度学习算法工程师')
]

# 创建文件对象
f = open('zhaopin_multiple_positions1.csv', mode='w', encoding='utf-8', newline='')
csv_writer = csv.DictWriter(f, fieldnames=[
    '岗位',
    '职位',
    '薪资',
    '公司',
    '城市',
    #'区域',
    #'街道',
    '经验',
    '学历',
    '领域',
    '规模',
    '性质',
    '技能要求',
    #'岗位需求',
    '招聘人数',
    '公司详情页',
    '职位详情页',
])
csv_writer.writeheader()

# 打开浏览器
dp = ChromiumPage()

# 遍历所有岗位URL
for position_url, position_name in position_urls:
    print(f'\n开始爬取岗位: {position_name}, URL: {position_url}')

    # 监听数据包
    dp.listen.start('search/positions')

    # 访问网站
    dp.get(position_url)

    # 下滑页面操作
    dp.scroll.to_bottom()
    time.sleep(uniform(1, 3))

    # 点击上一页（回到第一页）
    if dp.ele('css:.btn', timeout=3):
        dp.ele('css:.btn').click()
        time.sleep(uniform(1, 2))

    # 构建循环翻页
    for page in range(8):
        print(f'正在处理第 {page + 1} 页...')

        try:
            # 等待数据包加载
            resp = dp.listen.wait(timeout=10)
            if not resp:
                print(f'第 {page + 1} 页未获取到数据包')
                continue

            # 获取响应的数据
            json_data = resp.response.body

            #解析数据
            # 键值取值，提取职位信息所在列表list
            JobList = json_data['data']['list']

            # for循环遍历，提取列表里面的元素
            for job in JobList:
                # 处理技能标签
                skill_labels = job.get('skillLabel', [])
                skill_values = ', '.join(
                    [item['value'] for item in skill_labels if isinstance(item, dict) and 'value' in item])
                # 提取具体职位信息，保存字典中
                dic = {
                    '岗位': position_name,  # 新增的岗位列
                    '职位': job.get('name', ''),
                    '薪资': job.get('salary60', ''),
                    '公司': job.get('companyName', ''),
                    '城市': job.get('workCity', ''),
                    #'区域': job.get('cityDistrict', '),
                    #'街道': job.get('streetName', '),
                    '经验': job.get('workingExp', ''),
                    '学历': job.get('education', ''),
                    '领域': job.get('industryName', ''),
                    '规模': job.get('companySize', ''),
                    '性质': job.get('propertyName', ''),
                    '技能要求': skill_values,
                    #'岗位需求': job.get('jobSummary', '),
                    '招聘人数': job.get('recruitNumber', ''),
                    '公司详情页': job.get('companyUrl', ''),
                    '职位详情页': job.get('positionURL', ''),
                }
                # 写入数据
                csv_writer.writerow(dic)
                pprint(dic)

            # 下滑到底部
            dp.scroll.to_bottom()
            time.sleep(uniform(1, 2))

            # 处理弹窗（如果存在）
            if dp.ele('css:.a-dialog__close', timeout=2):
                dp.ele('css:.a-dialog__close').click()
                time.sleep(1)

            # 点击下一页（保持原有逻辑）
            next_btn = dp.ele('css:.soupager a:last-of-type', timeout=5)
            if next_btn:
                next_btn.click()
                time.sleep(uniform(2, 4))
            else:
                print('未找到下一页按钮，终止当前岗位爬取')
                break

        except Exception as e:
            print(f'处理第 {page + 1} 页时出错: {str(e)}')
            continue

    print(f'完成当前岗位爬取，等待3-6秒后继续下一个岗位...')
    time.sleep(uniform(3, 6))

# 关闭浏览器和文件
dp.quit()
f.close()
print('\n所有岗位数据爬取完成，已保存到 zhaopin_multiple_positions1.csv')