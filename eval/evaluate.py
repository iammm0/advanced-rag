
import json
import asyncio
import os
import sys

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rag_service import rag_service
from services.ollama_service import OllamaService
from utils.logger import logger

# 禁用日志以保持输出清洁
logger.setLevel("ERROR")

ollama = OllamaService()

async def evaluate_single(question, ground_truth):
    """
    评估单个问题的回答质量
    
    Args:
        question: 问题
        ground_truth: 标准答案
        
    Returns:
        (score, generated_answer): 分数和生成的回答
    """
    print(f"正在评估: {question}...")
    # 1. 检索 (Retrieve)
    try:
        retrieval_result = await rag_service.retrieve_context(question)
        context = retrieval_result.get("context", "")
    except Exception as e:
        print(f"检索失败: {e}")
        context = ""
    
    # 2. 生成回答 (Generate Answer)
    generated_answer = ""
    try:
        async for chunk in ollama.generate(question, context=context):
            generated_answer += chunk
    except Exception as e:
        print(f"生成失败: {e}")
        generated_answer = "Error"
        
    # 3. 评估 (Evaluate - LLM-as-a-Judge)
    eval_prompt = f"""
    你是一个评估员。请对比生成的回答和标准答案。
    
    问题: {question}
    标准答案: {ground_truth}
    生成的回答: {generated_answer}
    
    请对回答的正确性进行评分，范围从 0.0 到 1.0。
    只返回数字评分。
    """
    
    try:
        response = ollama.session.post(
            f"{ollama.base_url}/api/generate",
            json={
                "model": ollama.model_name,
                "prompt": eval_prompt,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        eval_resp = response.json().get("response", "").strip()
        
        # 提取分数
        import re
        match = re.search(r"(\d+(\.\d+)?)", eval_resp)
        if match:
            score = float(match.group(1))
            # 归一化处理
            if score > 1.0 and score <= 10.0:
                score /= 10.0
            elif score > 10.0: # 如果是百分制
                score /= 100.0
            score = min(max(score, 0.0), 1.0)
        else:
            score = 0.0
    except Exception as e:
        print(f"评估失败: {e}")
        score = 0.0
        
    return score, generated_answer

async def main():
    """主评估流程"""
    try:
        with open("eval/dataset.json", "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print("未找到数据集。请创建 eval/dataset.json")
        return
        
    total_score = 0
    results = []
    
    print(f"开始评估 {len(dataset)} 个条目...")
    
    for item in dataset:
        score, answer = await evaluate_single(item["question"], item["answer"])
        total_score += score
        results.append({
            "question": item["question"],
            "score": score,
            "answer": answer[:100] + "..." if len(answer) > 100 else answer
        })
        print(f"  -> 分数: {score:.2f}")
        
    avg_score = total_score / len(dataset) if dataset else 0
    print("-" * 50)
    print(f"平均分: {avg_score:.4f}")
    
    # 保存结果
    with open("eval/results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("结果已保存至 eval/results.json")

if __name__ == "__main__":
    asyncio.run(main())
