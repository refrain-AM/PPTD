import numpy as np
from Crypto.PublicKey import ECC
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
import shamir
import time
import math
from random import randint
import matplotlib.pyplot as plt


# 这部分应该重写效率函数，先把协议写出来
def KA_gen():
    start=time.time()
    k1=ECC.generate(curve='P-256')
    end=time.time()
    return end-start
def KA_agree():
    # single call to KA
    k1=ECC.generate(curve='P-256')
    temp_key=ECC.generate(curve='P-256')

    start=time.time()
    shared_key = k1.pointQ * temp_key.d
    end=time.time()
    return end - start
def shamir_t(nk, t,l=32):
    # single call to shamir's share and recover
    #
    res=[]
    max=2**l-1
    s=np.random.randint(0,2**16)
    start=time.time()
    rs = shamir.make_random_shares(t, nk - 1, s, max)
    end=time.time()
    res.append(end-start)

    start=time.time()
    shamir.recover_secret(rs[:t],max)
    end=time.time()
    res.append(end-start)
    return res
def AE(message_size):
    res=[]
    sk=get_random_bytes(16)
    header=b'header'
    plaintext = get_random_bytes(message_size)

    start=time.time()
    cipher=AES.new(sk,AES.MODE_GCM)
    cipher.update(header)
    ciphertext, tag=cipher.encrypt_and_digest(plaintext)
    end=time.time()

    res.append(end-start)

    start=time.time()
    nonce=cipher.nonce
    cipher=AES.new(sk,AES.MODE_GCM,nonce=nonce)
    cipher.update(header)
    plaintext=cipher.decrypt_and_verify(ciphertext,tag)
    end=time.time()

    res.append(end-start)
    return res
def creating_mask_r(M):
    r = get_random_bytes(16)
    start = time.time()
    for m in range(M):
        hash_ob = SHA256.new(r + bytes(bin(1), encoding='utf-8'))
        hash_ob.digest()
    end = time.time()
    return end - start
def creating_mask_s(nk,M):
    s = get_random_bytes(16)

    start = time.time()
    for m in range(M):
        for i in range(nk):
            hash_ob = SHA256.new(s + bytes(bin(1), encoding='utf-8'))
            hash_ob.digest()
    end = time.time()
    return end - start

def worker_computation(nk,M,drop_rate):
    # numbers are 32 bits
    res=KA_gen()
    res+=KA_agree()*(nk-1)
    res+=shamir_t(nk,math.ceil(3*nk/4),32)[0]
    res+=shamir_t(nk,math.ceil(3*nk/4),128)[0]
    ae_time=AE(1+1+16+4)
    res+=ae_time[0]*(nk-1)+ae_time[1]*(nk-1)
    res+=creating_mask_r(M)
    res+=creating_mask_s(nk,M)
    res+=AE(1+1+4)[0]*math.floor(nk*(1-drop_rate))
    return res

def fog_computation(nk,drop_rate,M,fog):
    res=KA_gen()
    res+=KA_agree()*fog
    res+=shamir_t(nk,math.ceil(3*nk/4),128)[1]*math.ceil(nk*drop_rate)
    res+=creating_mask_s(nk,M)*math.ceil(nk*drop_rate)
    res+=creating_mask_s(fog,M)

    return res


def cloud_computation(nk,n,M,drop_rate):
    res = AE(1+1+4)[1]*math.floor(nk*(1-drop_rate))
    res+=shamir_t(nk,math.ceil(3*nk/4),32)[1]*n
    res+=creating_mask_r(M)*n

    return res

def rtpt_cloud_computation(n,M,drop_rate):
    res=0
    res+=shamir_t(n,math.ceil(3*n/4),128)[1]*math.ceil(n*drop_rate)
    res+=creating_mask_s(n,M)*math.ceil(n*drop_rate)
    res += shamir_t(n, math.ceil(3 * n / 4), 32)[1] * n
    res+=creating_mask_r(M)*n
    return res
