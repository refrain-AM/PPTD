import copy
from math import log


class TD_CRH:
    K = 0
    M = 0
    x_k_m = list()
    x_m = list()
    w_K = list()
    xm_i = list()
    wk_i = list()

    def __init__(self, client_value_list, k, m):
        # print("对%d个用户的值进行真值发现"%k)
        self.x_k_m = list()
        self.K = k
        self.M = m
        self.x_m = list()
        self.w_K = list()
        self.xm_i = list()
        self.wk_i = list()
        for client_value in client_value_list:
            self.x_k_m.append(client_value)
        for m_ in range(m):
            self.x_m.append(0)
        for k_ in range(k):
            self.w_K.append(0)



    def get_wk(self):
        d_k = list()
        for k in range(self.K):
            dk = 0
            for m in range(self.M):
                dk = dk + (self.x_k_m[k][m] - self.x_m[m]) ** 2
            d_k.append(dk)
        sum_d_k = 0
        for k in range(self.K):
            sum_d_k = sum_d_k + d_k[k]
        for k in range(self.K):
            self.w_K[k] = (log(sum_d_k, 2) - log(d_k[k], 2))

    def get_xm(self):
        sum_wk = 0
        for w_k in self.w_K:
            sum_wk += w_k
        for m in range(self.M):
            x_m_temp = 0
            for k in range(self.K):
                x_m_temp = x_m_temp + self.w_K[k] * self.x_k_m[k][m]
            self.x_m[m] = (x_m_temp / sum_wk)

    def TD(self, count):
        self.xm_i.append(copy.copy(self.x_m))
        self.wk_i.append(copy.copy(self.w_K))
        for i in range(count):
            self.get_wk()
            self.get_xm()
            self.wk_i.append(copy.copy(self.w_K))
            self.xm_i.append(copy.copy(self.x_m))
        print(111)
