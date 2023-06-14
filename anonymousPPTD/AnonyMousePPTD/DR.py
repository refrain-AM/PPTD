import random

import params


class DR:
    seed_list = list()
    all_data_index_list = list()

    def __init__(self):
        self.seed_list = list()
        self.all_data_index_list = list()

    def generate_seed(self):
        """
        DR生成随机种子
        :return:
        """
        self.seed_list = list()
        for i in range(params.K):
            self.seed_list.append(random.randrange(params.seed_start, params.seed_end))

    def generate_data_index(self):
        """
        DR生成用户数据上传位置
        :return:
        """
        self.all_data_index_list = list()
        for i in range(params.K):
            self.all_data_index_list.append(i)
        random.shuffle(self.all_data_index_list)
