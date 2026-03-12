
import os
from neo4j import GraphDatabase
from utils.logger import logger

class Neo4jClient:
    """Neo4j 知识图谱数据库客户端"""
    
    def __init__(self):
        """初始化 Neo4j 客户端配置"""
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
        
    def connect(self):
        """建立连接"""
        if self.driver is None:
            try:
                # 兼容容器环境：如果在容器内运行且 URI 为 localhost，尝试替换为 host.docker.internal
                if "host.docker.internal" not in self.uri and "localhost" in self.uri:
                     # 检查是否在容器内运行（简单判断：检查 /.dockerenv 文件是否存在）
                     if os.path.exists("/.dockerenv"):
                         self.uri = self.uri.replace("localhost", "host.docker.internal")
                
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                # 验证连接
                self.driver.verify_connectivity()
                logger.info(f"Neo4j 连接成功: {self.uri}")
            except Exception as e:
                logger.error(f"Neo4j 连接失败: {e}")
                self.driver = None
                
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.driver = None
            
    def execute_query(self, query: str, parameters: dict = None):
        """
        执行 Cypher 查询
        
        Args:
            query: Cypher 查询语句
            parameters: 查询参数字典
            
        Returns:
            查询结果列表（字典格式），如果失败返回 None
        """
        if self.driver is None:
            self.connect()
        if self.driver is None:
            return None
            
        with self.driver.session() as session:
            try:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"Neo4j 查询失败: {e}\nQuery: {query}")
                return None

    def create_entity(self, label: str, properties: dict):
        """
        创建实体节点
        
        Args:
            label: 节点标签（类型）
            properties: 节点属性字典（必须包含 name）
        """
        query = f"MERGE (n:{label} {{name: $name}}) SET n += $props RETURN n"
        params = {"name": properties.get("name"), "props": properties}
        return self.execute_query(query, params)

    def create_relationship(self, start_node_name: str, start_label: str, 
                            end_node_name: str, end_label: str, 
                            rel_type: str, rel_props: dict = None):
        """
        创建关系
        
        Args:
            start_node_name: 起始节点名称
            start_label: 起始节点标签
            end_node_name: 目标节点名称
            end_label: 目标节点标签
            rel_type: 关系类型
            rel_props: 关系属性字典
        """
        query = (
            f"MATCH (a:{start_label} {{name: $start_name}}), (b:{end_label} {{name: $end_name}}) "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            f"SET r += $rel_props "
            f"RETURN r"
        )
        params = {
            "start_name": start_node_name,
            "end_name": end_node_name,
            "rel_props": rel_props or {}
        }
        return self.execute_query(query, params)

neo4j_client = Neo4jClient()
