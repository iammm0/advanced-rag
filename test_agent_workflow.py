"""
测试多Agent工作流和流式输出

使用方法:
    python test_agent_workflow.py
"""
import asyncio
import json
import sys
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, '.')

from agents.physics_assistant.physics_assistant_agent import PhysicsAssistantAgent
from utils.logger import logger


async def test_physics_assistant_agent():
    """测试PhysicsAssistantAgent"""
    print("=" * 60)
    print("测试 PhysicsAssistantAgent")
    print("=" * 60)
    
    agent = PhysicsAssistantAgent()
    
    # 测试上下文
    context = {
        "assistant_id": None,
        "conversation_id": None,
        "enable_rag": True,
        "conversation_history": None
    }
    
    # 测试问题
    test_query = "什么是传感器？"
    
    print(f"\n问题: {test_query}")
    print("\n开始流式输出:\n")
    print("-" * 60)
    
    try:
        chunk_count = 0
        full_response = ""
        
        async for result in agent.execute(
            task=test_query,
            context=context,
            stream=True
        ):
            if result.get("type") == "chunk":
                chunk = result.get("content", "")
                full_response += chunk
                chunk_count += 1
                # 实时输出chunk（不换行）
                print(chunk, end="", flush=True)
            
            elif result.get("type") == "complete":
                sources = result.get("sources", [])
                recommended_resources = result.get("recommended_resources", [])
                
                print("\n" + "-" * 60)
                print(f"\n流式输出完成!")
                print(f"总chunk数: {chunk_count}")
                print(f"总响应长度: {len(full_response)}")
                print(f"来源数: {len(sources)}")
                print(f"推荐资源数: {len(recommended_resources)}")
                
                if sources:
                    print("\n来源信息:")
                    for i, source in enumerate(sources[:3], 1):  # 只显示前3个
                        print(f"  {i}. {source.get('document_title', '未知')} (分数: {source.get('score', 0):.3f})")
                
                if recommended_resources:
                    print("\n推荐资源:")
                    for i, resource in enumerate(recommended_resources[:3], 1):  # 只显示前3个
                        print(f"  {i}. {resource.get('title', '未知')}")
            
            elif result.get("type") == "error":
                error_msg = result.get("content", "")
                print(f"\n错误: {error_msg}")
                return False
        
        print("\n" + "=" * 60)
        print("PhysicsAssistantAgent 测试通过!")
        print("=" * 60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_physics_assistant_with_history():
    """测试带对话历史的PhysicsAssistantAgent"""
    print("=" * 60)
    print("测试 PhysicsAssistantAgent (带对话历史)")
    print("=" * 60)
    
    agent = PhysicsAssistantAgent()
    
    # 模拟对话历史
    conversation_history = [
        {"role": "user", "content": "什么是传感器？"},
        {"role": "assistant", "content": "传感器是一种能够感知和检测物理量或化学量的设备..."},
        {"role": "user", "content": "传感器有哪些类型？"}
    ]
    
    # 测试上下文
    context = {
        "assistant_id": None,
        "conversation_id": None,
        "enable_rag": True,
        "conversation_history": conversation_history
    }
    
    # 测试问题（基于对话历史）
    test_query = "请详细解释电阻传感器的原理"
    
    print(f"\n对话历史:")
    for msg in conversation_history:
        print(f"  {msg['role']}: {msg['content'][:50]}...")
    
    print(f"\n当前问题: {test_query}")
    print("\n开始流式输出:\n")
    print("-" * 60)
    
    try:
        chunk_count = 0
        full_response = ""
        
        async for result in agent.execute(
            task=test_query,
            context=context,
            stream=True
        ):
            if result.get("type") == "chunk":
                chunk = result.get("content", "")
                full_response += chunk
                chunk_count += 1
                print(chunk, end="", flush=True)
            
            elif result.get("type") == "complete":
                print("\n" + "-" * 60)
                print(f"\n流式输出完成!")
                print(f"总chunk数: {chunk_count}")
                print(f"总响应长度: {len(full_response)}")
                break
            
            elif result.get("type") == "error":
                error_msg = result.get("content", "")
                print(f"\n错误: {error_msg}")
                return False
        
        print("\n" + "=" * 60)
        print("PhysicsAssistantAgent (带对话历史) 测试通过!")
        print("=" * 60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_non_streaming():
    """测试非流式输出"""
    print("=" * 60)
    print("测试 PhysicsAssistantAgent (非流式输出)")
    print("=" * 60)
    
    agent = PhysicsAssistantAgent()
    
    context = {
        "assistant_id": None,
        "conversation_id": None,
        "enable_rag": False,  # 禁用RAG以加快测试
        "conversation_history": None
    }
    
    test_query = "什么是传感器？"
    
    print(f"\n问题: {test_query}")
    print("\n开始非流式生成...\n")
    
    try:
        full_response = ""
        
        async for result in agent.execute(
            task=test_query,
            context=context,
            stream=False
        ):
            if result.get("type") == "complete":
                full_response = result.get("content", "")
                break
            elif result.get("type") == "error":
                error_msg = result.get("content", "")
                print(f"错误: {error_msg}")
                return False
        
        print("-" * 60)
        print(full_response)
        print("-" * 60)
        print(f"\n响应长度: {len(full_response)}")
        print("=" * 60)
        print("非流式输出测试通过!")
        print("=" * 60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("多Agent工作流和流式输出测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 测试1: 基本流式输出
    print("\n[测试 1/3] 基本流式输出测试")
    result1 = await test_physics_assistant_agent()
    results.append(("基本流式输出", result1))
    
    # 等待一下，避免请求过快
    await asyncio.sleep(2)
    
    # 测试2: 带对话历史的流式输出
    print("\n[测试 2/3] 带对话历史的流式输出测试")
    result2 = await test_physics_assistant_with_history()
    results.append(("带对话历史的流式输出", result2))
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 测试3: 非流式输出
    print("\n[测试 3/3] 非流式输出测试")
    result3 = await test_non_streaming()
    results.append(("非流式输出", result3))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\n总计: {total_passed}/{total_tests} 测试通过")
    print("=" * 60 + "\n")
    
    return total_passed == total_tests


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

