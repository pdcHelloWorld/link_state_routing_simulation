import threading
import time
from link_state import LinkStateProtocol
from dijkstra import calculate_shortest_paths

class Router:
    """路由器类，代表网络中的一个节点"""
    
    def __init__(self, node_id, network):
        self.node_id = node_id
        self.network = network
        self.routing_table = {}  # 路由表: {目的节点: (下一跳, 距离)}
        self.link_state_protocol = LinkStateProtocol(self)
        self.is_running = False
        self.lock = threading.RLock()
    
    def start_link_state_protocol(self):
        """启动链路状态协议"""
        self.is_running = True
        self.link_state_protocol.start()
    
    def stop_link_state_protocol(self):
        """停止链路状态协议"""
        self.is_running = False
        self.link_state_protocol.stop()
    
    def get_neighbors(self):
        """获取邻居节点"""
        return self.network.get_neighbors(self.node_id)
    
    def notify_link_change(self, neighbor, cost):
        """通知链路状态变化"""
        if self.is_running:
            self.link_state_protocol.update_link_state(neighbor, cost)
    
    def receive_lsa(self, source_id, lsa_data):
        """接收并处理链路状态通告"""
        self.link_state_protocol.process_lsa(source_id, lsa_data)
    
    def update_routing_table(self, topology):
        """基于拓扑信息更新路由表"""
        with self.lock:
            self.routing_table = calculate_shortest_paths(topology, self.node_id)
    
    def get_routing_table(self):
        """获取路由表"""
        with self.lock:
            return self.routing_table.copy()
    
    def forward_packet(self, destination):
        """转发数据包到指定目的地（仿真）"""
        with self.lock:
            if destination in self.routing_table:
                next_hop, distance = self.routing_table[destination]
                return next_hop
            else:
                return None  # 目的地不可达