def varying_workers():
    FPTD_worker = []
    FPTD_fog = []
    FPTD_cloud = []
    RTPT_worker = []
    RTPT_cloud = []
    for n in [100, 150, 200, 250, 300, 350, 400, 450, 500]:
        temp_fptd_worker = 0
        temp_fptd_fog = 0
        temp_fptd_cloud = 0
        temp_rtpt_worker = 0
        temp_rtpt_cloud = 0
        for t in range(50):
            fog = 10
            nk = n // fog
            drop_rate = 0.05
            M = 100

            temp_fptd_worker += worker_computation(nk, M + 1, drop_rate) + worker_computation(nk, M, drop_rate)
            temp_fptd_fog += fog_computation(nk, drop_rate, M + 1, fog) + fog_computation(nk, drop_rate, M, fog)
            temp_fptd_cloud += cloud_computation(nk, n, M + 1, drop_rate) + cloud_computation(nk, n, M, drop_rate)
            temp_rtpt_worker += worker_computation(n, M + 1, drop_rate) + worker_computation(n, M, drop_rate)
            temp_rtpt_cloud += rtpt_cloud_computation(n, M + 1, drop_rate) + rtpt_cloud_computation(n, M, drop_rate)

        FPTD_worker.append(temp_fptd_worker / 50)
        FPTD_fog.append(temp_fptd_fog / 50)
        FPTD_cloud.append(temp_fptd_cloud / 50)
        RTPT_worker.append(temp_rtpt_worker / 50)
        RTPT_cloud.append(temp_rtpt_cloud / 50)
    np.savetxt('Computation/Worker/FPTD_worker.txt', FPTD_worker)
    np.savetxt('Computation/Worker/FPTD_fog.txt', FPTD_fog)
    np.savetxt('Computation/Worker/FPTD_cloud.txt', FPTD_cloud)
    np.savetxt('Computation/Worker/RTPT_worker.txt', RTPT_worker)
    np.savetxt('Computation/Worker/RTPT_cloud.txt', RTPT_cloud)

    plt.figure(1)
    plt.plot([100, 150, 200, 250, 300, 350, 400, 450, 500], FPTD_worker, color='red')
    plt.plot([100, 150, 200, 250, 300, 350, 400, 450, 500], RTPT_worker, color='blue')

    plt.figure(2)
    plt.plot([100, 150, 200, 250, 300, 350, 400, 450, 500], FPTD_fog, color='red')
    plt.plot([100, 150, 200, 250, 300, 350, 400, 450, 500], FPTD_cloud, color='blue')
    plt.plot([100, 150, 200, 250, 300, 350, 400, 450, 500], RTPT_cloud, color='green')

    plt.show()
def varying_fog():
    FPTD_worker = []
    FPTD_fog = []
    FPTD_cloud = []
    RTPT_worker = []
    RTPT_cloud = []
    for fog in [1,2,3,4,5,6,10,15]:
        n=300
        nk = n // fog
        drop_rate = 0.05
        M = 100
        temp_fptd_worker = 0
        temp_fptd_fog = 0
        temp_fptd_cloud = 0
        temp_rtpt_worker = 0
        temp_rtpt_cloud = 0
        for t in range(20):
            temp_fptd_worker += worker_computation(nk, M + 1, drop_rate) + worker_computation(nk, M, drop_rate)
            temp_fptd_fog += fog_computation(nk, drop_rate, M + 1, fog) + fog_computation(nk, drop_rate, M, fog)
            temp_fptd_cloud += cloud_computation(nk, n, M + 1, drop_rate) + cloud_computation(nk, n, M, drop_rate)
            temp_rtpt_worker += worker_computation(n, M + 1, drop_rate) + worker_computation(n, M, drop_rate)
            temp_rtpt_cloud += rtpt_cloud_computation(n, M + 1, drop_rate) + rtpt_cloud_computation(n, M, drop_rate)

        FPTD_worker.append(temp_fptd_worker / 20)
        FPTD_fog.append(temp_fptd_fog / 20)
        FPTD_cloud.append(temp_fptd_cloud / 20)
        RTPT_worker.append(temp_rtpt_worker / 20)
        RTPT_cloud.append(temp_rtpt_cloud / 20)
    np.savetxt('Computation/Fog/FPTD_worker.txt', FPTD_worker)
    np.savetxt('Computation/Fog/FPTD_fog.txt', FPTD_fog)
    np.savetxt('Computation/Fog/FPTD_cloud.txt', FPTD_cloud)
    np.savetxt('Computation/Fog/RTPT_worker.txt', RTPT_worker)
    np.savetxt('Computation/Fog/RTPT_cloud.txt', RTPT_cloud)

    # plt.figure(3)
    # plt.plot([2,3,4,5,6,10,15], FPTD_worker, color='red')
    # plt.plot([2,3,4,5,6,10,15], RTPT_worker, color='blue')
    #
    # plt.figure(4)
    # plt.plot([2,3,4,5,6,10,15], FPTD_fog, color='red')
    # plt.plot([2,3,4,5,6,10,15], FPTD_cloud, color='blue')
    # plt.plot([2,3,4,5,6,10,15], RTPT_cloud, color='green')
    #
    # plt.show()
