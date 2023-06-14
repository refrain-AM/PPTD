import copy

import params
from AnonyMousePPTD.AnonyMousePPTD import AnonyMousePPTD
from AnonymousEdgePPTD import AnonymousEdgePPTD
from data_generator.DataGenerator import DataGenerator
from utils.TestUtils import TestUtils


def run_once():
    # 初始化
    anonymousEdgePPTD = AnonymousEdgePPTD()
    # 密钥和随机种子协商
    anonymousEdgePPTD.key_agreement()
    # 生成数据
    anonymousEdgePPTD.data_generator()
    anonymousEdgePPTD.load_data()
    # 生成极端值检测区间
    anonymousEdgePPTD.generate_datection_section()

    # 添加极端值
    anonymousEdgePPTD.generate_extreme_data_index_(params.K, params.M, params.extreme_client_number,
                                                   params.extreme_task_rate)
    anonymousEdgePPTD.add_extreme_data()

    # 边缘节点之间协商数据上传位置
    all_group_in_client_data_index = anonymousEdgePPTD.generate_data_index(params.select_index)  # 组内数据添加位置
    de_all_group_client_data_index = anonymousEdgePPTD.edgeManager.de_all_group_client_data_index  # 整体数据添加位置

    # 客户端加载数据
    anonymousEdgePPTD.client_load_data(anonymousEdgePPTD.all_client_data)
    # 客户端上传数据
    client_masking_data_all_group = anonymousEdgePPTD.client_upload_data(all_group_in_client_data_index,
                                                                         de_all_group_client_data_index)  # 生成要上传的数据

    data_miss_list_all_group = anonymousEdgePPTD.generate_data_miss_list_(params.miss_rate)
    client_encrypt_ru_all_group = anonymousEdgePPTD.clientManager.client_encrypt_ru_all_group
    # 边缘节点聚合客户端数据
    anonymousEdgePPTD.edge_aggregation_client_data(client_masking_data_all_group, data_miss_list_all_group)
    # 云中心生成hash噪声
    hash_noise_others_group = anonymousEdgePPTD.cloud_server_generate_hash_noise(client_encrypt_ru_all_group,
                                                                                 data_miss_list_all_group)
    # 边缘节点添加云中心回馈的noise后上传数据,生成masking噪声并处理用户数据后上传
    edge_masking_data_all_group = anonymousEdgePPTD.edge_generate_edge_masking_data_all_group(hash_noise_others_group,
                                                                                              2)
    # 云中心聚合数据
    anonymousEdgePPTD.cloud_server_aggregation_edge_masking_data(
        edge_masking_data_all_group)
    # 检测极端值
    anonymous_all_client_data = anonymousEdgePPTD.cloud_server_detection_extreme_data(anonymousEdgePPTD.data_section)

    print("***********************************************************************")
    print("开始进行真值发现")
    # 对原始数据做TD
    td_result_original_data = anonymousEdgePPTD.original_data_TD(anonymousEdgePPTD.origin_client_data)
    print("原始数据真值发现结果")
    print(td_result_original_data)
    print("直接TD的RMSE = %f" % (TestUtils.get_RMSE(td_result_original_data, anonymousEdgePPTD.base_data_list)))

    # 对有离群值数据做TD
    td_result_original_data = anonymousEdgePPTD.original_data_TD(anonymousEdgePPTD.all_client_data)
    print("有离群值数据直接真值发现结果")
    print(td_result_original_data)
    print("直接TD的RMSE = %f" % (TestUtils.get_RMSE(td_result_original_data, anonymousEdgePPTD.base_data_list)))

    # 云中心执行TD
    print("************************************************************************")
    print("云中心TD")
    td_result_anonymous_all_client_data = anonymousEdgePPTD.cloud_server_TD(anonymous_all_client_data)
    print("真值发现结果")
    print(td_result_anonymous_all_client_data)
    print("本方案RMSE = %f" % (TestUtils.get_RMSE(td_result_anonymous_all_client_data, anonymousEdgePPTD.base_data_list)))

    # 执行对比方案
    print("************************************************************************")
    print("执行对比方案")
    # 初始化
    anonyMousePPTD = AnonyMousePPTD()
    # DR生成有各个用户的随机数种子，以及数据添加位置
    seed_list, all_data_index_list = anonyMousePPTD.DR_init()
    anonyMousePPTD.client_init(seed_list, all_data_index_list)
    all_client_masking_data = anonyMousePPTD.client_upload_data_(anonymousEdgePPTD.all_client_data)
    data_miss_list = list()
    for j in range(int(params.miss_rate * params.K)):
        data_miss_list.append(j)
    anonymous_all_client_data = anonyMousePPTD.as_aggregation_masking_data(all_client_masking_data,
                                                                           data_miss_list,
                                                                           anonymousEdgePPTD.data_section)
    td_result_anonymous_all_client_data = anonyMousePPTD.as_td(anonymous_all_client_data)
    print("真值发现结果")
    print(td_result_anonymous_all_client_data)
    print("对比方案RMSE = %f" % (TestUtils.get_RMSE(td_result_anonymous_all_client_data, anonymousEdgePPTD.base_data_list)))

    print("****************************************************************")
    print("本方案运行时间")
    print("one client_time = %f" % (anonymousEdgePPTD.clientManager.all_client_time / params.client_number))
    print("index_edge_time:")
    print(anonymousEdgePPTD.edgeManager.index_edge_time)
    print("aggregation_and_upload_edge_time:")
    print(anonymousEdgePPTD.edgeManager.aggregation_and_upload_edge_time)
    print(
        "cloud_server_aggreate_time=%f,cloud_server_generate_hash_noise_time=%f" % (
            anonymousEdgePPTD.cloudServer.cloud_server_aggreate_time,

            anonymousEdgePPTD.cloudServer.cloud_server_generate_hash_noise_time))

    print("对比方案运行时间")
    print("one client_time = %f" % (anonyMousePPTD.client_manager.all_client_time / params.client_number))
    print("cloud_server_aggreate_time=%f" % (anonyMousePPTD.AS.cloud_server_aggreate_time))


