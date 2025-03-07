'''
Description: 
Author: zhangweilong
Date: 2025-03-07 14:28:15
LastEditTime: 2025-03-07 15:08:21
LastEditors: zhangweilong
'''
import sqlite3
import threading
import time

# 1. 创建数据库和插入测试数据
def create_database():
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    # 创建表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT
        )
    ''')
    # 插入测试数据
    for i in range(100000):
        cursor.execute("INSERT INTO test_table (value) VALUES (?)", (f"Value {i}",))
    conn.commit()
    conn.close()

# 2. 定义查询函数
class QueryDatabase:
    def __init__(self):
        self.conn_list = [sqlite3.connect('test.db', check_same_thread=False) for _ in range(6)]
        self.cursor_list = [self.conn_list[i].cursor() for i in range(6)]
    def query_database(self,query,idx = 0):
        # print(f"Thread {idx} is executing query: {query}")
        self.cursor_list[idx].execute(query)
        results = self.cursor_list[idx].fetchall()
        return results
    def __del__(self):
        for i in range(6):
            self.conn_list[i].close()

QD = QueryDatabase()

# 3. 使用单线程执行查询
def single_thread_query():
    queries = [
        "SELECT * FROM test_table"
    ]
    start_time = time.time()
    for query in queries:
        QD.query_database(query)
    end_time = time.time()
    print(f"单线程查询耗时: {end_time - start_time} 秒")

# 4. 使用多线程执行查询
def multi_thread_query():
    queries = [
        "SELECT * FROM test_table WHERE id BETWEEN 1 AND 20000",
        "SELECT * FROM test_table WHERE id BETWEEN 20001 AND 40000",
        "SELECT * FROM test_table WHERE id BETWEEN 40001 AND 60000",
        "SELECT * FROM test_table WHERE id BETWEEN 60001 AND 80000",
        "SELECT * FROM test_table WHERE id BETWEEN 80001 AND 100000"
    ]
    threads = []
    start_time = time.time()
    count = 1
    for query in queries:
        thread = threading.Thread(target=QD.query_database, args=(query,count))
        threads.append(thread)
        thread.start()
        count += 1
    for thread in threads:
        thread.join()
    end_time = time.time()
    print(f"多线程查询耗时: {end_time - start_time} 秒")

if __name__ == "__main__":
    create_database()
    single_thread_query()
    multi_thread_query()