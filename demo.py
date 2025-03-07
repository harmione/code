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
    for i in range(1000):
        cursor.execute("INSERT INTO test_table (value) VALUES (?)", (f"Value {i}",))
    conn.commit()
    conn.close()

# 2. 定义查询函数
def query_database(query):
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

# 3. 使用单线程依次执行查询
def single_thread_query():
    queries = [
        "SELECT * FROM test_table WHERE id BETWEEN 1 AND 200",
        "SELECT * FROM test_table WHERE id BETWEEN 201 AND 400",
        "SELECT * FROM test_table WHERE id BETWEEN 401 AND 600",
        "SELECT * FROM test_table WHERE id BETWEEN 601 AND 800",
        "SELECT * FROM test_table WHERE id BETWEEN 801 AND 1000"
    ]
    start_time = time.time()
    for query in queries:
        query_database(query)
    end_time = time.time()
    print(f"单线程查询耗时: {end_time - start_time} 秒")

# 4. 使用多线程执行查询
def multi_thread_query():
    queries = [
        "SELECT * FROM test_table WHERE id BETWEEN 1 AND 200",
        "SELECT * FROM test_table WHERE id BETWEEN 201 AND 400",
        "SELECT * FROM test_table WHERE id BETWEEN 401 AND 600",
        "SELECT * FROM test_table WHERE id BETWEEN 601 AND 800",
        "SELECT * FROM test_table WHERE id BETWEEN 801 AND 1000"
    ]
    threads = []
    start_time = time.time()
    for query in queries:
        thread = threading.Thread(target=query_database, args=(query,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    end_time = time.time()
    print(f"多线程查询耗时: {end_time - start_time} 秒")

if __name__ == "__main__":
    create_database()
    single_thread_query()
    multi_thread_query()