def run_test_computation():
    params.K = 0
    TestUtils.write_csv_one_line("D:/workPlace/researchRecord/anonymousPPTD/testResult/",
                                 "test_computation_M_10_result__.csv",
                                 ["N", "K", "worker_time", "EN_time",
                                  "server_time",
                                  "all_edge_add_cloud",
                                  "cloud_server_detection_extreme_data_time",
                                  "worker_time", "server_time",
                                  "cloud_server_detection_extreme_data_time"])
    for a in range(3):
        params.K = 4000 - 200 * a

        for i in range(3):
            print("开始第%d轮：-------------------------" % i)
            # 初始化参数
            params.K += 0
            params.client_number = params.K
            params.group_number_list = list()
            for edge_index in range(params.edge_number):
                params.group_number_list.append(int(params.K / params.edge_number))

            # 初始化
            anonymousEdgePPTD = AnonymousEdgePPTD()
            # 密钥和随机种子协商
            anonymousEdgePPTD.key_agreement()
            # 生成数据
            anonymousEdgePPTD.data_generator()
            anonymousEdgePPTD.load_data()
            # 生成极端值检测区间
            anonymousEdgePPTD.generate_datection_section()

            # 添加极端值
            anonymousEdgePPTD.generate_extreme_data_index_(params.K, params.M, params.extreme_client_number,
                                                           params.extreme_task_rate)
            anonymousEdgePPTD.add_extreme_data()

            # 边缘节点之间协商数据上传位置
            all_group_in_client_data_index = anonymousEdgePPTD.generate_data_index(params.select_index)  # 组内数据添加位置
            de_all_group_client_data_index = anonymousEdgePPTD.edgeManager.de_all_group_client_data_index  # 整体数据添加位置

            # 客户端加载数据
            anonymousEdgePPTD.client_load_data(anonymousEdgePPTD.all_client_data)
            # 客户端上传数据
            client_masking_data_all_group = anonymousEdgePPTD.client_upload_data(all_group_in_client_data_index,
                                                                                 de_all_group_client_data_index)  # 生成要上传的数据

            data_miss_list_all_group = anonymousEdgePPTD.generate_data_miss_list_(params.miss_rate)
            client_encrypt_ru_all_group = anonymousEdgePPTD.clientManager.client_encrypt_ru_all_group
            # 边缘节点聚合客户端数据
            anonymousEdgePPTD.edge_aggregation_client_data(client_masking_data_all_group, data_miss_list_all_group)
            # 云中心生成hash噪声
            hash_noise_others_group = anonymousEdgePPTD.cloud_server_generate_hash_noise(client_encrypt_ru_all_group,
                                                                                         data_miss_list_all_group)
            # 边缘节点添加云中心回馈的noise后上传数据,生成masking噪声并处理用户数据后上传
            edge_masking_data_all_group = anonymousEdgePPTD.edge_generate_edge_masking_data_all_group(
                hash_noise_others_group,
                2)

            # 云中心聚合数据
            anonymousEdgePPTD.cloud_server_aggregation_edge_masking_data(
                edge_masking_data_all_group)
            # 检测极端值
            anonymous_all_client_data = anonymousEdgePPTD.cloud_server_detection_extreme_data(
                anonymousEdgePPTD.data_section)

            print("***********************************************************************")
            print("开始进行真值发现")
            # 对原始数据做TD
            td_result_original_data = anonymousEdgePPTD.original_data_TD(anonymousEdgePPTD.origin_client_data)
            print("原始数据真值发现结果")
            print(td_result_original_data)
            print("直接TD的RMSE = %f" % (TestUtils.get_RMSE(td_result_original_data, anonymousEdgePPTD.base_data_list)))

            # 对有离群值数据做TD
            # td_result_original_data = anonymousEdgePPTD.original_data_TD(anonymousEdgePPTD.all_client_data)
            # print("有离群值数据直接真值发现结果")
            # print(td_result_original_data)
            # print("直接TD的RMSE = %f" % (TestUtils.get_RMSE(td_result_original_data, anonymousEdgePPTD.base_data_list)))

            # 云中心执行TD
            print("云中心TD")
            td_result_anonymous_all_client_data = anonymousEdgePPTD.cloud_server_TD(anonymous_all_client_data)
            print("真值发现结果")
            print(td_result_anonymous_all_client_data)
            print("本方案RMSE = %f" % (
                TestUtils.get_RMSE(td_result_anonymous_all_client_data, anonymousEdgePPTD.base_data_list)))
            print("本方案耗时")
            print([params.K, anonymousEdgePPTD.clientManager.all_client_time / params.client_number,
                   anonymousEdgePPTD.edgeManager.index_edge_time[0],
                   anonymousEdgePPTD.edgeManager.aggregation_and_upload_edge_time[0],
                   anonymousEdgePPTD.cloudServer.cloud_server_aggreate_time,
                   anonymousEdgePPTD.cloudServer.cloud_server_generate_hash_noise_time,
                   (anonymousEdgePPTD.edgeManager.index_edge_time[0] +
                    anonymousEdgePPTD.edgeManager.aggregation_and_upload_edge_time[
                        0]) * params.edge_number + anonymousEdgePPTD.cloudServer.cloud_server_aggreate_time + anonymousEdgePPTD.cloudServer.cloud_server_generate_hash_noise_time,
                   anonymousEdgePPTD.cloud_server_detection_extreme_data_time])
            # TestUtils.write_csv_one_line("D:/workPlace/researchRecord/anonymousPPTD/testResult/",
            #                              "test_computation_M_5_result.csv",
            #                              [params.edge_number, params.K,
            #                               anonymousEdgePPTD.clientManager.all_client_time / params.client_number,
            #                               anonymousEdgePPTD.edgeManager.index_edge_time[0],
            #                               anonymousEdgePPTD.edgeManager.aggregation_and_upload_edge_time[0],
            #                               anonymousEdgePPTD.cloudServer.cloud_server_aggreate_time,
            #                               anonymousEdgePPTD.cloudServer.cloud_server_generate_hash_noise_time,
            #                               (anonymousEdgePPTD.edgeManager.index_edge_time[0] +
            #                                anonymousEdgePPTD.edgeManager.aggregation_and_upload_edge_time[
            #                                    0]) * params.edge_number + anonymousEdgePPTD.cloudServer.cloud_server_aggreate_time + anonymousEdgePPTD.cloudServer.cloud_server_generate_hash_noise_time,
            #                               anonymousEdgePPTD.cloud_server_detection_extreme_data_time])
            # 执行对比方案
            print("************************************************************************")
            print("执行对比方案")
            # 初始化
            anonyMousePPTD = AnonyMousePPTD()
            # DR生成有各个用户的随机数种子，以及数据添加位置
            seed_list, all_data_index_list = anonyMousePPTD.DR_init()
            anonyMousePPTD.client_init(seed_list, all_data_index_list)
            all_client_masking_data = anonyMousePPTD.client_upload_data_(anonymousEdgePPTD.all_client_data)
            data_miss_list = list()
            for j in range(int(params.miss_rate * params.K)):
                data_miss_list.append(j)
            anonymous_all_client_data = anonyMousePPTD.as_aggregation_masking_data(all_client_masking_data,
                                                                                   data_miss_list,
                                                                                   anonymousEdgePPTD.data_section)
            td_result_anonymous_all_client_data = anonyMousePPTD.as_td(anonymous_all_client_data)
            print("真值发现结果")
            print(td_result_anonymous_all_client_data)
            print("对比方案RMSE = %f" % (
                TestUtils.get_RMSE(td_result_anonymous_all_client_data, anonymousEdgePPTD.base_data_list)))

            print("***********************计算开销******************************")

            print("边缘节点个数:%d,用户个数:%d" % (params.edge_number, params.K))
            print("本方案运行时间")
            print("one_client_time = %f" % (anonymousEdgePPTD.clientManager.all_client_time / params.client_number))
            print("index_edge_time:")
            print(anonymousEdgePPTD.edgeManager.index_edge_time)
            print("aggregation_and_upload_edge_time:")
            print(anonymousEdgePPTD.edgeManager.aggregation_and_upload_edge_time)
            print(
                "cloud_server_aggreate_time=%f,cloud_server_generate_hash_noise_time=%f" % (
                    anonymousEdgePPTD.cloudServer.cloud_server_aggreate_time,
                    anonymousEdgePPTD.cloudServer.cloud_server_generate_hash_noise_time))

            print("对比方案运行时间")
            print("one client_time = %f" % (anonyMousePPTD.client_manager.all_client_time / params.client_number))
            print("cloud_server_aggreate_time=%f" % anonyMousePPTD.AS.cloud_server_aggreate_time)

            TestUtils.write_csv_one_line("D:/workPlace/researchRecord/anonymousPPTD/testResult/",
                                         "test_computation_M_10_result__.csv",
                                         [params.edge_number, params.K,
                                          anonymousEdgePPTD.clientManager.all_client_time / params.client_number,
                                          anonymousEdgePPTD.edgeManager.index_edge_time[0] + anonymousEdgePPTD.edgeManager.aggregation_and_upload_edge_time[0],
                                          anonymousEdgePPTD.cloudServer.cloud_server_aggreate_time + anonymousEdgePPTD.cloudServer.cloud_server_generate_hash_noise_time,
                                          (anonymousEdgePPTD.edgeManager.index_edge_time[0] +
                                           anonymousEdgePPTD.edgeManager.aggregation_and_upload_edge_time[
                                               0]) * params.edge_number + anonymousEdgePPTD.cloudServer.cloud_server_aggreate_time + anonymousEdgePPTD.cloudServer.cloud_server_generate_hash_noise_time,
                                          anonymousEdgePPTD.cloud_server_detection_extreme_data_time,
                                          anonyMousePPTD.client_manager.all_client_time / params.client_number,
                                          anonyMousePPTD.AS.cloud_server_aggreate_time,
                                          anonyMousePPTD.cloud_server_detection_extreme_data_time])


