# edge_number = 5
# client_number = 1000
# group_number_list = [200, 200, 200, 200, 200]
edge_number = 10
client_number = 1000
group_number_list = [100, 100, 100, 100, 100,100, 100, 100, 100, 100]
# edge_number = 1
# client_number = 1000
# group_number_list = [1000]
# edge_number = 10
# client_number = 100
# group_number_list = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]

# TD
K = client_number
M = 20
count = 20

# datagenerate
base_data_rate = 1  # 随即生成地面真值之后乘以的倍数(更加分散)
base_data_start = 1  # 随机生成地面真值的起点
base_data_end = 200  # 随机生成地面真值的终点
reliable_client_rate = 101  # 可靠用户的比例,0-100 越接近100 可靠用户越多
unreliable_start = 99
unreliable_end = 99
reliable_start = 0.9
reliable_end = 0.9

unreliable__ = 99

miss_rate = 0/100  # 用户掉线情况 0表示不缺失,越接近1 缺失越多
# miss_number = 1000/1000  # 用户掉线个数 1表示不缺失,越接近0 缺失越多
extreme_client_rate = 0/1000  # 提交极端值的用户比率 越接近1 越多
extreme_client_number = 0  # 提交极端值的用户个数
extreme_task_rate = 1  # 提交极端值的用户任务极端的比率 越接近1 越多
error_rate_ = 10
error_rate = 10
extreme_detection_prior_number = 0  # 表示具有先验知识的任务个数
spite_client_vs_error_client = 1000  # 恶意用户和传感器偏差的可能 该数值越大,则越有可能是恶意用户0-1000
extreme_detection_flag = True  # 是否进行极端值检测
extreme_detection_flag_ = True  # 对比方案是否进行极端值检测
alpha = 2.5 # 非先验知识检测强度
extreme_detection_small_rate = 0.1
extreme_detection_big_rate = 2.5
extreme_data = 1000000




# DH
p = 9584766362985668998675320225938492576833127437546441475200651386681661214949815198902067575999636607649757091547852460848597727186027733861209248123986003
q = None
g = 2

# noise
select_index = 0  # 选择哪个边缘节点的随机向量
client_noise = 0
edge_masking_noise = 0
edge_noise = 0
ru_start = 0
ru_end = 1000
seed_start = 0
seed_end = 100000
masking_p = 100000
prf_p = 10000

if __name__ == '__main__':
    print(p.bit_length())