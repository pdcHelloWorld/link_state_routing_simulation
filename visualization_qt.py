import sys
import networkx as nx
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QLabel, QComboBox, QTreeWidget, QTreeWidgetItem,
                            QDialog, QLineEdit, QGridLayout, QMessageBox, QGroupBox,
                            QSplitter, QFrame, QHeaderView, QInputDialog, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QPainterPath
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import threading


class NetworkVizCanvas(FigureCanvas):
    """PyQt网络可视化画布，使用matplotlib绘制网络拓扑"""
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_axis_off()  # 隐藏坐标轴
        
        super(NetworkVizCanvas, self).__init__(self.fig)
        self.setParent(parent)
        
        self.graph = nx.Graph()
        self.pos = None
    
    def draw_network(self, nodes, links):
        """绘制网络拓扑"""
        self.axes.clear()
        self.graph.clear()
        
        # 添加节点和边
        for node_id in nodes:
            self.graph.add_node(node_id)
        
        for (src, dst), cost in links.items():
            self.graph.add_edge(src, dst, weight=cost)
        
        # 计算节点位置
        self.pos = nx.spring_layout(self.graph)
        
        # 绘制节点
        nx.draw_networkx_nodes(self.graph, self.pos, ax=self.axes, node_size=700, 
                              node_color='lightblue', edgecolors='black')
        
        # 绘制节点标签
        nx.draw_networkx_labels(self.graph, self.pos, ax=self.axes, font_size=14, font_weight='bold')
        
        # 绘制边
        nx.draw_networkx_edges(self.graph, self.pos, ax=self.axes, width=2.0, alpha=0.7)
        
        # 绘制边标签
        edge_labels = {(src, dst): cost for (src, dst), cost in links.items()}
        nx.draw_networkx_edge_labels(self.graph, self.pos, edge_labels=edge_labels, 
                                    ax=self.axes, font_size=12, font_color='red')
        
        self.fig.canvas.draw()


class AddLinkDialog(QDialog):
    """添加链路对话框"""
    def __init__(self, parent, nodes):
        super().__init__(parent)
        self.setWindowTitle("添加链路")
        self.setMinimumWidth(300)
        self.result_data = None
        self.nodes = nodes
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        # 第一个节点选择器
        layout.addWidget(QLabel("选择第一个节点:"), 0, 0)
        self.node1_combo = QComboBox()
        self.node1_combo.addItems(nodes)
        layout.addWidget(self.node1_combo, 0, 1)
        
        # 第二个节点选择器
        layout.addWidget(QLabel("选择第二个节点:"), 1, 0)
        self.node2_combo = QComboBox()
        self.node2_combo.addItems(nodes)
        if len(nodes) > 1:
            self.node2_combo.setCurrentIndex(1)
        layout.addWidget(self.node2_combo, 1, 1)
        
        # 代价输入框
        layout.addWidget(QLabel("链路代价:"), 2, 0)
        self.cost_edit = QLineEdit("1")
        layout.addWidget(self.cost_edit, 2, 1)
        
        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        ok_btn.clicked.connect(self.on_ok)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout, 3, 0, 1, 2)
    
    def on_ok(self):
        """确定按钮处理"""
        node1 = self.node1_combo.currentText()
        node2 = self.node2_combo.currentText()
        
        try:
            cost = float(self.cost_edit.text())
            if cost <= 0:
                raise ValueError("代价必须大于0")
        except ValueError as e:
            QMessageBox.critical(self, "错误", f"无效的代价: {e}")
            return
        
        if node1 == node2:
            QMessageBox.critical(self, "错误", "不能连接相同的节点")
            return
        
        self.result_data = (node1, node2, cost)
        self.accept()


class UpdateLinkDialog(QDialog):
    """更新链路代价对话框"""
    def __init__(self, parent, links):
        super().__init__(parent)
        self.setWindowTitle("更新链路代价")
        self.setMinimumWidth(300)
        self.result_data = None
        self.links = links
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        # 链路选择器
        layout.addWidget(QLabel("选择链路:"), 0, 0)
        self.link_combo = QComboBox()
        link_strs = [f"{src} - {dst} (当前代价: {cost})" for (src, dst), cost in links]
        self.link_combo.addItems(link_strs)
        layout.addWidget(self.link_combo, 0, 1)
        
        # 代价输入框
        layout.addWidget(QLabel("新链路代价:"), 1, 0)
        self.cost_edit = QLineEdit("1")
        layout.addWidget(self.cost_edit, 1, 1)
        
        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        ok_btn.clicked.connect(self.on_ok)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout, 2, 0, 1, 2)
    
    def on_ok(self):
        """确定按钮处理"""
        index = self.link_combo.currentIndex()
        if index < 0 or index >= len(self.links):
            QMessageBox.critical(self, "错误", "请选择一个链路")
            return
        
        link_info, old_cost = self.links[index]
        
        try:
            cost = float(self.cost_edit.text())
            if cost <= 0:
                raise ValueError("代价必须大于0")
        except ValueError as e:
            QMessageBox.critical(self, "错误", f"无效的代价: {e}")
            return
        
        self.result_data = (link_info, cost)
        self.accept()


