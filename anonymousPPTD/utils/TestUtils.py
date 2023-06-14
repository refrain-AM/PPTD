import csv


class TestUtils:

    def __init__(self):
        pass

    @staticmethod
    def get_RMSE(result_list, truth_list):
        M = len(result_list)
        temp = 0
        for m in range(M):
            temp = temp + (result_list[m] - truth_list[m]) ** 2
        return (temp / M) ** 0.5

    @staticmethod
    def get_MAE(result_list, truth_list):
        M = len(result_list)
        temp = 0
        for m in range(M):
            temp = temp + abs(result_list[m] - truth_list[m])
        return (temp / M)

    @staticmethod
    def write_csv(file_path, file_name, data_list):
        # !/usr/bin/python3
        # -*- coding: utf-8 -*-

        # 导入CSV安装包

        # 1. 创建文件对象
        f = open(file_path + file_name, 'w', encoding='utf-8', newline='')

        # 2. 基于文件对象构建 csv写入对象
        csv_writer = csv.writer(f)

        for data in data_list:
            csv_writer.writerow(data)

        # # 3. 构建列表头
        # csv_writer.writerow(["姓名", "年龄", "性别"])
        #
        # # 4. 写入csv文件内容
        # csv_writer.writerow(["l", '18', '男'])
        # csv_writer.writerow(["c", '20', '男'])
        # csv_writer.writerow(["w", '22', '女'])

        # 5. 关闭文件
        f.close()

    @staticmethod
    def write_csv_one_line(file_path, file_name, data_list):
        # !/usr/bin/python3
        # -*- coding: utf-8 -*-

        # 导入CSV安装包

        # 1. 创建文件对象
        f = open(file_path + file_name, 'a+', encoding='utf-8', newline='')

        # 2. 基于文件对象构建 csv写入对象
        csv_writer = csv.writer(f)
        csv_writer.writerow(data_list)

        # # 3. 构建列表头
        # csv_writer.writerow(["姓名", "年龄", "性别"])
        #
        # # 4. 写入csv文件内容
        # csv_writer.writerow(["l", '18', '男'])
        # csv_writer.writerow(["c", '20', '男'])
        # csv_writer.writerow(["w", '22', '女'])

        # 5. 关闭文件
        f.close()

    @staticmethod
    def write_csv_one_line_title(file_path, file_name, data_list):
        f = open(file_path + file_name, 'a', encoding='utf-8', newline='')
        csv_writer = csv.writer(f)
        csv_writer.writerow(data_list)
        f.close()

    @staticmethod
    def write_csv_one_line_title_(file_path, file_name, data_list):
        f = open(file_path + file_name, 'w', encoding='utf-8', newline='')
        csv_writer = csv.writer(f)
        csv_writer.writerow(data_list)
        f.close()


TestUtils.write_csv_one_line("D:/workPlace/researchRecord/anonymousPPTD/testResult/", "测试结果.csv", [1, 2, 3, 4, 5])
