import sqlite3
import threading
import time

# 1. 创建数据库和插入测试数据
def create_database():
    for count in range(6):
        conn = sqlite3.connect(f'test_{count}.db')
        cursor = conn.cursor()
        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value TEXT
            )
        ''')
        # 插入测试数据
        for i in range(1000000):
            cursor.execute("INSERT INTO test_table (value) VALUES (?)", (f"Value {i}",))
        conn.commit()
        conn.close()

# 2. 定义查询函数，只统计 execute 时间
def query_database(query,idx = 0):
    print(f"task {idx}begin, query is {query}.")
    conn = sqlite3.connect(f'test_{idx}.db')
    cursor = conn.cursor()
    print(f"task {idx}mid, query is {query}.")
    start_time = time.time()
    cursor.execute(query)
    results = cursor.fetchall()
    end_time = time.time()
    conn.close()
    print(f"task {idx}done, query is {query}.")
    return end_time - start_time

# 3. 使用单线程执行查询，只统计 execute 总时间
def single_thread_query():
    queries = [
        "SELECT * FROM test_table"
    ]
    total_time = 0
    for idx,query in enumerate(queries):
        total_time += query_database(query,idx)
    print(f"单线程 execute 总耗时: {total_time} 秒")

# 4. 使用多线程执行查询，只统计 execute 总时间
def multi_thread_query():
    queries = [
        "SELECT * FROM test_table",
        "SELECT * FROM test_table WHERE id BETWEEN 1 AND 200000",
        "SELECT * FROM test_table WHERE id BETWEEN 200001 AND 400000",
        "SELECT * FROM test_table WHERE id BETWEEN 400001 AND 600000",
        "SELECT * FROM test_table WHERE id BETWEEN 600001 AND 800000",
        "SELECT * FROM test_table WHERE id BETWEEN 800001 AND 1000000"
    ]
    threads = []
    time_results = [0 for _ in queries]
    def thread_wrapper(query, idx):
        execute_time = query_database(query,idx)
        time_results[idx] = execute_time

    for idx,query in enumerate(queries):
        thread = threading.Thread(target=thread_wrapper, args=(query,idx))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    total_time = sum(time_results)/len(time_results)
    print(f"多线程 execute 平均耗时: {total_time} 秒")
    print(f"多线程 execute 总耗时: {total_time} 秒")
    print(time_results)

if __name__ == "__main__":
    create_database()
    single_thread_query()
    multi_thread_query()