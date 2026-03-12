
import asyncio
import os
import sys
import logging

# 添加项目根目录到 sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)  # 使用 insert(0) 确保优先加载本地包
print(f"Added to sys.path: {root_dir}")
print(f"Current sys.path: {sys.path}")

print("DEBUG: Importing HybridChunker...")
from chunking.hybrid_chunker import HybridChunker
print("DEBUG: Importing knowledge_extraction_service...")
from services.knowledge_extraction_service import knowledge_extraction_service
print("DEBUG: Importing neo4j_client...")
from database.neo4j_client import neo4j_client
print("DEBUG: Importing RAGRetriever...")
from retrieval.rag_retriever import RAGRetriever
print("DEBUG: All imports done")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_hybrid_chunker():
    logger.info("--- 测试混合分块器 ---")
    text = """
    # RAG 系统介绍
    RAG (Retrieval-Augmented Generation) 是一种结合检索和生成的技术。
    
    ## 公式
    下面是一个简单的公式：
    $$ E = mc^2 $$
    
    ## 代码示例
    ```python
    def hello():
        print("Hello World")
    ```
    
    ## 表格
    | 组件 | 描述 |
    | --- | --- |
    | Retriever | 检索器 |
    | Generator | 生成器 |
    """
    
    chunker = HybridChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk(text)
    
    logger.info(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        logger.info(f"块 {i+1} [{chunk['metadata'].get('content_type')}]: {chunk['text'][:50]}...")
    
    return chunks

async def test_knowledge_extraction(chunks):
    logger.info("\n--- 测试知识抽取与图谱构建 ---")
    
    # 检查 Neo4j 连接
    neo4j_client.connect()
    if not neo4j_client.driver:
        logger.warning("Neo4j 连接失败，跳过图谱构建测试")
        return

    # 选取一个文本块进行测试
    text_chunks = [c for c in chunks if c['metadata'].get('content_type') == 'text']
    if not text_chunks:
        logger.warning("没有文本块，跳过")
        return

    test_chunk = text_chunks[0]
    logger.info(f"正在从以下文本抽取知识: {test_chunk['text'][:100]}...")
    
    # 模拟入库
    await knowledge_extraction_service.build_graph(
        test_chunk['text'], 
        metadata={"document_id": "test_doc_001", "chunk_id": "test_chunk_001"}
    )
    logger.info("知识抽取与入库完成 (请检查 Neo4j)")

async def test_retrieval():
    logger.info("\n--- 测试混合检索 ---")
    
    retriever = RAGRetriever(top_k=3)
    query = "RAG 系统是什么？"
    
    # 注意：这里可能因为没有向量库数据而检索不到向量结果，
    # 但如果图谱构建成功，可能会有图谱结果（如果 query 能提取出实体）
    
    logger.info(f"执行检索: {query}")
    results = await retriever.retrieve_async(query)
    
    logger.info(f"检索结果数量: {len(results)}")
    for i, res in enumerate(results):
        logger.info(f"结果 {i+1} [{res['payload'].get('retrieval_type')}]: {res['payload'].get('text')[:100]}...")

async def main():
    print("DEBUG: Starting main()")
    try:
        print("DEBUG: Calling test_hybrid_chunker()")
        chunks = await test_hybrid_chunker()
        print(f"DEBUG: test_hybrid_chunker returned {len(chunks)} chunks")
        
        print("DEBUG: Calling test_knowledge_extraction()")
        await test_knowledge_extraction(chunks)
        print("DEBUG: test_knowledge_extraction done")
        
        print("DEBUG: Calling test_retrieval()")
        await test_retrieval()
        print("DEBUG: test_retrieval done")
        
        logger.info("\n=== 所有测试完成 ===")
    except Exception as e:
        print(f"DEBUG: Exception in main: {e}")
        logger.error(f"测试过程中出错: {e}", exc_info=True)

if __name__ == "__main__":
    print("DEBUG: Script started")
    asyncio.run(main())
    print("DEBUG: Script finished")
