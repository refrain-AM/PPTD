import time

import params
from utils.TD_CRH import TD_CRH


class AS:
    anonymous_all_client_data = list()
    cloud_server_aggreate_time = 0
    extream_detection_time = 0
    td_time = 0

    def __init__(self):
        self.anonymous_all_client_data = list()
        self.cloud_server_aggreate_time = 0
        self.extream_detection_time = 0
        self.td_time = 0

    def aggregation_masking_data_all_client(self, all_client_masking_data, data_miss_list):
        """
        中心服务器聚合用户数据
        :param all_client_masking_data:
        :return:
        """
        start_time = time.perf_counter()
        for k in range(params.K):
            anonymous_one_client_data = list()
            for m in range(params.M):
                temp = 0
                for j in range(params.K):
                    if j not in data_miss_list:
                        temp += all_client_masking_data[j][m][k]
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
                    extreme_data_list.append(self.anonymous_all_client_data[k])
                    break
                if params.extreme_detection_flag_:
                    if self.anonymous_all_client_data[k][m] < data_section[m][0] or data_section[m][1] < \
                            self.anonymous_all_client_data[k][m]:
                        extreme_data_list.append(self.anonymous_all_client_data[k])
                        break
                        # self.anonymous_all_client_data[k][m] = (data_section[m][1] - data_section[m][0])/2
        for extreme_data in extreme_data_list:
            if extreme_data in self.anonymous_all_client_data:
                self.anonymous_all_client_data.remove(extreme_data)
        end_time = time.perf_counter()
        self.extream_detection_time += (end_time - start_time) * 1000

    def td_in_anonymous_data(self, anonymous_all_client_data):
        """
        对匿名数据执行真值发现
        :param anonymous_all_client_data:
        :return:
        """
        start_time = time.perf_counter()
        td_CRH = TD_CRH(anonymous_all_client_data, len(anonymous_all_client_data), len(anonymous_all_client_data[0]))
        td_CRH.TD(params.count)
        self.td_result = td_CRH.xm_i[params.count]
        end_time = time.perf_counter()
        self.td_time += (end_time - start_time) * 1000