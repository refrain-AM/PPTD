import time

import params
from AnonyMousePPTD.AS import AS
from AnonyMousePPTD.ClientManage import ClientManage
from AnonyMousePPTD.DR import DR
from data_generator.DataGenerator import DataGenerator
from utils.DetectOutliers import DetectOutliers


class AnonyMousePPTD:
    DR = None
    client_manager = None
    AS = None
    dataGenerator = None
    cloud_server_detection_extreme_data_time = 0

    def __init__(self):
        self.DR = DR()
        self.client_manager = ClientManage()
        self.AS = AS()
        self.cloud_server_detection_extreme_data_time = 0
        # self.dataGenerator = DataGenerator()
        print("对比方案初始化完成")

    def DR_init(self):
        self.DR.generate_seed()
        self.DR.generate_data_index()
        return self.DR.seed_list, self.DR.all_data_index_list

    def client_init(self, seed_list, all_data_index_list):
        self.client_manager.load_seed_and_data_index(seed_list, all_data_index_list)

    def data_generator_init(self):
        # 生成整个系统的用户数据
        self.dataGenerator.generate_base_data(params.base_data_rate, params.base_data_start, params.base_data_end,
                                              params.reliable_client_rate)
        # 打印basedata
        print("basedata")
        print(self.dataGenerator.base_data)

    def client_upload_data(self):
        # self.data_generator_init()
        self.client_manager.load_data(self.dataGenerator.generate_client_data())
        self.client_manager.generate_noise(2)
        # self.client_manager.verify_noise_data()
        self.client_manager.generate_masking_data()
        return self.client_manager.all_client_masking_data

    def client_upload_data_(self, all_client_data):
        self.client_manager.load_data(all_client_data)
        self.client_manager.generate_noise(1)
        # self.client_manager.verify_noise_data()
        self.client_manager.generate_masking_data()
        return self.client_manager.all_client_masking_data

    def as_aggregation_masking_data(self, all_client_masking_data, data_miss_list, data_section):
        self.AS.aggregation_masking_data_all_client(all_client_masking_data, data_miss_list)
        # 生成检测区间
        start_time = time.perf_counter()
        data_section_sifenwei = DetectOutliers.detect_outliers(self.AS.anonymous_all_client_data, params.alpha)
        print("data_section_sifenwei")
        print(data_section_sifenwei)
        for m in range(params.M - params.extreme_detection_prior_number):
            data_section[m + params.extreme_detection_prior_number][0] = \
                data_section_sifenwei[m + params.extreme_detection_prior_number][0]
            data_section[m + params.extreme_detection_prior_number][1] = \
                data_section_sifenwei[m + params.extreme_detection_prior_number][1]
        self.AS.detection_extreme_data(data_section)
        end_time = time.perf_counter()
        self.cloud_server_detection_extreme_data_time = (end_time - start_time) * 1000
        return self.AS.anonymous_all_client_data

    def as_td(self, anonymous_all_client_data):
        print("收到%d个有效的用户数据" % (len(anonymous_all_client_data)))
        self.AS.td_in_anonymous_data(anonymous_all_client_data)
        return self.AS.td_result