class RemoveLinkDialog(QDialog):
    """删除链路对话框"""
    def __init__(self, parent, links):
        super().__init__(parent)
        self.setWindowTitle("删除链路")
        self.setMinimumWidth(300)
        self.result_data = None
        self.links = links
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        # 链路选择器
        layout.addWidget(QLabel("选择要删除的链路:"), 0, 0)
        self.link_combo = QComboBox()
        link_strs = [f"{src} - {dst} (代价: {cost})" for (src, dst), cost in links]
        self.link_combo.addItems(link_strs)
        layout.addWidget(self.link_combo, 0, 1)
        
        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        ok_btn.clicked.connect(self.on_ok)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout, 1, 0, 1, 2)
    
    def on_ok(self):
        """确定按钮处理"""
        index = self.link_combo.currentIndex()
        if index < 0 or index >= len(self.links):
            QMessageBox.critical(self, "错误", "请选择一个链路")
            return
        
        (src, dst), _ = self.links[index]
        self.result_data = (src, dst)
        self.accept()


class NetworkVisualizerQt(QMainWindow):
    """基于PyQt的网络拓扑可视化类"""
    
    def __init__(self, network):
        super().__init__()
        self.network = network
        self.protocol_running = False
        
        self.init_ui()
        
        # 刷新界面
        self.update_graph()
        self.update_node_selector()
    
    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("链路状态路由协议仿真系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建顶部控制面板
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        # 添加各种按钮
        self.add_node_btn = QPushButton("添加节点")
        self.add_node_btn.clicked.connect(self.add_node)
        control_layout.addWidget(self.add_node_btn)
        
        self.add_link_btn = QPushButton("添加链路")
        self.add_link_btn.clicked.connect(self.add_link)
        control_layout.addWidget(self.add_link_btn)
        
        self.update_link_btn = QPushButton("修改链路代价")
        self.update_link_btn.clicked.connect(self.update_link_cost)
        control_layout.addWidget(self.update_link_btn)
        
        self.remove_link_btn = QPushButton("删除链路")
        self.remove_link_btn.clicked.connect(self.remove_link)
        control_layout.addWidget(self.remove_link_btn)
        
        self.toggle_protocol_btn = QPushButton("启动路由协议")
        self.toggle_protocol_btn.clicked.connect(self.toggle_protocol)
        control_layout.addWidget(self.toggle_protocol_btn)
        
        self.save_topo_btn = QPushButton("保存拓扑")
        self.save_topo_btn.clicked.connect(self.save_topology)
        control_layout.addWidget(self.save_topo_btn)
        
        self.load_topo_btn = QPushButton("加载拓扑")
        self.load_topo_btn.clicked.connect(self.load_topology)
        control_layout.addWidget(self.load_topo_btn)
        
        main_layout.addWidget(control_frame)
        
        # 创建拓扑图和路由表的分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 拓扑图区域
        graph_group = QGroupBox("网络拓扑")
        graph_layout = QVBoxLayout(graph_group)
        
        self.canvas = NetworkVizCanvas()
        graph_layout.addWidget(self.canvas)
        
        # 路由表区域
        route_group = QGroupBox("路由表")
        route_layout = QVBoxLayout(route_group)
        
        # 节点选择器
        node_selector_layout = QHBoxLayout()
        node_selector_layout.addWidget(QLabel("选择节点:"))
        self.node_selector = QComboBox()
        self.node_selector.currentIndexChanged.connect(self.update_routing_table_display)
        node_selector_layout.addWidget(self.node_selector)
        route_layout.addLayout(node_selector_layout)
        
        # 路由表显示
        self.routing_table = QTreeWidget()
        self.routing_table.setHeaderLabels(["目的节点", "下一跳", "代价"])
        self.routing_table.header().setSectionResizeMode(QHeaderView.Stretch)
        
        # 设置每列的最小宽度，确保表头文字完整显示
        self.routing_table.setColumnWidth(0, 100)
        self.routing_table.setColumnWidth(1, 100)
        self.routing_table.setColumnWidth(2, 80)
        
        route_layout.addWidget(self.routing_table)
        
        # 添加到分割器
        splitter.addWidget(graph_group)
        splitter.addWidget(route_group)
        splitter.setStretchFactor(0, 1)  # 拓扑图占比改为2
        splitter.setStretchFactor(1, 1)  # 路由表占比维持1
        
        main_layout.addWidget(splitter)
        
        # 设置定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_routing_table_display)
    
    def update_graph(self):
        """更新网络拓扑图"""
        self.canvas.draw_network(
            self.network.get_all_nodes(),
            self.network.get_all_links()
        )
    
    def update_node_selector(self):
        """更新节点选择器"""
        self.node_selector.blockSignals(True)
        current_text = self.node_selector.currentText()
        self.node_selector.clear()
        
        nodes = self.network.get_all_nodes()
        self.node_selector.addItems(nodes)
        
        # 尝试保持当前选择
        if current_text in nodes:
            index = self.node_selector.findText(current_text)
            self.node_selector.setCurrentIndex(index)
        elif nodes:
            self.node_selector.setCurrentIndex(0)
            
        self.node_selector.blockSignals(False)
        self.update_routing_table_display()
    
    def update_routing_table_display(self):
        """更新路由表显示"""
        self.routing_table.clear()
        
        # 获取选中节点
        node_id = self.node_selector.currentText()
        if not node_id or node_id not in self.network.nodes:
            return
        
        # 获取该节点的路由表
        router = self.network.nodes[node_id]
        routing_table = router.get_routing_table()
        
        # 添加到表格
        for destination, (next_hop, cost) in routing_table.items():
            item = QTreeWidgetItem([destination, next_hop, str(cost)])
            self.routing_table.addTopLevelItem(item)
    
    def add_node(self):
        """添加新节点"""
        node_id, ok = QInputDialog.getText(self, "添加节点", "输入节点ID:")
        if ok and node_id:
            if self.network.add_node(node_id):
                self.update_graph()
                self.update_node_selector()
            else:
                QMessageBox.critical(self, "错误", f"节点 {node_id} 已存在")
    
    def add_link(self):
        """添加新链路"""
        nodes = self.network.get_all_nodes()
        if len(nodes) < 2:
            QMessageBox.critical(self, "错误", "至少需要两个节点才能添加链路")
            return
        
        dialog = AddLinkDialog(self, nodes)
        if dialog.exec_() == QDialog.Accepted and dialog.result_data:
            node1, node2, cost = dialog.result_data
            if self.network.add_link(node1, node2, cost):
                self.update_graph()
            else:
                QMessageBox.critical(self, "错误", "添加链路失败")
    
    def update_link_cost(self):
        """更新链路代价"""
        links = list(self.network.get_all_links().items())
        if not links:
            QMessageBox.critical(self, "错误", "没有可修改的链路")
            return
        
        dialog = UpdateLinkDialog(self, links)
        if dialog.exec_() == QDialog.Accepted and dialog.result_data:
            (src, dst), cost = dialog.result_data
            if self.network.update_link_cost(src, dst, cost):
                self.update_graph()
            else:
                QMessageBox.critical(self, "错误", "更新链路代价失败")
    
    def remove_link(self):
        """删除链路"""
        links = list(self.network.get_all_links().items())
        if not links:
            QMessageBox.critical(self, "错误", "没有可删除的链路")
            return
        
        dialog = RemoveLinkDialog(self, links)
        if dialog.exec_() == QDialog.Accepted and dialog.result_data:
            src, dst = dialog.result_data
            if self.network.remove_link(src, dst):
                self.update_graph()
            else:
                QMessageBox.critical(self, "错误", "删除链路失败")
    
    def toggle_protocol(self):
        """启动/停止路由协议"""
        if self.protocol_running:
            self.network.stop_all_routers()
            self.protocol_running = False
            self.toggle_protocol_btn.setText("启动路由协议")
            self.update_timer.stop()
        else:
            self.network.start_all_routers()
            self.protocol_running = True
            self.toggle_protocol_btn.setText("停止路由协议")
            self.update_timer.start(1000)  # 每秒更新一次路由表
    
    def save_topology(self):
        """保存拓扑到文件"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存拓扑", "topology/custom.json", "JSON Files (*.json)"
        )
        
        if filename:
            self.network.save_to_file(filename)
            QMessageBox.information(self, "成功", f"拓扑已保存到 {filename}")
    
    def load_topology(self):
        """从文件加载拓扑"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "加载拓扑", "topology/default.json", "JSON Files (*.json)"
        )
        
        if filename:
            if self.network.load_from_file(filename):
                # 如果协议正在运行，先停止
                if self.protocol_running:
                    self.network.stop_all_routers()
                    self.protocol_running = False
                    self.toggle_protocol_btn.setText("启动路由协议")
                    self.update_timer.stop()
                
                self.update_graph()
                self.update_node_selector()
                QMessageBox.information(self, "成功", f"已加载拓扑 {filename}")
            else:
                QMessageBox.critical(self, "错误", f"无法加载拓扑 {filename}")