def run_test_accuracy():
    # fileName = "test_accuracy_with_exit_.csv"
    fileName = "test_accuracy_withOutliers.csv"
    datafileName = "client_data.csv"
    TestUtils.write_csv_one_line("D:/workPlace/researchRecord/anonymousPPTD/testResult/",
                                 fileName,
                                 ["params.K", "params.miss_rate", "params.extreme_client_number", " TD_original_RMSE",
                                  "TD_original_MAE",
                                  "TD_Outlier_RMSE", "TD_Outlier_MAE",
                                  "ODPPTD_Outlier_RMSE", "ODPPTD_Outlier_MAE",
                                  "AN_Outlier_RMSE", " AN_Outlier_MAE"])

    # # 生成原始数据和极端值检测区间
    # dataGenerator = DataGenerator()
    # dataGenerator.generate_base_data(params.base_data_rate, params.base_data_start, params.base_data_end,
    #                                  params.reliable_client_rate)
    # print(dataGenerator.reliable_client)
    # dataGenerator.generate_client_data()
    # print(111)
    # print(dataGenerator.base_data)
    # print(111)
    # dataGenerator.sava_all_client_data("D:/workPlace/researchRecord/anonymousPPTD/testResult/", datafileName)
    # dataGenerator.read_all_client_data("D:/workPlace/researchRecord/anonymousPPTD/testResult/", datafileName)
    # print(dataGenerator.base_data)
    # dataGenerator.generate_datection_section()
    params.alpha = 2.0
    for i in range(3):
        params.extreme_client_number = int(( (i+6) / 100) * params.K)
        params.miss_rate = 0
        # 初始化参数
        # params.miss_rate = 0
        # if params.extreme_client_number == 110:
        #     if params.alpha < 2.5:
        #         if params.alpha*10%2 == 0:
        #             params.alpha += 0.3
        #         else:
        #             params.alpha += 0.2
        #     else:
        #         params.alpha += 1
        #     if params.alpha > 5:
        #         params.alpha += 5
        #     if params.alpha > 10:
        #         params.alpha += 10
        #     if params.alpha == 100:
        #         break
        #     params.extreme_client_number = 0
        # else:
        #     params.extreme_client_number += 10

        # if i < 10 :
        #     params.extreme_client_number = int(( (10) / 100) * params.K)
        #     params.miss_rate = (i + 1) / 100
        #     # params.miss_rate = 0
        # else:
        #     params.extreme_client_number = int((0 / 100) * params.K)
        #     params.miss_rate = (i + 1 - 10) / 100
        TestUtils.write_csv_one_line("D:/workPlace/researchRecord/anonymousPPTD/testResult/", fileName, [])
        TestUtils.write_csv_one_line("D:/workPlace/researchRecord/anonymousPPTD/testResult/", fileName, [])
        for j in range(5):
            print("掉线率为%f,非正常用户个数为%f,开始第%d轮:" % (params.miss_rate, params.extreme_client_number,j))
            # 初始化
            anonymousEdgePPTD = AnonymousEdgePPTD()
            # 密钥和随机种子协商
            anonymousEdgePPTD.key_agreement()
            # 读取数据
            anonymousEdgePPTD.dataGenerator.read_all_client_data(
                "D:/workPlace/researchRecord/anonymousPPTD/testResult/",
                datafileName)
            # 加载数据
            anonymousEdgePPTD.load_data()
            # 生成极端值检测区间
            anonymousEdgePPTD.generate_datection_section()
            # 添加极端值
            anonymousEdgePPTD.generate_extreme_data_index_(params.K, params.M, params.extreme_client_number,
                                                           params.extreme_task_rate)
            anonymousEdgePPTD.add_extreme_data()
            # # 边缘节点之间协商数据上传位置
            # all_group_in_client_data_index = anonymousEdgePPTD.generate_data_index(params.select_index)  # 组内数据添加位置
            # de_all_group_client_data_index = anonymousEdgePPTD.edgeManager.de_all_group_client_data_index  # 整体数据添加位置
            #
            # # 客户端加载数据
            # anonymousEdgePPTD.client_load_data(anonymousEdgePPTD.all_client_data)
            # # 客户端上传数据
            # client_masking_data_all_group = anonymousEdgePPTD.client_upload_data(all_group_in_client_data_index,
            #                                                                      de_all_group_client_data_index)  # 生成要上传的数据
            # 掉线用户
            data_miss_list_all_group = anonymousEdgePPTD.generate_data_miss_list_(params.miss_rate)
            print(data_miss_list_all_group)
            # client_encrypt_ru_all_group = anonymousEdgePPTD.clientManager.client_encrypt_ru_all_group
            # # 边缘节点聚合客户端数据
            # anonymousEdgePPTD.edge_aggregation_client_data(client_masking_data_all_group, data_miss_list_all_group)
            # # 云中心生成hash噪声
            # hash_noise_others_group = anonymousEdgePPTD.cloud_server_generate_hash_noise(client_encrypt_ru_all_group,
            #                                                                              data_miss_list_all_group)
            # # 边缘节点添加云中心回馈的noise后上传数据,生成masking噪声并处理用户数据后上传
            # edge_masking_data_all_group = anonymousEdgePPTD.edge_generate_edge_masking_data_all_group(
            #     hash_noise_others_group,2)

            temp_client_data = copy.deepcopy(anonymousEdgePPTD.all_client_data)
            # 准确率测试专用
            anonymous_all_client_data = anonymousEdgePPTD.cloud_server_aggregation_edge_masking_data_(
                data_miss_list_all_group,
                anonymousEdgePPTD.all_client_data
                , anonymousEdgePPTD.data_section)

            print("*************************开始进行真值发现,并计算准确率********************************")
            print("开始进行真值发现")
            # 对原始数据做TD
            td_result_original_data = anonymousEdgePPTD.original_data_TD(anonymousEdgePPTD.origin_client_data)
            # print("原始数据真值发现结果")
            # print(td_result_original_data)
            TD_original_RMSE = TestUtils.get_RMSE(td_result_original_data, anonymousEdgePPTD.base_data_list)
            TD_original_MAE = TestUtils.get_MAE(td_result_original_data, anonymousEdgePPTD.base_data_list)
            print("直接TD的RMSE = %f" % TD_original_RMSE)
            print("直接TD的MAE = %f" % TD_original_MAE)

            # 对有离群值数据做TD
            td_result_original_data = anonymousEdgePPTD.original_data_TD(temp_client_data)
            # print("有离群值数据直接真值发现结果")
            # print(td_result_original_data)
            TD_Outlier_RMSE = TestUtils.get_RMSE(td_result_original_data, anonymousEdgePPTD.base_data_list)
            TD_Outlier_MAE = TestUtils.get_MAE(td_result_original_data, anonymousEdgePPTD.base_data_list)
            print("有离群值数据直接真值发现结果RMSE = %f" % TD_Outlier_RMSE)
            print("有离群值数据直接真值发现结果MAE = %f" % TD_Outlier_MAE)

            # 云中心执行TD
            print("云中心TD")
            td_result_anonymous_all_client_data = anonymousEdgePPTD.cloud_server_TD(anonymous_all_client_data)
            # print("真值发现结果")
            # print(td_result_anonymous_all_client_data)
            ODPPTD_Outlier_RMSE = TestUtils.get_RMSE(td_result_anonymous_all_client_data,
                                                     anonymousEdgePPTD.base_data_list)
            ODPPTD_Outlier_MAE = TestUtils.get_MAE(td_result_anonymous_all_client_data,
                                                   anonymousEdgePPTD.base_data_list)
            print("本方案RMSE = %f" % ODPPTD_Outlier_RMSE)
            print("本方案MAE = %f" % ODPPTD_Outlier_MAE)

            # 执行对比方案
            # print("************************************************************************")
            # print("执行对比方案")
            # # 初始化
            # anonyMousePPTD = AnonyMousePPTD()
            # # DR生成有各个用户的随机数种子，以及数据添加位置
            # seed_list, all_data_index_list = anonyMousePPTD.DR_init()
            # anonyMousePPTD.client_init(seed_list, all_data_index_list)
            # all_client_masking_data = anonyMousePPTD.client_upload_data_(temp_client_data)
            # data_miss_list = list()
            # for j in range(int(params.miss_rate * params.K)):
            #     data_miss_list.append(j)
            # anonymous_all_client_data = anonyMousePPTD.as_aggregation_masking_data(all_client_masking_data,
            #                                                                        data_miss_list,
            #                                                                        anonymousEdgePPTD.data_section)
            # td_result_anonymous_all_client_data = anonyMousePPTD.as_td(anonymous_all_client_data)
            # print("真值发现结果")
            # AN_Outlier_RMSE = TestUtils.get_RMSE(td_result_anonymous_all_client_data, anonymousEdgePPTD.base_data_list)
            # AN_Outlier_MAE = TestUtils.get_MAE(td_result_anonymous_all_client_data, anonymousEdgePPTD.base_data_list)
            # print("对比方案RMSE = %f" % AN_Outlier_RMSE)
            # print("对比方案MAE = %f" % AN_Outlier_MAE)

            TestUtils.write_csv_one_line("D:/workPlace/researchRecord/anonymousPPTD/testResult/",
                                         fileName,
                                         [params.K, params.miss_rate, params.extreme_client_number, TD_original_RMSE,
                                          TD_original_MAE,
                                          TD_Outlier_RMSE, TD_Outlier_MAE,
                                          ODPPTD_Outlier_RMSE, ODPPTD_Outlier_MAE, "", "", params.base_data_end,
                                          params.error_rate_,params.alpha])
            # TestUtils.write_csv_one_line("D:/workPlace/researchRecord/anonymousPPTD/testResult/",
            #                              fileName,
            #                              [params.K, params.miss_rate, params.extreme_client_number,TD_original_RMSE, TD_original_MAE,
            #                               TD_Outlier_RMSE, TD_Outlier_MAE,
            #                               ODPPTD_Outlier_RMSE, ODPPTD_Outlier_MAE,
            #                               AN_Outlier_RMSE, AN_Outlier_MAE,params.base_data_end,params.error_rate_,params.alpha,len(anonymous_all_client_data)])

# run_once()
# run_test_computation()
run_test_accuracy()
