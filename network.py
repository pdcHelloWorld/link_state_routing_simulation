import json
import os
import threading
import time

class NetworkTopology:
    """网络拓扑类，用于管理网络节点和链路"""
    
    def __init__(self):
        self.nodes = {}  # 存储网络中的节点 {节点ID: 节点对象}
        self.links = {}  # 存储网络中的链路 {(node1, node2): cost}
        self.lock = threading.RLock()  # 用于同步访问
        
    def add_node(self, node_id):
        """添加节点到拓扑中"""
        with self.lock:
            if node_id not in self.nodes:
                from router import Router
                self.nodes[node_id] = Router(node_id, self)
                return True
            return False
    
    def add_link(self, node1, node2, cost):
        """添加链路到拓扑中"""
        with self.lock:
            if node1 in self.nodes and node2 in self.nodes:
                self.links[(node1, node2)] = cost
                self.links[(node2, node1)] = cost
                return True
            return False
    
    def update_link_cost(self, node1, node2, cost):
        """更新链路代价"""
        with self.lock:
            if (node1, node2) in self.links:
                self.links[(node1, node2)] = cost
                self.links[(node2, node1)] = cost
                # 通知节点链路变化
                self.nodes[node1].notify_link_change(node2, cost)
                self.nodes[node2].notify_link_change(node1, cost)
                return True
            return False
    
    def remove_link(self, node1, node2):
        """移除链路"""
        with self.lock:
            if (node1, node2) in self.links:
                del self.links[(node1, node2)]
                del self.links[(node2, node1)]
                # 通知节点链路变化
                self.nodes[node1].notify_link_change(node2, float('inf'))
                self.nodes[node2].notify_link_change(node1, float('inf'))
                return True
            return False
    
    def get_neighbors(self, node_id):
        """获取节点的邻居节点及链路代价"""
        neighbors = {}
        for (src, dst), cost in self.links.items():
            if src == node_id:
                neighbors[dst] = cost
        return neighbors
    
    def get_all_nodes(self):
        """获取所有节点ID"""
        return list(self.nodes.keys())
    
    def get_all_links(self):
        """获取所有链路信息，用于可视化"""
        unique_links = {}
        for (src, dst), cost in self.links.items():
            if src < dst:  # 只返回单向链路，避免重复
                unique_links[(src, dst)] = cost
        return unique_links
    
    def save_to_file(self, filename):
        """将拓扑保存到文件"""
        with self.lock:
            topology_data = {
                "nodes": list(self.nodes.keys()),
                "links": []
            }
            
            for (src, dst), cost in self.links.items():
                if src < dst:  # 只保存单向链路，避免重复
                    topology_data["links"].append({
                        "source": src,
                        "target": dst,
                        "cost": cost
                    })
            
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(topology_data, f, indent=4)
    
    def load_from_file(self, filename):
        """从文件加载拓扑"""
        with self.lock:
            try:
                with open(filename, 'r') as f:
                    topology_data = json.load(f)
                
                # 清空当前拓扑
                self.nodes.clear()
                self.links.clear()
                
                # 添加节点
                for node_id in topology_data["nodes"]:
                    self.add_node(node_id)
                
                # 添加链路
                for link in topology_data["links"]:
                    self.add_link(link["source"], link["target"], link["cost"])
                
                return True
            except Exception as e:
                print(f"加载拓扑失败: {e}")
                return False
    
    def start_all_routers(self):
        """启动所有路由器的链路状态协议"""
        for router in self.nodes.values():
            router.start_link_state_protocol()
    
    def stop_all_routers(self):
        """停止所有路由器的链路状态协议"""
        for router in self.nodes.values():
            router.stop_link_state_protocol()