def varying_drop_rate():
    # FPTD_worker = []
    # FPTD_fog = []
    # FPTD_cloud = []
    RTPT_worker = []
    # RTPT_cloud = []
    for drop_rate in [0.00,0.05,0.10,0.15,0.20]:
        # temp_fptd_worker = 0
        # temp_fptd_fog = 0
        # temp_fptd_cloud = 0
        temp_rtpt_worker = 0
        # temp_rtpt_cloud = 0
        for t in range(50):
            n=300
            fog =5
            nk = n // fog
            M = 100

            # temp_fptd_worker += worker_computation(nk, M + 1, drop_rate) + worker_computation(nk, M, drop_rate)
            # temp_fptd_fog += fog_computation(nk, drop_rate, M + 1, fog) + fog_computation(nk, drop_rate, M, fog)
            # temp_fptd_cloud += cloud_computation(nk, n, M + 1, drop_rate) + cloud_computation(nk, n, M, drop_rate)
            temp_rtpt_worker += worker_computation(n, M + 1, drop_rate) + worker_computation(n, M, drop_rate)
            # temp_rtpt_cloud += rtpt_cloud_computation(n, M + 1, drop_rate) + rtpt_cloud_computation(n, M, drop_rate)

        # FPTD_worker.append(temp_fptd_worker / 50)
        # FPTD_fog.append(temp_fptd_fog / 50)
        # FPTD_cloud.append(temp_fptd_cloud / 50)
        RTPT_worker.append(temp_rtpt_worker / 1)
        # RTPT_cloud.append(temp_rtpt_cloud / 50)
    # np.savetxt('Computation/Drop rate/FPTD_worker.txt', FPTD_worker)
    # np.savetxt('Computation/Drop rate/FPTD_fog.txt', FPTD_fog)
    # np.savetxt('Computation/Drop rate/FPTD_cloud.txt', FPTD_cloud)
    np.savetxt('Computation/Drop rate/RTPT_worker.txt', RTPT_worker)
    # np.savetxt('Computation/Drop rate/RTPT_cloud.txt', RTPT_cloud)

    # plt.figure(5)
    # plt.plot([0.00,0.05,0.10,0.15,0.20], FPTD_worker, color='red')
    # plt.plot([0.00,0.05,0.10,0.15,0.20], RTPT_worker, color='blue')
    #
    # plt.figure(6)
    # plt.plot([0.00,0.05,0.10,0.15,0.20], FPTD_fog, color='red')
    # plt.plot([0.00,0.05,0.10,0.15,0.20], FPTD_cloud, color='blue')
    # plt.plot([0.00,.05,0.10,0.15,0.20], RTPT_cloud, color='green')
    #
    # plt.show()
