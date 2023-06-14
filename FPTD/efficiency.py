import numpy as np
from Crypto.PublicKey import ECC
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
import shamir
import time
import math
from random import randint

# A worker needs to nk-1 KA+nk secret share+encrypts and decrypts+creating
# masks


def KA_efficiency(nk):
    # receiving keys
    # one key is 448 bits
    k1_list = []
    for i in range(nk - 1):
        k1_list.append(ECC.generate(curve='P-256'))
    k2_list = []
    shared_key = []
    # call to KA.agree
    start = time.time()
    for i in range(nk - 1):
        temp_key = ECC.generate(curve='P-256')
        k2_list.append(temp_key)
        shared_key.append(k1_list[i].pointQ * temp_key.d)
    end = time.time()
    print()
    return end - start


def share_efficiency(nk, t):
    # a secret is 32 bits
    max = 2 ** 31 - 1
    r = randint(0,2**32)
    s = randint(0,2**32)
    start = time.time()
    shamir.make_random_shares(t,nk-1,r,max)
    shamir.make_random_shares(t,nk-1,s,max)
    end = time.time()
    return end - start


def recover_efficiency(nk, t):
    max = 2 ** 31 - 1
    r = list(range(nk - 1))
    rs = []
    for i in range(nk - 1):
        rs.append(shamir.make_random_shares(t, nk - 1, r[i], max))
    start = time.time()
    for i in range(nk - 1):
        shamir.recover_secret(rs[i][:t], max)
    end = time.time()
    return end - start


def encrypt_and_decrypt_efficiency(nk):
    # set symmetric key as 128 bits
    sk = get_random_bytes(16)
    header = b'header'
    start = time.time()
    for i in range(nk - 1):
        plaintext = get_random_bytes(128)
        cipher = AES.new(sk, AES.MODE_GCM)
        cipher.update(header)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)

        nonce = cipher.nonce

        cipher = AES.new(sk, AES.MODE_GCM, nonce=nonce)
        cipher.update(header)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    end = time.time()

    return end-start


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


def worker_efficiency(nk, t,drop_rate):
    time_sum=0
    for i in range(10):
        time_sum=(KA_efficiency(nk) +
            share_efficiency(nk, t) +
            encrypt_and_decrypt_efficiency(nk) +
            creating_mask_r(M)*(1-drop_rate)+creating_mask_s(nk,M)*(1-drop_rate)) * 2
    return time_sum/10

def fog_efficiency(nk,t,M,drop_rate):

    time_sum=0
    for i in range(10):
        # recover secrets
        time_sum+=recover_efficiency(nk,t)
        # drop users' recovery of KA
        time_sum+=KA_efficiency(math.ceil(nk*drop_rate))
        # re-generate alive users' random mask
        time_sum+=creating_mask_r(M)*(1-drop_rate)*nk
        # re-generate drop users' zero-sum mask
        time_sum+=creating_mask_s(math.ceil(nk*drop_rate),M)*math.ceil(nk*drop_rate)
    return time_sum/10
def worker_communication(nk,drop_rate,M):
    ka=(32+512)*nk
    encrypt=(32+32+128+32+16*8)*(nk-1)
    masked_data=M*32
    secrets=32*math.ceil((nk-1)*(1-drop_rate))+256*math.floor((nk-1)*drop_rate)
    res=(ka+encrypt+masked_data+secrets)*2+M*32
    return res

if __name__ == '__main__':
    t_rate = 0.75
    M = 50
    K = 10
    drop_rate=0.1

    computation={}
    computation['rtpt worker']=[]
    computation['fptd worker']=[]
    computation['fptd fog']=[]
    computation['rtpt server']=[]
    computation['fptd server']=[]

    for N in [20 * 5, 40 * 5, 60 * 5, 80 * 5, 100 * 5]:
        nk = N // K
        t = math.ceil(t_rate * nk)
        computation['fptd worker'].append(worker_efficiency(nk, t,drop_rate))
        computation['rtpt worker'].append(worker_efficiency(N, math.floor(t_rate * N),drop_rate))
        computation['fptd fog'].append(fog_efficiency(nk,t,M,drop_rate))
        computation['rtpt server'].append(fog_efficiency(N,math.floor(t_rate * N),M,drop_rate))

    np.savetxt('Computation/fptd worker.txt', computation['fptd worker'])
    np.savetxt('Computation/fptd fog.txt', computation['fptd fog'])
    np.savetxt('Computation/rtpt worker.txt',computation['rtpt worker'])
    np.savetxt('Computation/rtpt server.txt',computation['rtpt server'])