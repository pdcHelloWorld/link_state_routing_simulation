import heapq

def calculate_shortest_paths(topology, source):
    """
    使用Dijkstra算法计算从source节点到所有其他节点的最短路径
    
    参数:
        topology: {node_id: {neighbor_id: cost, ...}, ...} 格式的拓扑结构
        source: 源节点ID
    
    返回:
        {destination: (next_hop, distance), ...} 格式的路由表
    """
    # 初始化距离和前驱节点
    distances = {node: float('infinity') for node in topology}
    predecessors = {node: None for node in topology}
    distances[source] = 0
    
    # 优先队列存储(距离, 节点)元组
    priority_queue = [(0, source)]
    
    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)
        
        # 如果已经找到更短的路径，则跳过
        if current_distance > distances[current_node]:
            continue
        
        # 检查当前节点的邻居
        for neighbor, weight in topology.get(current_node, {}).items():
            distance = current_distance + weight
            
            # 如果找到更短的路径
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                predecessors[neighbor] = current_node
                heapq.heappush(priority_queue, (distance, neighbor))
    
    # 构建路由表
    routing_table = {}
    
    for destination in topology:
        if destination == source:
            continue  # 跳过自身
            
        if distances[destination] == float('infinity'):
            continue  # 目的地不可达
        
        # 查找从source到destination的第一跳
        next_hop = destination
        while predecessors[next_hop] != source and predecessors[next_hop] is not None:
            next_hop = predecessors[next_hop]
        
        if predecessors[next_hop] is None:
            continue  # 没有路径
            
        routing_table[destination] = (next_hop, distances[destination])
    
    return routing_table