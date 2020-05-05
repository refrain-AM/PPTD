# -*-coding:utf-8 -*-
import csv
import numpy as np
import matplotlib.pyplot as plt

def normal_worker(avg,sigma,K,M):
    # avg 均值; sigma^2 是方差; K workers数量; M objects数量
    # avg和sigma是长为M的list
    # excel表示是否生成excel文件
    workers=np.zeros((K,M),dtype=int)
    for k in range(K):
        for m in range(M):
            t=np.random.normal(avg[m],sigma[m])
            while t<0 or t>2*avg[m]:    
                t=np.random.normal(avg[m],sigma[m])
            workers[k,m]=t
    return workers

def disturb_data(data_input):
    rand=np.random.rand(data_input.shape[0],data_input.shape[1])
    out1=(rand*data_input).astype(np.int)
    out2=data_input-out1
    return out1,out2

def ini_avg(M):
    def_range_min = 10
    def_range_max = 10000
    t_v = np.random.randint(def_range_min,def_range_max,size=M)
    return t_v

def write_csv(data,filename):
    with open(filename,'w',newline='') as f:
        f_csv=csv.writer(f)
        f_csv.writerows(data)

M=1000
avg=ini_avg(M)
sigma=avg*0.0025

K=1000
normal=normal_worker(avg,sigma,K,M)
out1,out2=disturb_data(normal)
write_csv(normal,'normalworkers.csv')
write_csv(out1,"normalout1.csv")
write_csv(out2,"normalout2.csv")
