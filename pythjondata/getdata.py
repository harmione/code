# 2024.10.21最新更新
import psycopg2
import datetime
import pandas as pd
import openpyxl
# 配置数据库连接
postgres_conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="qyng@mds",
    host="10.100.0.189",
    port="1235"
)

# 创建cursor对象
postgres_cursor = postgres_conn.cursor()

# 定义获取数据和插入数据的函数
def fetch_data_from_source():
    # 这里写查询源数据库的SQL语句
    source_sql_query = """
        select
        p."Year" as "年份",
        p."BookPrj" as "育种站",
        p."BookName" as "测试点",
        count(*) as "保苗数",
        count(p."YLD14") as "产量",
        count(p."MST") as "水分",
        count(p."PHT") as "株高",
        count(p."EHT") as "穗位",
        count(p."EARTCNT") as "穗腐病穗数",
        count(p."GSPCNT") as "早期茎折株数",
        count(p."GSPPCT") as "早期茎折比例",
        count(p."STKLCNT") as "茎倒株数",
        count(p."STKLPCT") as "茎倒比例",
        count(p."STKRPCT") as "茎基腐病比例",
        count(p."ERTLPCT") as "前期根倒比例",
        count(p."LRTLPCT") as "后期根倒级别",
        count(p."RTLPCT") as "根倒比例",
        count(p."TDPPCT") as "倒折比例",
        count(p."GLS") as "灰斑病级别",
        count(p."SCLB") as "小斑病级别",
        count(p."NCLB") as "大斑病级别",
        count(p."RSTCOM") as "普通锈病级别",
        count(p."RSTSOU") as "南方锈病级别",
        count(p."CWLSPT") as "白斑病级别",
        count(p."PMDCNT") as "青枯病株数",
        count(p."PMDSC") as "青枯病级别",
        count(p."PMDPCT") as "青枯病比例",
        count(P."SHBLSC") as "纹枯病级别",
        count(p."EARTSC") as "穗腐病级别",
        count(p."SEDSC") as "苗情级别"

    from
        "ODS"."ODSPheno" p
    where
        "TrialType" not like '%Filler%' AND p."Year" ='2024'
    group by
        p."Year" ,
        p."BookPrj" ,
        p."BookName"
    order by
        p."Year" desc ,
        p."BookName"
    """
    postgres_cursor.execute(source_sql_query)
    return postgres_cursor.fetchall()


def insert_data_into_target(time,data):
    # 插入数据到目标表
    # target_sql_query = "INSERT INTO target_table (column1, column2) VALUES %s;"
    temp_data = [row[3:] for row in data]
    # 使用 zip 转置矩阵
    transposed_matrix = zip(*temp_data)
    # 计算每一列的和
    column_sums = [sum(column) if isinstance(column[0],int) else 0 for column in transposed_matrix ]
    #column_sums.insert(0,time)
    column_sums.append(time)
    enddata = [tuple(column_sums)]
    columns = [
        'bm_sum', 'yld14', 'mst', 'pht', 'eht', 'eartcnt', 'gspcnt', 'gsppct',
        'stklcnt', 'stklpct','stkrpct', 'ertlpct', 'lrtlpct', 'rtlpct', 'tdppct', 'gls',
        'sclb', 'nclb', 'rstcom', 'rstsou', 'cwlspt', 'pmdcnt', 'pmdsc',
        'pmdpct', 'shblsc', 'eartsc', 'sedsc', 'create_time'
    ]
    placeholders = ', '.join(['%s'] * len(columns))

    sql_insert = """
    INSERT INTO "DWS".save_everyday_data (%s)
    VALUES (%s);
    """ % (', '.join(columns), placeholders)

    for row in enddata:
        postgres_cursor.execute(sql_insert,row)
    postgres_conn.commit()

# 获取数据
data_to_insert = fetch_data_from_source()

# 获取当前日期
current_date = datetime.date.today()
# 将日期格式化为 YYYY-MM-DD
formatted_date = current_date.strftime('%Y-%m-%d')

# 插入数据到目标表
insert_data_into_target(formatted_date,data_to_insert)

#关闭cursor和连接
postgres_cursor.close()
postgres_conn.close()