def varying_objects():
    # FPTD_worker = []
    # FPTD_fog = []
    # FPTD_cloud = []
    RTPT_worker = []
    # RTPT_cloud = []
    for M in [20,40,60,80,100]:
        # temp_fptd_worker = 0
        # temp_fptd_fog = 0
        # temp_fptd_cloud = 0
        temp_rtpt_worker = 0
        # temp_rtpt_cloud = 0
        for t in range(1):
            n = 300
            fog = 5
            nk = n // fog
            drop_rate=0.05

            # temp_fptd_worker += worker_computation(nk, M + 1, drop_rate) + worker_computation(nk, M, drop_rate)
            # temp_fptd_fog += fog_computation(nk, drop_rate, M + 1, fog) + fog_computation(nk, drop_rate, M, fog)
            # temp_fptd_cloud += cloud_computation(nk, n, M + 1, drop_rate) + cloud_computation(nk, n, M, drop_rate)
            temp_rtpt_worker += worker_computation(n, M + 1, drop_rate) + worker_computation(n, M, drop_rate)
            # temp_rtpt_cloud += rtpt_cloud_computation(n, M + 1, drop_rate) + rtpt_cloud_computation(n, M, drop_rate)

        # FPTD_worker.append(temp_fptd_worker / 50)
        # FPTD_fog.append(temp_fptd_fog / 50)
        # FPTD_cloud.append(temp_fptd_cloud / 50)
        RTPT_worker.append(temp_rtpt_worker / 50)
        # RTPT_cloud.append(temp_rtpt_cloud / 50)
    # np.savetxt('Computation/Objects/FPTD_worker.txt', FPTD_worker)
    # np.savetxt('Computation/Objects/FPTD_fog.txt', FPTD_fog)
    # np.savetxt('Computation/Objects/FPTD_cloud.txt', FPTD_cloud)
    np.savetxt('Computation/Objects/RTPT_worker.txt', RTPT_worker)
    # np.savetxt('Computation/Objects/RTPT_cloud.txt', RTPT_cloud)

    # plt.figure(7)
    # plt.plot([20,40,60,80,100], FPTD_worker, color='red')
    # plt.plot([20,40,60,80,100], RTPT_worker, color='blue')
    #
    # plt.figure(8)
    # plt.plot([20,40,60,80,100], FPTD_fog, color='red')
    # plt.plot([20,40,60,80,100], FPTD_cloud, color='blue')
    # plt.plot([20,40,60,80,100], RTPT_cloud, color='green')
    #
    # plt.show()
def cloud_composition():
    n = 300
    fog = 5
    nk = n // fog
    M = 100
    drop_rate = 0.05

    fptd_decryption_time=0
    fptd_recover_time=0
    fptd_mask_time=0

    rtpt_recover_time=0
    rtpt_mask_time=0
    for t in range(50):
        fptd_decryption_time+=AE(1+1+4)[1]*math.floor(nk*(1-drop_rate))
        fptd_recover_time += shamir_t(nk, math.ceil(3 * nk / 4), 32)[1] * n
        fptd_mask_time += creating_mask_r(M) * n

        rtpt_recover_time+=shamir_t(n,math.ceil(3*n/4),128)[1]*math.ceil(n*drop_rate)+shamir_t(n, math.ceil(3 * n / 4), 32)[1] * n
        rtpt_mask_time +=creating_mask_s(n,M)*math.ceil(n*drop_rate)+creating_mask_r(M)*n

    fptd_decryption_time=fptd_decryption_time/50
    fptd_recover_time=fptd_recover_time/50
    fptd_mask_time=fptd_mask_time/50

    rtpt_recover_time=rtpt_recover_time/50
    rtpt_mask_time=rtpt_mask_time/50
    np.savetxt('Computation/Composition/RTPT_cloud.txt', [rtpt_recover_time,rtpt_mask_time])
    np.savetxt('Computation/Composition/FPTD_cloud.txt', [fptd_decryption_time,fptd_recover_time,fptd_mask_time])
    plt.bar([1,2],[fptd_mask_time,rtpt_mask_time],label='mask time',fc='r')
    plt.bar([1,2],[fptd_recover_time,rtpt_recover_time],label='recover time',fc='blue')
    plt.show()
if __name__=='__main__':
    # varying_workers()
    varying_fog()
    # varying_drop_rate()
    # varying_objects()
    # cloud_composition()