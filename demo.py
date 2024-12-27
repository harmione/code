'''
Description: 
Author: zhangweilong
Date: 2024-12-27 15:00:42
LastEditTime: 2024-12-27 15:33:32
LastEditors: zhangweilong
'''
import requests
import numpy as np
import faiss
import json
from typing import List, Dict, Tuple

HEADERS = {"Content-Type": "application/json"}

def OLLAMA_URL_GEN(api = "generate"):
    OLLAMA_URL = f"http://localhost:11434/api/{api}"
    return OLLAMA_URL


# Step 1: 使用 Ollama 嵌入模型生成问题向量
def generate_embedding(text: str) -> List[float]:
    url = OLLAMA_URL_GEN("embed")
    payload = {"model":"mxbai-embed-large","input": text}
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json().get("embeddings", [])
    return []

# Step 2: 保存问题-解决方案的向量库到本地
def save_local_vector_library(knowledge_data: List[Tuple[str, str]], library_path: str) -> None:
    embeddings = []
    questions = []
    solutions = []
    for question, solution in knowledge_data:
        vector = generate_embedding(question)
        print(f"问题: {question} -> 向量: {vector[0][:10]}")
        if vector:
            embeddings.append(vector[0])
            questions.append(question)
            solutions.append(solution)
    np.savez(library_path, embeddings=np.array(embeddings), questions=questions, solutions=solutions)
    print(f"问题-解决方案知识向量库已保存到 {library_path}")


# Step 3: 本地加载并使用 FAISS 搜索
def load_local_library(library_path: str):
    data = np.load(library_path, allow_pickle=True)
    embeddings = data["embeddings"]
    questions = data["questions"].tolist()
    solutions = data["solutions"].tolist()
    return embeddings, questions, solutions


def search_top_k(query: str, library_path: str, k: int = 3) -> List[Tuple[str, str]]:
    # 加载本地库
    embeddings, questions, solutions = load_local_library(library_path)

    # 初始化 FAISS 索引
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # 查询向量
    query_vector = np.array(generate_embedding(query)).reshape(1, -1)

    # 搜索最近邻
    _, indices = index.search(query_vector, k)
    return [(questions[i], solutions[i]) for i in indices[0]]

# Step 4: 生成应答
def generate_response_with_prompt(prompt: str, model_name: str = "glm4:latest") -> str:
    url = OLLAMA_URL_GEN()
    payload = {"model":model_name,"prompt": prompt,"stream": False}
    payload_j = json.dumps(payload,ensure_ascii=False,indent=4)
    response = requests.post(url, headers=HEADERS, data=payload_j.encode('utf-8'))
    if response.status_code == 200:
        return response.json().get("response", "")
    return "Error generating response."

# 主流程
if __name__ == "__main__":
    # 问题-解决方案形式的知识点
    knowledge_data = [
        ("什么是 REST API？", "REST API 是一种基于 HTTP 协议的应用程序接口，支持通过标准方法进行资源操作。"),
        ("如何定义机器学习？", "机器学习是一种让计算机从数据中学习和预测的技术，不需要显式编程。"),
        ("Python 有什么特点？", "Python 是一种易于学习、语法简洁且具有广泛生态系统的高级编程语言。")
    ]
    library_path = "qa_knowledge_library.npz"
    # 1. 保存知识向量库到本地
    save_local_vector_library(knowledge_data, library_path)

    # 2. 用户提问
    user_question = "REST API 是什么？"

    # 3. 本地搜索
    top_matches = search_top_k(user_question, library_path, k=3)
    print("找到的相关问题及解决方案：", top_matches)

    # 4. 生成应答
    prompt_content = "\n".join([f"问题：{q}\n解决方案：{s}" for q, s in top_matches])
    prompt = f"以下是与用户提问相关的内容：\n{prompt_content}\n\n基于这些信息，回答以下问题：{user_question}"
    response = generate_response_with_prompt(prompt)
    print("生成的应答：", response)