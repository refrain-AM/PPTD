import copy
import random
import time

import params
from utils.DetectOutliers import DetectOutliers
from utils.Encrypt import Encrypt
from utils.TD_CRH import TD_CRH


class CloudServer:
    private_server_key = None
    public_server_key = None
    aes_key_list_with_client = None
    anonymous_all_client_data = list()
    td_result = list()
    hash_noise_all_group = list()
    hash_noise_others_group = list()
    hash_noise_index = list()
    cloud_server_aggreate_time = 0
    cloud_server_generate_hash_noise_time = 0
    extream_detection_time = 0
    td_time = 0
    cloud_server_r = list()
    cloud_server_r_list = list()
    hash_noise_others_group_new = list()

    def __init__(self):
        self.private_server_key = None
        self.public_server_key = None
        self.aes_key_list_with_client = None
        self.anonymous_all_client_data = list()
        self.td_result = list()
        self.hash_noise_all_group = list()
        self.hash_noise_others_group = list()
        self.hash_noise_index = list()
        self.cloud_server_aggreate_time = 0
        self.cloud_server_generate_hash_noise_time = 0
        self.extream_detection_time = 0
        self.td_time = 0
        self.cloud_server_r = list()
        self.cloud_server_r_list = list()
        self.hash_noise_others_group_new = list()
        # print("init CloudServer")

    def generate_dh_key(self):
        encrypt = Encrypt(params.p, params.g)
        self.private_server_key, self.public_server_key = encrypt.generate_dh_key()

    def generate_aes_key(self, public_key_client_list):
        aes_key_list_with_client = list()
        encrypt = Encrypt(params.p, params.g)
        for public_key_client in public_key_client_list:
            aes_key_list_with_client.append(
                encrypt.generate_aes_key(self.private_server_key, self.public_server_key, public_key_client))
        self.aes_key_list_with_client = aes_key_list_with_client

    def generate_hash_noise_all_group(self, client_encrypt_ru_all_group, data_miss_list_all_group):
        """
        云中心生成hash噪声  此处需要进一步优化 旧版本 已废弃
        :param client_encrypt_ru_all_group:
        :return:
        """
        start_time = time.perf_counter()
        for m in range(params.M):
            cloud_server_r_one_task = list()
            for k in range(params.K):
                cloud_server_r_one_task.append(random.randrange(params.ru_start, params.ru_end))
            self.cloud_server_r.append(cloud_server_r_one_task)
        client_ru_all_group = list()
        count = 0
        for edge_index in range(params.edge_number):
            client_ru_one_group = list()
            for k in range(params.group_number_list[edge_index]):
                client_ru_one_group.append(Encrypt.aes_decryptor(self.aes_key_list_with_client[count + k],
                                                                 client_encrypt_ru_all_group[edge_index][k]))
            count += params.group_number_list[edge_index]
            client_ru_all_group.append(client_ru_one_group)

        for edge_index in range(params.edge_number):
            hash_noise_one_group = list()
            for m in range(params.M):
                hash_noise_one_group_one_task = list()
                for k in range(params.K):
                    noise = 0
                    for edge_index2 in range(params.edge_number):
                        if edge_index != edge_index2:
                            for client_index in range(params.group_number_list[edge_index2]):
                                # 删除未上传用户的数据
                                if client_index not in data_miss_list_all_group[edge_index2]:
                                    temp = client_ru_all_group[edge_index2][client_index] + k + m
                                    noise += Encrypt.hash_random(temp)
                    hash_noise_one_group_one_task.append(noise + self.cloud_server_r[m][k])
                hash_noise_one_group.append(hash_noise_one_group_one_task)
            self.hash_noise_others_group.append(hash_noise_one_group)

        for m in range(params.M):
            hash_noise_all_group_one_task = list()
            for k in range(params.K):
                noise = 0
                for edge_index in range(params.edge_number):
                    for client_index in range(params.group_number_list[edge_index]):
                        # 删除未上传用户的数据
                        if client_index not in data_miss_list_all_group[edge_index]:
                            temp = client_ru_all_group[edge_index][client_index] + k + m
                            noise += Encrypt.hash_random(temp)
                hash_noise_all_group_one_task.append(noise + self.cloud_server_r[m][k])
            self.hash_noise_all_group.append(hash_noise_all_group_one_task)
        end_time = time.perf_counter()
        print((end_time - start_time) * 1000)
        # 主要计算开销
        self.cloud_server_generate_hash_noise_time += (end_time - start_time) * 1000

    def generate_hash_noise_all_group_(self, client_encrypt_ru_all_group, data_miss_list_all_group):
        """
        云中心生成hash噪声  在程序上进行优化后的结果
        :param client_encrypt_ru_all_group:
        :return:
        """
        start_time = time.perf_counter()
        client_ru_all_group = list()
        count = 0
        for edge_index in range(params.edge_number):
            client_ru_one_group = list()
            for k in range(params.group_number_list[edge_index]):
                client_ru_one_group.append(Encrypt.aes_decryptor(self.aes_key_list_with_client[count + k],
                                                                 client_encrypt_ru_all_group[edge_index][k]))
            count += params.group_number_list[edge_index]
            client_ru_all_group.append(client_ru_one_group)

        # 计算所有用户的hash_noise
        hash_noise_all_task = list()
        for m in range(params.M):
            hash_noise_one_task = list()
            for k in range(params.K):
                hash_noise_one_task_index_i = list()
                for edge_index in range(params.edge_number):
                    hash_noise_one_task_index_i_edge = list()
                    for i in range(params.group_number_list[edge_index]):
                        count += 1
                        temp = client_ru_all_group[edge_index][i] + k + m
                        hash_noise_one_task_index_i_edge.append(Encrypt.hash_random(temp))
                    hash_noise_one_task_index_i.append(hash_noise_one_task_index_i_edge)
                hash_noise_one_task.append(hash_noise_one_task_index_i)
            hash_noise_all_task.append(hash_noise_one_task)

        # 计算云中心要用的noise
        for m in range(params.M):
            hash_noise_all_group_one_task = list()
            for k in range(params.K):
                noise = 0
                for edge_index in range(params.edge_number):
                    for client_index in range(params.group_number_list[edge_index]):
                        # 删除未上传用户的数据
                        if client_index not in data_miss_list_all_group[edge_index]:
                            noise += hash_noise_all_task[m][k][edge_index][client_index]
                hash_noise_all_group_one_task.append(noise)
            self.hash_noise_all_group.append(hash_noise_all_group_one_task)

        # 计算要发给每个边缘节点的noise
        start_time1 = time.perf_counter()
        for edge_index in range(params.edge_number):
            hash_noise_one_group = copy.deepcopy(self.hash_noise_all_group)
            for m in range(params.M):
                for k in range(params.K):
                    for client_index in range(params.group_number_list[edge_index]):
                        if client_index not in data_miss_list_all_group[edge_index]:
                            hash_noise_one_group[m][k] -= hash_noise_all_task[m][k][edge_index][client_index]
            self.hash_noise_others_group.append(hash_noise_one_group)
        end_time = time.perf_counter()
        self.cloud_server_generate_hash_noise_time += (end_time - start_time) * 1000

    def generate_hash_noise_all_group__(self, client_encrypt_ru_all_group, data_miss_list_all_group):
        """
        云中心生成hash噪声   在协议上进行优化后的结果
        :param client_encrypt_ru_all_group:
        :return:
        """
        start_time = time.perf_counter()
        client_ru_all_group = list()
        count = 0
        # 解密ru
        for edge_index in range(params.edge_number):
            client_ru_one_group = list()
            for k in range(params.group_number_list[edge_index]):
                client_ru_one_group.append(Encrypt.aes_decryptor(self.aes_key_list_with_client[count + k],
                                                                 client_encrypt_ru_all_group[edge_index][k]))
            count += params.group_number_list[edge_index]
            client_ru_all_group.append(client_ru_one_group)

        # 云中心生成随机数
        for m in range(params.M):
            cloud_server_r_list_one_task = list()
            for index in range(params.group_number_list[0]):
                cloud_server_r_list_one_task.append(random.randrange(params.ru_start, params.ru_end))
            self.cloud_server_r_list.append(cloud_server_r_list_one_task)

        # 计算要发给每个边缘节点的noise
        for edge_index in range(params.edge_number):
            hash_noise_one_group = list()
            for m in range(params.M):
                hash_noise_one_group_one_task = list()
                for index in range(params.group_number_list[edge_index]):
                    hash_noise_one_group_one_task_one_index = 0
                    for client_index in range(params.group_number_list[edge_index]):
                        if client_index not in data_miss_list_all_group[edge_index]:
                            temp = client_ru_all_group[edge_index][client_index] + index + m
                            hash_noise_one_group_one_task_one_index += Encrypt.hash_random(temp)
                    hash_noise_one_group_one_task.append(
                        self.cloud_server_r_list[m][index] - hash_noise_one_group_one_task_one_index)
                hash_noise_one_group.append(hash_noise_one_group_one_task)
            self.hash_noise_others_group.append(hash_noise_one_group)
        end_time = time.perf_counter()
        self.cloud_server_generate_hash_noise_time += (end_time - start_time) * 1000

    def aggregation_all_group_masking_client_random_index(self, all_group_masking_client_random_index):
        """
        聚合hash_noise_index
        :param all_group_masking_client_random_index:
        :return:
        """
        start_time = time.perf_counter()
        for k in range(params.K):
            self.hash_noise_index.append(0)
        for k in range(params.K):
            for edge_index in range(params.edge_number):
                self.hash_noise_index[k] += all_group_masking_client_random_index[edge_index][k]
        end_time = time.perf_counter()
        self.cloud_server_generate_hash_noise_time += (end_time - start_time) * 1000

    def aggregation_edge_masking_data_all_group(self, edge_masking_data_all_group):
        """
        中心服务器聚合用户数据
        :param edge_masking_data_all_group:
        :return:
        """
        start_time = time.perf_counter()
        for k in range(params.K):
            anonymous_one_client_data = list()
            for m in range(params.M):
                temp = 0
                for edge_index in range(params.edge_number):
                    temp += edge_masking_data_all_group[edge_index][m][k]
                temp -= self.cloud_server_r_list[m][self.hash_noise_index[k]]
                anonymous_one_client_data.append(temp)
            self.anonymous_all_client_data.append(anonymous_one_client_data)
        end_time = time.perf_counter()
        self.cloud_server_aggreate_time += (end_time - start_time) * 1000

    def detection_extreme_data(self, data_section):
        start_time = time.perf_counter()
        extreme_data_list = list()
        for k in range(len(self.anonymous_all_client_data)):
            for m in range(params.M):
                if self.anonymous_all_client_data[k][m] == 0:
                    # print(self.anonymous_all_client_data[k])
                    extreme_data_list.append(self.anonymous_all_client_data[k])
                    break
                if params.extreme_detection_flag:
                    if self.anonymous_all_client_data[k][m] < data_section[m][0] or data_section[m][1] < \
                            self.anonymous_all_client_data[k][m]:
                        extreme_data_list.append(self.anonymous_all_client_data[k])
                        # self.anonymous_all_client_data[k][m] = 0
                        # self.anonymous_all_client_data[k][m] = (data_section[m][1] - data_section[m][0]) / 2
                        break
        for extreme_data in extreme_data_list:
            # print(extreme_data)
            if extreme_data in self.anonymous_all_client_data:
                self.anonymous_all_client_data.remove(extreme_data)
            else:
                print("没找到")
        end_time = time.perf_counter()
        self.extream_detection_time += (end_time - start_time) * 1000

    def td_in_anonymous_data(self, anonymous_all_client_data):
        start_time = time.perf_counter()
        td_CRH = TD_CRH(anonymous_all_client_data, len(anonymous_all_client_data), len(anonymous_all_client_data[0]))
        td_CRH.TD(params.count)
        self.td_result = td_CRH.xm_i[params.count]
        end_time = time.perf_counter()
        self.td_time += (end_time - start_time) * 1000
