import requests
import psycopg2
import re
import streamlit as st

# Ollama 容器的 API 地址
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# PostgreSQL 数据库连接信息
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "postgres",
    "user": "postgres",
    "password": "123456"
}

# 调用 DeepSeek 模型生成 SQL 查询
def generate_sql_from_nl(nl_query):
    payload = {
        "model": "deepseek-r1:1.5b",  # 使用 DeepSeek 模型
        "prompt": f"已知在postgresql数据库里有student这个表，且student表里只有id、name、sex这些列名，将以下自然语言转换为PostgreSQL查询语句，只输出语句，不要输出任何其他文本或解释：\n{nl_query}",
        "stream": False
    }
    response = requests.post(OLLAMA_API_URL, json=payload)
    if response.status_code == 200:
        # 提取 SQL 语句
        sql_query = response.json()["response"].strip()
        # 使用正则表达式匹配 SQL 语句
        sql_match = re.search(r"(SELECT|INSERT|UPDATE|DELETE)\s+.*?;", sql_query, re.IGNORECASE)
        if sql_match:
            return sql_match.group(0).strip()
        else:
            raise Exception("未找到有效的 SQL 语句")
    else:
        raise Exception(f"Failed to generate SQL: {response.text}")

# 连接到 PostgreSQL 数据库
def connect_to_db():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

# 执行 SQL 查询
def execute_sql_query(sql):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        return result
    except Exception as e:
        raise Exception(f"SQL execution failed: {e}")
    finally:
        cursor.close()
        conn.close()

# Streamlit 页面逻辑
def streamlitfun():
    st.title("自然语言转SQL查询")
    user_input = st.text_input("请输入你的问题（例如：查询所有年龄大于 30 的用户）: ")
    
    # 创建一个按钮，点击后发送问题到后台
    if st.button("提问"):
        if user_input.strip() == "":
            st.warning("请输入有效的问题！")
        else:
            try:
                # 生成 SQL 查询
                sql_query = generate_sql_from_nl(user_input)
                st.write(f"生成的 SQL 查询: `{sql_query}`")
                
                # 执行 SQL 查询并获取结果
                result = execute_sql_query(sql_query)
                st.write("查询结果:")
                for row in result:
                    st.write(row)
            except Exception as e:
                st.error(f"出错: {e}")

if __name__ == "__main__":
    streamlitfun()