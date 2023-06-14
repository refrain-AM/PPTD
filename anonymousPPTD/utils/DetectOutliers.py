import params


class DetectOutliers:
    def __init__(self):
        pass

    @staticmethod
    def detect_outliers(data_list, alpha):
        K = len(data_list)
        if K == 0:
            print("极端值检测输入数据为0")
            return
        M = len(data_list[0])
        data_section = list()
        for m in range(M):
            # 获取数据
            temp_data_list_m = list()
            for k in range(K):
                temp_data_list_m.append(data_list[k][m])
            # 排序
            temp_data_list_m.sort()
            # 获取四分位数
            Q1 = temp_data_list_m[int(K / 4)]
            Q3 = temp_data_list_m[int((3 * K) / 4)]
            start = Q1 - alpha * (Q3 - Q1)
            end = Q3 + alpha * (Q3 - Q1)
            data_section_one_task = list()
            data_section_one_task.append(start)
            data_section_one_task.append(end)
            data_section.append(data_section_one_task)
        return data_section
