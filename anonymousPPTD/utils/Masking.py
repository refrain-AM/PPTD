import random
import time

from utils.Encrypt import Encrypt


class Masking:
    client_number = 0
    M = 0
    K = 0
    masking_p = 0
    client_seed_all = list()
    random_all_client = list()
    masking_noise_all_client = list()

    def __init__(self, client_number, m, k, masking_p):
        self.client_number = client_number
        self.M = m
        self.K = k
        self.masking_p = masking_p
        self.client_seed_all = list()
        self.random_all_client = list()
        self.masking_noise_all_client = list()

    def generate_seed_i_j(self, seed_start, seed_end):
        """
        用户之间协商m共享的asking随机数种子
        :param seed_start:masking随机数种子起点
        :param seed_end:masking随机数种子终点
        :return:
        """
        for i in range(self.client_number):
            client_random_one = list()
            for j in range(self.client_number):
                client_random_one.append(0)
            self.client_seed_all.append(client_random_one)
        for i in range(self.client_number):
            j = i + 1
            while j < self.client_number:
                temp = random.randrange(seed_start, seed_end)
                self.client_seed_all[i][j] = temp
                self.client_seed_all[j][i] = temp
                j += 1
        return self.client_seed_all

    def load_client_seed_all(self, client_seed_all):
        self.client_seed_all = client_seed_all

    def generate_random_all_client(self, count):
        """
        用户生成本次用的随机数
        :return:
        """
        # 逐个初始化用户矩阵
        for i in range(self.client_number):
            random_one_client = list()
            for m in range(self.M):
                random_one_client_one_task = list()
                for k in range(self.K):
                    random_one_client_one_task_with_j = list()
                    for j in range(self.client_number):
                        random_one_client_one_task_with_j.append(0)
                    random_one_client_one_task.append(random_one_client_one_task_with_j)
                random_one_client.append(random_one_client_one_task)
            self.random_all_client.append(random_one_client)
        # 生成随机数填充初始化后的矩阵
        for i in range(self.client_number):
            for m in range(self.M):
                for k in range(self.K):
                    j = i + 1
                    while j < self.client_number:
                        if m == 0 or k == 0:
                            random_noise = Encrypt.random_prf(self.client_seed_all[i][j] + m + k + count)
                            self.random_all_client[i][m][k][j] = random_noise
                            self.random_all_client[j][m][k][i] = random_noise
                        else:
                            random_noise = Encrypt.random_prf(self.random_all_client[i][m][-1][j])
                            self.random_all_client[i][m][k][j] = random_noise
                            self.random_all_client[j][m][k][i] = random_noise
                        j += 1

    def generate_masking_noise_all_client(self):
        """
        生成要对m行k列的数据添加的masking噪声
        :return:
        """
        for i in range(self.client_number):
            masking_noise_one_client = list()
            for m in range(self.M):
                masking_noise_one_client_one_task = list()
                for k in range(self.K):
                    noise_m_k = 0
                    for j in range(self.client_number):
                        if i > j:
                            noise_m_k += self.random_all_client[i][m][k][j] % self.masking_p
                        if i < j:
                            noise_m_k -= self.random_all_client[i][m][k][j] % self.masking_p
                    masking_noise_one_client_one_task.append(noise_m_k)
                masking_noise_one_client.append(masking_noise_one_client_one_task)
            self.masking_noise_all_client.append(masking_noise_one_client)
        return self.masking_noise_all_client

    def verify_masking_eliminate(self):
        for m in range(self.M):
            for k in range(self.K):
                m_k = 0
                for i in range(self.client_number):
                    m_k += self.masking_noise_all_client[i][m][k]
                # 输出应当为0 表示噪声消除掉了
                print(m_k)

# if __name__ == '__main__':
#     print('PyCharm')
#     masking = Masking(10, 3, 10, 10000000000000)
#     masking.generate_seed_i_j(0, 1000000000)
#     print(masking.client_seed_all)
#     # 测试PRF
#     masking.generate_random_all_client(2)
#     masking.generate_masking_noise_all_client()
#     masking.verify_masking_eliminate()
#     print(masking.random_all_client)
#     print("aaaaaaaa")
