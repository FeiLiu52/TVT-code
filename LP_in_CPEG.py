import yaml
from gurobipy import *
from CPEG import expand_network
import time
import os
from pathlib import Path

def load_network_from_yaml(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    nodes = [str(node) for node in data['nodes']]
    edges = [(str(edge['source']), str(edge['destination']), {
        'bandwidth': edge['bandwidth'],
        'propagation_delay': edge['propagation_delay'],
        'processing_delay': edge['processing_delay'],
        'queuing_delay': edge['queuing_delay'],
        'jitter': edge['jitter']
    }) for edge in data['edges']]
    compute_nodes = [str(node) for node in data.get('compute_nodes', [])]
    
    # 处理 compute_node_capacity 是列表的情况
    compute_node_capacity = data.get('compute_node_capacity', [])
    if isinstance(compute_node_capacity, list):
        if len(compute_node_capacity) == len(compute_nodes):
            compute_capacities = {str(node): capacity for node, capacity in zip(compute_nodes, compute_node_capacity)}
    if isinstance(compute_node_capacity, dict):
        compute_capacities = {str(node): capacity for node, capacity in compute_node_capacity.items()}

    source_node = str(data['source_node'])
    destination_node = str(data['destination_node'])
    
    flow_size = data.get('flow_size', 1)
    gamma = data.get('gamma', 2)
    omega = data.get('omega', 10)
    
    return nodes, edges, compute_nodes, compute_capacities, source_node, destination_node, flow_size, gamma, omega

def d_uv(u, v, layer, edge_data):
    # 检查 edge_data 是否为字典
    if not isinstance(edge_data, dict):
        # print(f"警告：edge_data 不是字典。u={u}, v={v}, layer={layer}, edge_data={edge_data}")
        return 0  # 或者返回一个默认值
    
    if layer == 'C-UCL':
        transmission_delay = flow_size / edge_data.get('bandwidth', 1)
        non_transmission_delay = (edge_data.get('propagation_delay', 0) + 
                                  edge_data.get('processing_delay', 0) + 
                                  edge_data.get('queuing_delay', 0) + 
                                  edge_data.get('jitter', 0))
        return transmission_delay + non_transmission_delay
    elif layer == 'C-DCL':
        transmission_delay = gamma * flow_size / edge_data.get('bandwidth', 1)
        non_transmission_delay = (edge_data.get('propagation_delay', 0) + 
                                  edge_data.get('processing_delay', 0) + 
                                  edge_data.get('queuing_delay', 0) + 
                                  edge_data.get('jitter', 0))
        return transmission_delay + non_transmission_delay
    elif layer == 'UCL-CL':
        compute_node = v.split('_')[0]  # 获取计算节点的原始名称
        compute_capacity = compute_capacities.get(compute_node, 1)  # 获取计算节点的计算容量
        computing_delay = omega * flow_size / compute_capacity
        return computing_delay
    elif layer == 'CL-DCL':
        return 0
    else:
        return 0  # 其他情况


# 获取当前文件所在目录
CURRENT_DIR = os.path.dirname(__file__)
yaml_file_path = os.path.join(CURRENT_DIR, "random_network.yaml")

original_nodes, original_edges, compute_nodes, compute_capacities, source_node, destination_node, flow_size, gamma, omega = load_network_from_yaml(yaml_file_path)

# 扩展网络
V, E = expand_network(original_nodes, original_edges, compute_nodes, compute_capacities, source_node, destination_node)


# 创建数学模型
model = Model("Network_Optimization")

# 定义决策变量
x = model.addVars([(u, v) for u, v, _, _ in E], vtype=GRB.BINARY, name="x")

# 设置目标函数
model.setObjective(quicksum(x[u, v] * d_uv(u, v, layer, edge_data) for u, v, edge_data, layer in E), GRB.MINIMIZE)

# 添加约束条件
# 源节点约束
model.addConstr(quicksum(x[source_node, v] for v in V if (source_node, v) in x) -
                quicksum(x[v, source_node] for v in V if (v, source_node) in x) == 1)

# 目的节点约束
dest_node_dcl = destination_node + '_3'  # 在DCL层中的目的节点
model.addConstr(quicksum(x[u, dest_node_dcl] for u in V if (u, dest_node_dcl) in x) -
                quicksum(x[dest_node_dcl, w] for w in V if (dest_node_dcl, w) in x) == 1)

# source_node_dcl = source_node + '_3'  # 在DCL层中的源节点
# model.addConstr(quicksum(x[source_node_dcl, v] for v in V if (source_node_dcl, v) in x)  == 0)

# 流量守恒约束
for v in V:
    if v not in [source_node, dest_node_dcl]:  # 排除源节点和目的节点
        model.addConstr(
            quicksum(x[u, v] for u in V if (u, v) in x) == 
            quicksum(x[v, w] for w in V if (v, w) in x)
        )
# 开始计时
LP_start_time = time.time()

# 优化模型
model.optimize()

# 计时结束
LP_end_time = time.time()

# # 打印优化目标
# print("优化目标:")
# print(model.getObjective())

def print_selected_path(x, V, source_node, dest_node_dcl):
    path = [source_node]
    current_node = source_node
    while current_node != dest_node_dcl:
        for v in V:
            if (current_node, v) in x and x[current_node, v].x > 0.5:
                path.append(v)
                current_node = v
                break
        else:
            print("无法找到完整路径")
            return
    
    print("选择的路径:")
    for i in range(len(path) - 1):
        print(f"{path[i]} -> {path[i+1]}")

# 输出结果
if model.status == GRB.OPTIMAL:
    print("找到最优解")
    print_selected_path(x, V, source_node, dest_node_dcl)
    # print(f"端到端总时延 = {model.objVal}")
else:
    print("未找到最优解")

# print(f"LP_start_time = {LP_start_time}")
# print(f"LP_end_time = {LP_end_time}")
# print(f"LP_running_time = {LP_end_time - LP_start_time}")

end_to_end_delay = model.objVal
running_time = LP_end_time - LP_start_time

print(f"END_TO_END_DELAY:{end_to_end_delay}")
print(f"RUNNING_TIME:{running_time}")