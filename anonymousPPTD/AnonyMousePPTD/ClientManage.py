import copy
import random
import time

import params
from utils.Encrypt import Encrypt


class ClientManage:
    all_client_seed = list()
    all_data_index_list = list()
    all_client_data = list()
    all_client_noise = list()
    all_client_masking_data = list()
    all_client_time = 0

    def __init__(self):
        self.all_client_seed = list()
        self.all_data_index_list = list()
        self.all_client_data = list()
        self.all_client_noise = list()
        self.all_client_masking_data = list()
        self.all_client_time = 0

    def load_seed_and_data_index(self, seed_list, all_data_index_list):
        """
        用户端接收种子和数据添加位置
        :param seed_list:
        :param all_data_index_list:
        :return:
        """
        self.all_client_seed = list()
        # 初始化用户种子
        for k in range(params.K):
            one_client_seed = list()
            one_client_seed.append(0)
            one_client_seed.append(0)
            self.all_client_seed.append(one_client_seed)
        # 为用户分发种子
        temp_list_1 = list()
        temp_list_2 = list()
        for k in range(params.K):
            temp_list_1.append(k)
            temp_list_2.append(k)
        random.shuffle(temp_list_1)
        random.shuffle(temp_list_2)
        for k in range(params.K):
            self.all_client_seed[k][0] = seed_list[temp_list_1[k]]
            self.all_client_seed[k][1] = seed_list[temp_list_2[k]]
        # 为用户分配数据添加位置
        self.all_data_index_list = all_data_index_list

    def load_data(self, client_data):
        """
        把生成的整个系统的用户数据切分给到各个组的用户中去
        :param client_data:整个系统的用户数据
        :return:
        """
        self.all_client_data = copy.deepcopy(client_data)

    def generate_noise(self, count):
        # 为用户生成噪声
        start_time = time.perf_counter()
        for i in range(params.K):
            one_client_noise = list()
            for m in range(params.M):
                one_client_noise_one_task = list()
                one_client_noise_one_task_a = list()
                # 使用第一个种子做处理
                for k in range(params.K):
                    if m == 0 or k == 0:
                        random_noise_1 = Encrypt.random_prf(self.all_client_seed[i][0] + m + k + count)
                        one_client_noise_one_task_a.append(random_noise_1)
                    else:
                        one_client_noise_one_task_a.append(Encrypt.random_prf(one_client_noise_one_task_a[k - 1]))
                one_client_noise_one_task_b = list()
                for k in range(params.K):
                    if m == 0 or k == 0:
                        random_noise_1 = Encrypt.random_prf(self.all_client_seed[i][1] + m + k + count)
                        one_client_noise_one_task_b.append(random_noise_1)
                    else:
                        one_client_noise_one_task_b.append(Encrypt.random_prf(one_client_noise_one_task_b[k - 1]))
                for k in range(params.K):
                    one_client_noise_one_task.append(one_client_noise_one_task_a[k] - one_client_noise_one_task_b[k])
                one_client_noise.append(one_client_noise_one_task)
            self.all_client_noise.append(one_client_noise)
        end_time = time.perf_counter()
        self.all_client_time += (end_time - start_time) * 1000

    def verify_noise_data(self):
        for m in range(params.M):
            for k in range(params.K):
                temp = 0
                for i in range(params.K):
                    temp += self.all_client_noise[i][m][k]
                print(temp)

    def generate_masking_data(self):
        """
        用户生成数据并上传
        :return:
        """
        self.all_client_masking_data = copy.deepcopy(self.all_client_noise)
        for i in range(params.K):
            start_time = time.perf_counter()
            for m in range(params.M):
                for j in range(params.K):
                    if j == self.all_data_index_list[i]:
                        self.all_client_masking_data[i][m][j] = self.all_client_masking_data[i][m][j] + \
                                                                self.all_client_data[j][m]
            end_time = time.perf_counter()
            self.all_client_time += (end_time - start_time) * 1000
