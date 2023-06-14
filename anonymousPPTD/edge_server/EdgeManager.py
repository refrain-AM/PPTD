import copy
import random
import time

import params
from utils.Encrypt import Encrypt
from utils.Masking import Masking


class EdgeManager:
    public_key_edge_list = list()
    private_key_edge_list = list()
    aes_key_list_all_edge = list()
    en_all_edge_client_data_index = list()
    de_all_group_client_data_index = list()
    all_group_in_client_data_index = list()
    all_group_aggreagtion_client_data = list()
    edge_masking_data_all_group = list()
    all_group_masking_client_random_index = list()
    masking = None
    edge_seed_all = list()
    masking_noise_all_edge = list()
    index_edge_time = list()
    aggregation_and_upload_edge_time = list()

    def __init__(self):
        self.public_key_edge_list = list()
        self.private_key_edge_list = list()
        self.aes_key_list_all_edge = list()
        self.en_all_edge_client_data_index = list()
        self.de_all_group_client_data_index = list()
        self.all_group_in_client_data_index = list()
        self.all_group_aggreagtion_client_data = list()
        self.edge_masking_data_all_group = list()
        self.all_group_masking_client_random_index = list()
        self.masking = None
        self.edge_seed_all = list()
        self.masking_noise_all_edge = list()
        self.index_edge_time = list()
        self.aggregation_and_upload_edge_time = list()

        self.masking = Masking(params.edge_number, params.M, params.K, params.masking_p)
        for edge_index in range(params.edge_number):
            self.index_edge_time.append(0)
            self.aggregation_and_upload_edge_time.append(0)
        # print("init EdgeManager")

    def generate_dh_key(self, edge_count):
        encrypt = Encrypt(params.p, params.g)
        public_key_list = list()
        private_key_list = list()
        for i in range(edge_count):
            private_key, public_key = encrypt.generate_dh_key()
            public_key_list.append(public_key)
            private_key_list.append(private_key)
        self.public_key_edge_list = public_key_list
        self.private_key_edge_list = private_key_list

    def generate_aes_key(self):
        encrypt = Encrypt(params.p, params.g)
        # 为所有边缘节点和其他所有边缘节点协商对称密钥
        aes_key_list_all_edge = list()
        for edge_index in range(len(self.private_key_edge_list)):
            # 逐个处理每个边缘节点
            aes_key_list_one_edge = list()
            for public_key in self.public_key_edge_list:
                # 生成对称密钥
                aes_key = encrypt.generate_aes_key(self.private_key_edge_list[edge_index],
                                                   self.public_key_edge_list[edge_index],
                                                   public_key)
                aes_key_list_one_edge.append(aes_key)
            aes_key_list_all_edge.append(aes_key_list_one_edge)
        self.aes_key_list_all_edge = aes_key_list_all_edge

    def generate_masking_seed(self):
        """
        边缘节点之间相互协商masking_seed
        :return:
        """
        self.edge_seed_all = self.masking.generate_seed_i_j(params.seed_start, params.seed_end)

    def generate_en_client_data_index(self):
        all_edge_client_data_index = list()
        # 所有边缘节点生成初始的未加密的数据添加位置向量
        for edge_index in range(params.edge_number):

            start_time = time.perf_counter()
            one_edge_client_data_index = list()
            for k in range(params.K):
                one_edge_client_data_index.append(k)
            random.shuffle(one_edge_client_data_index)
            # print(one_edge_client_data_index)
            end_time = time.perf_counter()
            self.index_edge_time[edge_index] += (end_time - start_time) * 1000

            all_edge_client_data_index.append(one_edge_client_data_index)
        # 为所有边缘节点加密身生成的数据添加位置
        for edge_index1 in range(len(all_edge_client_data_index)):
            start_time = time.perf_counter()
            # en_one_edge_client_data_index = bytes()
            en_one_edge_client_data_index = list()
            one_edge_client_data_index = all_edge_client_data_index[edge_index1]
            start_index = 0
            end_index = 0
            # 对序列切分，并使用和不同节点共享的密钥加密
            for edge_index2 in range(len(params.group_number_list)):
                end_index += params.group_number_list[edge_index2]
                temp_list = copy.copy(one_edge_client_data_index[start_index:end_index])
                temp = Encrypt.aes_list_encryptor_(self.aes_key_list_all_edge[edge_index1][edge_index2], temp_list)
                en_one_edge_client_data_index += temp
                start_index = end_index
            self.en_all_edge_client_data_index.append(en_one_edge_client_data_index)
            end_time = time.perf_counter()
            self.index_edge_time[edge_index1] += (end_time - start_time) * 1000

    def generate_de_group_client_data_index(self, edge_en_data_index, en_data_list):
        """
        节点解密收到的加密数据位置
        :param edge_en_data_index: 加密数据上传位置向量的节点的索引
        :param en_data_list: 收到的加密数据添加位置
        :return:
        """
        start_index = 0
        end_index = 0
        for edge_index in range(params.edge_number):
            end_index += params.group_number_list[edge_index]
            temp_list = copy.copy(en_data_list[start_index:end_index])

            start_time = time.perf_counter()
            self.de_all_group_client_data_index.append(
                Encrypt.aes_list_decryptor_(self.aes_key_list_all_edge[edge_index][edge_en_data_index], temp_list))
            end_time = time.perf_counter()
            self.index_edge_time[edge_index] += (end_time - start_time) * 1000

            start_index = end_index

    def generate_all_group_masking_client_random_index(self):
        """
        边缘节点生成关于random_index要上传的向量
        :return:
        """
        for edge_index in range(params.edge_number):

            start_time = time.perf_counter()
            one_group_masking_client_random_index = list()
            for k in range(params.K):
                one_group_masking_client_random_index.append(0)
            count = 0
            for random_index in self.de_all_group_client_data_index[edge_index]:
                one_group_masking_client_random_index[random_index] = count + params.edge_masking_noise
                count += 1
            end_time = time.perf_counter()
            # print("1=%f"%((end_time-start_time)*1000))
            self.aggregation_and_upload_edge_time[edge_index] += (end_time - start_time) * 1000

            self.all_group_masking_client_random_index.append(one_group_masking_client_random_index)

    def generate_in_group_client_data_index(self):
        """
        各个边缘节点为组内用户分配组内数据添加位置
        :return:
        """
        for edge_index in range(len(params.group_number_list)):
            # 依次执行每个边缘节点
            start_time = time.perf_counter()
            one_group_in_group_client_data_index = list()
            for i in range(params.group_number_list[edge_index]):
                one_group_in_group_client_data_index.append(i)
            random.shuffle(one_group_in_group_client_data_index)
            end_time = time.perf_counter()
            self.index_edge_time[edge_index] += (end_time - start_time) * 1000

            self.all_group_in_client_data_index.append(one_group_in_group_client_data_index)

    def aggregation_all_group_client_data(self, client_masking_data_all_group, data_miss_list_all_group):
        # 边缘节点聚合用户数据
        for edge_index in range(params.edge_number):
            # 逐组处理

            start_time = time.perf_counter()
            one_group_aggreagtion_client_data = list()
            for m in range(params.M):
                # 每组中逐任务处理
                one_task_group_aggregation_client_data = list()
                for client_index in range(params.group_number_list[edge_index]):
                    # 先生成长度为k的向量
                    one_task_group_aggregation_client_data.append(0)
                for client_index1 in range(params.group_number_list[edge_index]):
                    # 逐列聚合用户的数据
                    for client_index2 in range(params.group_number_list[edge_index]):
                        if client_index2 not in data_miss_list_all_group[edge_index]:
                            one_task_group_aggregation_client_data[client_index1] += \
                                client_masking_data_all_group[edge_index][client_index2][m][client_index1]
                one_group_aggreagtion_client_data.append(one_task_group_aggregation_client_data)
            end_time = time.perf_counter()
            # print("2=%f"%((end_time-start_time)*1000))
            self.aggregation_and_upload_edge_time[edge_index] += (end_time - start_time) * 1000

            self.all_group_aggreagtion_client_data.append(one_group_aggreagtion_client_data)

    def generate_edge_masking_noise_all_group(self, count):
        """
        各边缘节点生成本次上传用的masking_noise
        :param count:
        :return:
        """
        start_time = time.perf_counter()
        self.masking.generate_random_all_client(count)
        self.masking_noise_all_edge = self.masking.generate_masking_noise_all_client()
        end_time = time.perf_counter()
        # print("3=%f"%((end_time-start_time)*1000))
        for edge_index in range(params.edge_number):
            self.aggregation_and_upload_edge_time[edge_index] += ((end_time - start_time) * 1000) / params.edge_number

    def generate_edge_masking_data_all_group(self, hash_noise_others_group):
        """
        边缘节点生成要上传给服务器的数据,此处的masking噪声先用00000000代替
        :return:
        """
        for edge_index in range(params.edge_number):
            start_time = time.perf_counter()
            edge_masking_data_one_group = list()
            # 边缘节点初始化要上传的数据矩阵,此处先把masking的噪声添加了
            for m in range(params.M):
                edge_masking_data_one_task_one_group = list()
                for k in range(params.client_number):
                    edge_masking_data_one_task_one_group.append(self.masking_noise_all_edge[edge_index][m][k])
                edge_masking_data_one_group.append(edge_masking_data_one_task_one_group)
            # 边缘节点将数据和哈希噪声添加到初始化后的数据矩阵
            for m in range(params.M):
                count = 0
                for client_data_index in self.de_all_group_client_data_index[edge_index]:
                    # 边缘节点添加数据
                    edge_masking_data_one_group[m][client_data_index] += \
                        self.all_group_aggreagtion_client_data[edge_index][m][count]
                    # # 边缘节点添加哈希噪声 用户知道匿名集
                    # edge_masking_data_one_group[m][client_data_index] += hash_noise_others_group[edge_index][m][
                    #     self.de_all_group_client_data_index[edge_index][count]]
                    # 边缘节点添加哈希噪声 用户不知道匿名集
                    edge_masking_data_one_group[m][client_data_index] += hash_noise_others_group[edge_index][m][count]
                    count += 1
            end_time = time.perf_counter()
            # print("4=%f"%((end_time-start_time)*1000))
            self.aggregation_and_upload_edge_time[edge_index] += (end_time - start_time) * 1000

            self.edge_masking_data_all_group.append(edge_masking_data_one_group)
