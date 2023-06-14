import copy
import csv
import random

import params
from utils.TestUtils import TestUtils


class DataGenerator:
    base_data = list()
    reliable_client = list()
    all_client_data = list()
    data_section = list()

    def __init__(self):
        self.base_data = list()
        self.reliable_client = list()
        self.all_client_data = list()
        self.data_section = list()
        # print("init DataGenerator")

    def generate_base_data(self, base_data_rate, base_data_start, base_data_end, reliable_client_rate):
        """
        生成地面真值和用户可靠性(观测准确度)
        :param base_data_rate: 随即生成地面真值之后乘以的倍数(更加分散)
        :param base_data_start: 随机生成地面真值的起点
        :param base_data_end: 随机生成地面真值的终点
        :param reliable_client_rate: 可靠用户的比例,0-100 越接近100 可靠用户越多
        """
        base_data = list()
        reliable_client = list()
        for m in range(params.M):
            base_data.append(random.randint(base_data_start, base_data_end) * base_data_rate)
        for k in range(params.K):
            temp = random.randint(0, 100)
            if temp < reliable_client_rate:
                reliable_client.append(params.reliable_start)
            else:
                reliable_client.append(params.unreliable_start)
        self.base_data = base_data
        self.reliable_client = reliable_client

    def generate_client_data(self):
        all_client_data = list()
        for k in range(params.K):
            one_client_data = list()
            for m in range(params.M):
                # 生成高斯噪声,模拟用户观测不准确
                noise = self.base_data[m] * random.gauss(0, self.reliable_client[k])
                one_client_data.append(self.base_data[m] + noise * 0.2)
            all_client_data.append(one_client_data)
        self.all_client_data = all_client_data
        return self.all_client_data

    def generate_datection_section(self):
        # 计算极端值检测区间
        for base_data in self.base_data:
            data_section_one_task = list()
            data_section_one_task.append(base_data * params.extreme_detection_small_rate)
            data_section_one_task.append(base_data * params.extreme_detection_big_rate)
            self.data_section.append(data_section_one_task)

    def sava_all_client_data(self, file_path, file_name):
        TestUtils.write_csv_one_line_title_(file_path, file_name, self.base_data)
        for client_data in self.all_client_data:
            TestUtils.write_csv_one_line(file_path, file_name, client_data)

    def read_all_client_data(self, file_path, file_name):
        with open(file_path + file_name, 'r', encoding='utf8') as fp:
            temp_list = [i for i in csv.reader(fp)]
            for i in range(len(temp_list)):
                for j in range(len(temp_list[0])):
                    temp_list[i][j] = float(temp_list[i][j])
            self.base_data = copy.copy(temp_list[0])
            temp_list.remove(temp_list[0])
            self.all_client_data = temp_list
