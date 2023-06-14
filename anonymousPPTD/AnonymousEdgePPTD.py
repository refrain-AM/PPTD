import copy
import random
import time

import params
from client.ClientManager import ClientManager
from cloud_server.CloudServer import CloudServer
from data_generator.DataGenerator import DataGenerator
from edge_server.EdgeManager import EdgeManager
from utils.DetectOutliers import DetectOutliers
from utils.TD_CRH import TD_CRH


class AnonymousEdgePPTD:
    clientManager = None
    edgeManager = None
    cloudServer = None
    dataGenerator = None
    base_data_list = list()
    extreme_data_index = list()
    data_miss_list_all_group = list()
    all_client_data = list()
    origin_client_data = list()
    data_section = list()
    cloud_server_detection_extreme_data_time = 0

    def __init__(self):
        self.clientManager = ClientManager()
        self.edgeManager = EdgeManager()
        self.cloudServer = CloudServer()
        self.dataGenerator = DataGenerator()
        self.base_data_list = list()
        self.extreme_data_index = list()
        self.data_miss_list_all_group = list()
        self.all_client_data = list()
        self.origin_client_data = list()
        self.data_section = list()
        self.cloud_server_detection_extreme_data_time = 0
        print("init Application")

    def key_agreement(self):
        # 用户生成dh密钥，并相互生成aes密钥
        # start = round(time.time()*1000)# 返回当前时间戳 ms级别
        start = time.perf_counter()  # 返回性能计数器的值（以小数秒为单位）作为浮点数
        self.clientManager.generate_dh_key(int(params.client_number))
        end = time.perf_counter()
        # print("为所有用户生成DH密钥用时%d" % (end - start))
        # start = time.perf_counter()
        # self.clientManager.generate_aes_key()
        # end = time.perf_counter()
        # print("为所有用户协商对称密钥用时%d" % (end - start))
        # 边缘节点生成dh密钥，并相互生成aes密钥
        start = time.perf_counter()
        self.edgeManager.generate_dh_key(int(params.edge_number))
        end = time.perf_counter()
        # print("为所有边缘节点生成DH密钥用时%d" % (end - start))
        start = time.perf_counter()
        self.edgeManager.generate_aes_key()
        end = time.perf_counter()
        # print("为所有边缘节点生成协商对称密钥用时%d" % (end - start))
        self.edgeManager.generate_masking_seed()
        # 云中心生成dh密钥，并和用户相互生成aes密钥
        self.cloudServer.generate_dh_key()
        start = time.perf_counter()
        self.cloudServer.generate_aes_key(self.clientManager.public_key_client_list)
        end = time.perf_counter()
        self.clientManager.generate_aes_key_with_cloud(self.cloudServer.public_server_key)
        # print("为所有用户和云中心协商对称密钥用时%d" % (end - start))

    def data_generator(self):
        # 生成整个系统的用户数据
        self.dataGenerator.generate_base_data(params.base_data_rate, params.base_data_start, params.base_data_end,
                                              params.reliable_client_rate)
        self.dataGenerator.generate_client_data()

    def load_data(self):
        # 打印basedata
        # print("basedata")
        self.base_data_list = self.dataGenerator.base_data
        # print(self.dataGenerator.base_data)
        self.all_client_data = self.dataGenerator.all_client_data
        self.origin_client_data = copy.deepcopy(self.all_client_data)
        return self.all_client_data

    def generate_datection_section(self):
        self.dataGenerator.generate_datection_section()
        self.data_section = self.dataGenerator.data_section

    def generate_extreme_data_index(self, k, m, extreme_client_rate, extreme_task_rate):
        extreme_data_index = list()
        for k_ in range(k):
            extreme_data_index_one_cliet = list()
            for m_ in range(m):
                extreme_data_index_one_cliet.append(0)
            if random.randrange(0, k) < int(extreme_client_rate * k):
                if random.randrange(0, 1000) < params.spite_client_vs_error_client:
                    # 是恶意用户
                    for m_ in range(int(m * extreme_task_rate)):
                        extreme_data_index_one_cliet[m_] = 1
                        # extreme_data_index_one_cliet[random.randrange(0,m)] = 1
                else:
                    # 是传感器偏差
                    for m_ in range(int(m * extreme_task_rate)):
                        extreme_data_index_one_cliet[m_] = 2
                        # extreme_data_index_one_cliet[random.randrange(0,m)] = 1
            extreme_data_index.append(extreme_data_index_one_cliet)
        self.extreme_data_index = extreme_data_index

    def generate_extreme_data_index_(self, k, m, extreme_client_rate, extreme_task_rate):
        extreme_data_index = list()
        for k_ in range(k):
            extreme_data_index_one_cliet = list()
            for m_ in range(m):
                extreme_data_index_one_cliet.append(0)
            extreme_data_index.append(extreme_data_index_one_cliet)

        for k_ in range(extreme_client_rate):
            k_temp = random.randrange(0, 1000)
            # k_temp = k_
            if random.randrange(0, 1000) < params.spite_client_vs_error_client:
                # 是恶意用户
                for m_ in range(int(m * extreme_task_rate)):
                    # extreme_data_index_one_cliet.append(1)
                    extreme_data_index[k_temp][random.randrange(0, m)] = 1
            else:
                # 是传感器偏差
                for m_ in range(int(m * extreme_task_rate)):
                        # extreme_data_index_one_cliet.append(2)
                    extreme_data_index[k_temp][random.randrange(0, m)] = 2
        self.extreme_data_index = extreme_data_index

    def add_extreme_data(self):
        for k in range(params.K):
            for m in range(params.M):
                # 恶意用户情况下的极端值
                if self.extreme_data_index[k][m] == 1:
                    # 生成高斯噪声,模拟用户观测不准确
                    # noise = self.all_client_data[k][m] * random.gauss(0, params.unreliable__)
                    # self.all_client_data[k][m] = self.all_client_data[k][m] + noise
                    self.all_client_data[k][m] = self.all_client_data[k][m] * params.error_rate_
                    # self.all_client_data[k][m] = random.randint(int(self.all_client_data[k][m]/params.error_rate_), int(self.all_client_data[k][m] * params.error_rate_))
                if self.extreme_data_index[k][m] == 2:
                    self.all_client_data[k][m] = self.all_client_data[k][m] * params.error_rate

    def client_load_data(self, all_client_data):
        # 将用户数据加载到clientManager中
        self.clientManager.load_data(all_client_data)

    def generate_data_index(self, edge_en_data_index):
        """
        边缘节点协商数据添加位置
        :param edge_en_data_index: 云中心选的数据上传位置的边缘服务器
        :return:
        """
        self.edgeManager.generate_en_client_data_index()
        self.edgeManager.generate_de_group_client_data_index(edge_en_data_index,
                                                             self.edgeManager.en_all_edge_client_data_index[
                                                                 edge_en_data_index])
        # 边缘节点总体数据添加位置
        # print("边缘节点总体数据添加位置")
        # print(self.edgeManager.de_all_group_client_data_index)
        # 各个边缘节点生成组内用户数据添加位置
        self.edgeManager.generate_in_group_client_data_index()
        # print("各边缘节点内部用户数据添加位置")
        # print(self.edgeManager.all_group_in_client_data_index)
        # 边缘节点协商关于random_index要上传的向量
        self.edgeManager.generate_all_group_masking_client_random_index()
        return self.edgeManager.all_group_in_client_data_index

    # def client_generate_ru(self):
    #     # 用户生成ru
    #     self.clientManager.generate_ru()
    #     return self.clientManager.client_ru_all_group

    def generate_data_miss_list(self, rate):
        """
        生成掉线用户的索引
        :param rate:
        :return:
        """
        data_miss_list_all_group = list()
        for edge_index in range(params.edge_number):
            data_miss_list_one_group = list()
            temp = params.group_number_list[edge_index]
            for k in range(temp):
                data_miss_list_one_group.append(k)
            for k in range(int(temp * rate)):
                temp = len(data_miss_list_one_group)
                data_miss_list_one_group.remove(data_miss_list_one_group[random.randrange(0, temp)])
            data_miss_list_all_group.append(data_miss_list_one_group)
        self.data_miss_list_all_group = data_miss_list_all_group
        return data_miss_list_all_group

    def generate_data_miss_list_(self, rate):
        """
        生成掉线用户的索引
        :param number:
        :return:
        """
        data_miss_list_all_group = list()
        for edge_index in range(params.edge_number):
            data_miss_list_one_group = list()
            temp = params.group_number_list[edge_index]
            for k in range(int(temp * rate)):
                data_miss_list_one_group.append(random.randrange(0, temp))
            data_miss_list_all_group.append(data_miss_list_one_group)
        self.data_miss_list_all_group = data_miss_list_all_group
        return data_miss_list_all_group

    def client_upload_data(self, all_group_in_client_data_index, de_all_group_client_data_index):
        # 用户生成ru
        self.clientManager.generate_ru()
        # 用户生成加密的ru
        self.clientManager.generate_encrypt_ru()
        # 用户生成要添加的hash噪声
        self.clientManager.generate_hash_noise_data(de_all_group_client_data_index)
        # 用户生成上传数据
        return self.clientManager.generate_update_data(all_group_in_client_data_index)

    def cloud_server_generate_hash_noise(self, client_encrypt_ru_all_group, data_miss_list_all_group):
        self.cloudServer.generate_hash_noise_all_group__(client_encrypt_ru_all_group, data_miss_list_all_group)
        return self.cloudServer.hash_noise_others_group

    def edge_aggregation_client_data(self, client_masking_data_all_group, data_miss_list_all_group):
        self.edgeManager.aggregation_all_group_client_data(client_masking_data_all_group, data_miss_list_all_group)
        return self.edgeManager.all_group_aggreagtion_client_data

    def edge_generate_edge_masking_data_all_group(self, hash_noise_others_group, count):
        self.edgeManager.generate_edge_masking_noise_all_group(count)
        self.edgeManager.generate_edge_masking_data_all_group(hash_noise_others_group)
        return self.edgeManager.edge_masking_data_all_group

    def cloud_server_aggregation_edge_masking_data(self, edge_masking_data_all_group):
        # 聚合hash噪声的位置
        self.cloudServer.aggregation_all_group_masking_client_random_index(
            self.edgeManager.all_group_masking_client_random_index)
        # 聚合用户数据
        self.cloudServer.aggregation_edge_masking_data_all_group(edge_masking_data_all_group)

    def cloud_server_detection_extreme_data(self, data_section):
        # 检测极端值
        start_time = time.perf_counter()
        data_section_sifenwei = DetectOutliers.detect_outliers(self.cloudServer.anonymous_all_client_data, params.alpha)
        print("data_section_sifenwei")
        print(data_section_sifenwei)
        for m in range(params.M - params.extreme_detection_prior_number):
            data_section[m + params.extreme_detection_prior_number][0] = \
                data_section_sifenwei[m + params.extreme_detection_prior_number][0]
            data_section[m + params.extreme_detection_prior_number][1] = \
                data_section_sifenwei[m + params.extreme_detection_prior_number][1]
        self.cloudServer.detection_extreme_data(data_section)
        end_time = time.perf_counter()
        self.cloud_server_detection_extreme_data_time = (end_time - start_time) * 1000
        return self.cloudServer.anonymous_all_client_data

    def cloud_server_aggregation_edge_masking_data_(self, data_miss_list_all_group, anonymous_all_client_data,
                                                    data_section):
        count = 0
        for edge_index in range(params.edge_number):
            if (len(data_miss_list_all_group[edge_index]) == 0):
                continue
            for i in data_miss_list_all_group[edge_index]:
                anonymous_all_client_data.remove(
                    anonymous_all_client_data[int(edge_index * (params.K / params.edge_number) + i - count)])
                count += 1
        self.cloudServer.anonymous_all_client_data = anonymous_all_client_data

        # 检测极端值
        data_section_sifenwei = DetectOutliers.detect_outliers(self.cloudServer.anonymous_all_client_data, params.alpha)
        print("data_section_sifenwei")
        print(data_section_sifenwei)
        for m in range(params.M - params.extreme_detection_prior_number):
            data_section[m + params.extreme_detection_prior_number][0] = \
                data_section_sifenwei[m + params.extreme_detection_prior_number][0]
            data_section[m + params.extreme_detection_prior_number][1] = \
                data_section_sifenwei[m + params.extreme_detection_prior_number][1]
        self.cloudServer.detection_extreme_data(data_section)
        return self.cloudServer.anonymous_all_client_data

    def cloud_server_TD(self, anonymous_all_client_data):
        print("收到%d个有效的用户数据" % (len(anonymous_all_client_data)))
        self.cloudServer.td_in_anonymous_data(anonymous_all_client_data)
        return self.cloudServer.td_result

    @staticmethod
    def original_data_TD(original_data):
        td_CRH = TD_CRH(original_data, len(original_data), len(original_data[0]))
        td_CRH.TD(params.count)
        return td_CRH.xm_i[params.count]
