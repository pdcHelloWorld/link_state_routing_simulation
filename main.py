import os
import sys
from PyQt5.QtWidgets import QApplication
from network import NetworkTopology
from visualization_qt import NetworkVisualizerQt

def create_default_topology(network):
    """创建默认的网络拓扑供测试使用"""
    # 添加节点
    nodes = ["A", "B", "C", "D", "E", "F"]
    for node in nodes:
        network.add_node(node)
    
    # 添加链路
    links = [
        ("A", "B", 1),
        ("A", "C", 3),
        ("B", "C", 1),
        ("B", "D", 5),
        ("C", "D", 2),
        ("C", "E", 4),
        ("D", "E", 1),
        ("D", "F", 2),
        ("E", "F", 3)
    ]
    for src, dst, cost in links:
        network.add_link(src, dst, cost)
    
    # 保存默认拓扑
    os.makedirs("topology", exist_ok=True)
    network.save_to_file("topology/default.json")

def main():
    """主程序入口"""
    # 创建Qt应用
    app = QApplication(sys.argv)
    
    # 创建网络拓扑
    network = NetworkTopology()
    
    # 如果没有默认拓扑文件，创建一个
    if not os.path.exists("link_state_routing_simulation/topology/default.json"):
        create_default_topology(network)
    else:
        network.load_from_file("link_state_routing_simulation/topology/default.json")
    
    # 创建可视化界面
    visualizer = NetworkVisualizerQt(network)
    visualizer.show()
    
    # 运行主循环
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()