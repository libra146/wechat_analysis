import re
import sqlite3
import string
from collections import Counter

import jieba
import pandas as pd
from pandas import DataFrame
from pyecharts import options as opts
from pyecharts.charts import Bar, Page, WordCloud

# 微信数据库路径
path = ''
# 需要分析的人的微信号
talker = ''

# 加载数据
con = sqlite3.connect(path)
# 提取数据，将需要的字段查询出来，过滤掉没有意义的字段和数据类型，按照时间排序
sql = f"SELECT type,status,isSend,createTime,talker,content FROM message where talker='{talker}'" \
      f" and type not in (3,43,47,49,889192497,10000,1048625,754974769) ORDER BY createTime"
# 读取数据到DataFrame
data = pd.read_sql_query(sql=sql, con=con)
# 过滤数据，将引用的内容还原回正常文本
data['content'] = data['content'].apply(
    lambda x: re.search('<title>(.*?)</title>', x).group(1) if re.search('<title>(.*?)</title>', x) else x)
# 处理时间，将时间戳转换为年月日时分秒的格式，记得转换时区
data['datetime'] = data['createTime'].apply(
    lambda x: pd.Timestamp(x, unit='ms', tz='Asia/Shanghai').strftime('%Y-%m-%d %H:%M:%S'))
# 重新格式化时间，用来作为分组依据
data['time'] = data['createTime'].apply(lambda x: pd.Timestamp(x, unit='ms', tz='Asia/Shanghai').strftime('%Y-%m-%d'))

# 按照每天的所有聊天记录统计
# 按照时间（精确到日期）进行分组统计，统计出每天聊天记录的数量
content_num: DataFrame = data.groupby('time')['content'].count().reset_index()

bar = Bar(init_opts=opts.InitOpts(width='1500px', height='650px'))
bar.add_xaxis(content_num['time'].tolist())
bar.add_yaxis(content_num.columns[1], content_num['content'].tolist())

# 按照每天每个人聊天记录统计
# 根据isSend筛选出发送和回复，按照日期分开统计
content_num_my: DataFrame = data[data['isSend'] == 1].groupby('time')['content'].count().reset_index()
content_num_my.rename(columns={'content': 'my'}, inplace=True)

content_num_you: DataFrame = data[data['isSend'] == 0].groupby('time')['content'].count().reset_index()
content_num_you.rename(columns={'content': 'you'}, inplace=True)
# 合并两个表格。横向合并数据，使用内连接方式
merge = pd.merge(left=content_num_my, right=content_num_you, left_on='time', right_on='time', how='inner')

bar1 = Bar(init_opts=opts.InitOpts(width='1500px', height='650px'))
bar1.add_xaxis(merge['time'].tolist())
bar1.add_yaxis(merge.columns[1], merge['you'].tolist())
bar1.add_yaxis(merge.columns[2], merge['my'].tolist())

# 按照每天聊天时间点统计
data['hour'] = data['createTime'].apply(lambda x: pd.Timestamp(x, unit='ms', tz='Asia/Shanghai').strftime('%H'))
hour: DataFrame = data.groupby('hour')['content'].count().reset_index()

bar2 = Bar(init_opts=opts.InitOpts(width='1500px', height='650px'))
bar2.add_xaxis(hour['hour'].tolist())
bar2.add_yaxis(hour.columns[1], hour['content'].tolist())

# 词云图
result = []
# 排除列表，包括中英文标点符号和一些停止词
extend = list('，。、【 】 “”：；（）《》‘’{}？！⑦()、%^>℃：.”“^-——=&#@￥') + list(string.punctuation)
with open('cn_stopwords.txt', 'r', encoding='utf8') as f:
    for cc in f:
        extend.append(cc.replace('\n', ''))
# 可选是否要过滤掉表情
extend = list(set(extend))  # +['旺柴','捂脸','皱眉','吃瓜']
for a in data['content'].tolist():
    for b in jieba.cut(a, cut_all=False, HMM=True):
        if b not in extend:
            result.append(b)

bar3 = WordCloud()
bar3.add(series_name="词云", data_pair=Counter(result).items(), word_size_range=[10, 80])
bar3.set_global_opts(
    title_opts=opts.TitleOpts(
        title="词云", title_textstyle_opts=opts.TextStyleOpts(font_size=23)
    ),
    tooltip_opts=opts.TooltipOpts(is_show=True),
)

# 按照所有的字数统计
data['num'] = data['content'].apply(lambda x: len(x))
num: DataFrame = data.groupby('time')['num'].sum().reset_index()

bar4 = Bar(init_opts=opts.InitOpts(width='1500px', height='650px'))
bar4.add_xaxis(num['time'].tolist())
bar4.add_yaxis(num.columns[1], num['num'].tolist())

# 按照每天每个人聊天字数统计
num_my: DataFrame = data[data['isSend'] == 1].groupby('time')['num'].sum().reset_index()
num_my.rename(columns={'num': 'my'}, inplace=True)

num_you: DataFrame = data[data['isSend'] == 0].groupby('time')['num'].sum().reset_index()
num_you.rename(columns={'num': 'you'}, inplace=True)

merge = pd.merge(left=num_my, right=num_you, left_on='time', right_on='time', how='inner')
bar5 = Bar(init_opts=opts.InitOpts(width='1500px', height='650px'))
bar5.add_xaxis(merge['time'].tolist())
bar5.add_yaxis(merge.columns[1], merge['you'].tolist())
bar5.add_yaxis(merge.columns[2], merge['my'].tolist())

# 按照周一到周日的聊天频次统计
data['week'] = data['createTime'].apply(lambda x: pd.Timestamp(x, unit='ms', tz='Asia/Shanghai').strftime('%w'))
week: DataFrame = data.groupby('week')['content'].count().reset_index()
bar6 = Bar(init_opts=opts.InitOpts(width='1500px', height='650px'))
bar6.add_xaxis(week['week'].tolist())
bar6.add_yaxis(week.columns[1], week['content'].tolist())

# 顺序显示图标
grid = Page()
grid.add(bar)
grid.add(bar1)
grid.add(bar2)
grid.add(bar3)
grid.add(bar4)
grid.add(bar5)
grid.add(bar6)
grid.render()
