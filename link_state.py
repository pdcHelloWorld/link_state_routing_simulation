import threading
import time
import copy
import random

class LinkStateProtocol:
    """链路状态协议实现类"""
    
    def __init__(self, router):
        self.router = router
        self.link_state_database = {}  # 链路状态数据库: {节点ID: {邻居ID: 代价}}
        self.sequence_numbers = {}  # 序列号: {节点ID: 序号}
        self.lsa_thread = None
        self.running = False
        self.lock = threading.RLock()
    
    def start(self):
        """启动链路状态协议"""
        with self.lock:
            if not self.running:
                self.running = True
                # 初始化链路状态数据库
                self.link_state_database = {}
                self.sequence_numbers = {}
                
                # 添加本节点的链路状态
                neighbors = self.router.get_neighbors()
                self.link_state_database[self.router.node_id] = neighbors
                self.sequence_numbers[self.router.node_id] = 1
                
                # 启动链路状态广告线程
                self.lsa_thread = threading.Thread(target=self._lsa_sender_thread)
                self.lsa_thread.daemon = True
                self.lsa_thread.start()
                
                # 首次发送LSA
                self._send_lsa()
    
    def stop(self):
        """停止链路状态协议"""
        with self.lock:
            if self.running:
                self.running = False
                if self.lsa_thread and self.lsa_thread.is_alive():
                    self.lsa_thread.join(1.0)  # 等待线程结束，最多1秒
    
    def update_link_state(self, neighbor, cost):
        """更新本地链路状态"""
        with self.lock:
            if not self.running:
                return
                
            neighbors = self.link_state_database.get(self.router.node_id, {})
            if cost == float('inf'):  # 链路断开
                if neighbor in neighbors:
                    del neighbors[neighbor]
            else:
                neighbors[neighbor] = cost
                
            self.link_state_database[self.router.node_id] = neighbors
            
            # 增加序列号
            seq = self.sequence_numbers.get(self.router.node_id, 0) + 1
            self.sequence_numbers[self.router.node_id] = seq
            
            # 立即发送LSA
            self._send_lsa()
            
            # 重新计算路由表
            self._recalculate_routes()
    
    def process_lsa(self, source_id, lsa_data):
        """处理接收到的链路状态通告"""
        with self.lock:
            if not self.running:
                return
                
            node_id, seq_num, neighbors = lsa_data
            
            # 检查序列号，避免处理旧的LSA
            current_seq = self.sequence_numbers.get(node_id, 0)
            if seq_num <= current_seq:
                return  # 忽略旧的或重复的LSA
                
            # 更新链路状态数据库和序列号
            self.link_state_database[node_id] = neighbors
            self.sequence_numbers[node_id] = seq_num
            
            # 转发LSA给除了源节点外的所有邻居
            for neighbor in self.router.get_neighbors():
                if neighbor != source_id:
                    self._forward_lsa_to_neighbor(neighbor, lsa_data)
            
            # 重新计算路由表
            self._recalculate_routes()
    
    def _send_lsa(self):
        """发送链路状态通告给所有邻居"""
        if not self.running:
            return
            
        neighbors = self.router.get_neighbors()
        if not neighbors:
            return
            
        # 准备LSA数据
        lsa_data = (
            self.router.node_id,
            self.sequence_numbers.get(self.router.node_id, 1),
            copy.deepcopy(self.link_state_database.get(self.router.node_id, {}))
        )
        
        # 发送给所有邻居
        for neighbor in neighbors:
            self._forward_lsa_to_neighbor(neighbor, lsa_data)
    
    def _forward_lsa_to_neighbor(self, neighbor, lsa_data):
        """转发LSA到指定邻居"""
        # 在实际网络中，这里会通过网络发送消息
        # 在仿真中，我们直接调用邻居的接收方法
        if neighbor in self.router.network.nodes:
            neighbor_router = self.router.network.nodes[neighbor]
            neighbor_router.receive_lsa(self.router.node_id, lsa_data)
    
    def _lsa_sender_thread(self):
        """周期性发送LSA的后台线程"""
        while self.running:
            # 随机等待一段时间，避免同步发送
            time.sleep(random.uniform(5, 15))
            
            with self.lock:
                if self.running:
                    self._send_lsa()
    
    def _recalculate_routes(self):
        """重新计算路由表"""
        # 将链路状态数据库转换为适合Dijkstra算法的拓扑结构
        topology = self._build_topology_from_lsdb()
        
        # 更新路由表
        self.router.update_routing_table(topology)
    
    def _build_topology_from_lsdb(self):
        """从链路状态数据库构建拓扑结构"""
        topology = {}
        
        # 对于链路状态数据库中的每个节点
        for node_id, neighbors in self.link_state_database.items():
            if node_id not in topology:
                topology[node_id] = {}
                
            # 添加该节点到其邻居的连接
            for neighbor, cost in neighbors.items():
                topology[node_id][neighbor] = cost
                
                # 确保邻居节点也在拓扑中
                if neighbor not in topology:
                    topology[neighbor] = {}
        
        return topology