#!/usr/bin/python3

# Author: https://github.com/liu246542

from phe import paillier
import random, scipy.stats
import numpy as np

class SimWorkers(object):
  """docstring for SimWorkers"""
  def __init__(self, K, M, S, GT):
    super(SimWorkers, self).__init__()
    self.K = K
    self.M = M
    self.XM = np.zeros([K, M])
    self.PHI = np.zeros([K, M])
    self.SPL = [1] * S + [0] * (10 - S)
    for k in range(K):
      self.PHI[k] = [random.choice(self.SPL) for m in range(M)]
    def genPHI():
      for k in range(K):
        self.PHI[k] = [random.choice(self.SPL) for m in range(M)]
      if np.prod(np.sum(self.PHI, axis = 0)) > 0 and np.prod(np.sum(self.PHI, axis = 1)) > 0:
        return
      else:
        genPHI()
    genPHI()
    assert np.prod(np.sum(self.PHI, axis = 0)) > 0 and np.prod(np.sum(self.PHI, axis = 1)) > 0
    # for i,j in zip(np.sum(self.PHI, axis = 0), np.sum(self.PHI, axis = 1)):
      # assert np.prod(i) > 0 and np.prod(j) > 0
    for k in range(K):
      for m in range(M):
        # self.XM[k][m] = self.PHI[k][m] * round((random.random() * 10), 2) # 随机在 [0,10) 之间取值，此处可以自行修改
        self.XM[k][m] = self.PHI[k][m] * np.random.normal(loc = GT[m], scale = 2)

  def ss(self):
    Y = np.array([scipy.stats.chi2.ppf(0.05, k) for k in np.sum(self.PHI, axis = 1)])
    tphi = self.PHI / np.tile(Y, self.M).reshape(self.M, self.K).T
    tphi0 = np.random.random([self.K, self.M])
    phi0 = np.random.random([self.K, self.M])
    xm0 = np.random.random([self.K, self.M])
    tphi1 = tphi - tphi0
    phi1 = self.PHI - phi0
    xm1 = self.XM - xm0
    return [(tphi0, phi0, xm0), (tphi1, phi1, xm1)]

class CATD(object):
  """docstring for CATD"""
  def __init__(self, PHI, XM):
    super(CATD, self).__init__()
    self.PHI = PHI
    self.XM = XM
  def up_weight(self, XT):
    Y = np.array([scipy.stats.chi2.ppf(0.05, k) for k in np.sum(self.PHI, axis = 1)])
    W = Y / np.sum(self.PHI * (self.XM - XT) ** 2, axis = 1)
    return W
  def up_truth(self, W):
    XT = np.dot(W, self.XM) / np.dot(W, self.PHI)
    return XT

class S0(object):
  """docstring for S0"""
  def __init__(self, K, M, tphi0, phi0, xm0):
    super(S0, self).__init__()
    self.K = K
    self.M = M
    self.pk, self.sk = paillier.generate_paillier_keypair()
    self.tphi0 = tphi0
    self.phi0 = phi0
    self.xm0 = xm0
  def pre_up_weight(self):
    KM = self.K * self.M
    C0 = [self.pk.encrypt(m) for m in np.sum(self.tphi0 * (self.xm0 ** 2), axis = 1)]
    c_xm0 = np.array([self.pk.encrypt(m) for m in self.xm0.reshape(KM,)]).reshape(self.K, self.M)
    c_xm02 = np.array([self.pk.encrypt(m) for m in (self.xm0 ** 2).reshape(KM,)]).reshape(self.K, self.M)
    c_tphi0 = np.array([self.pk.encrypt(m) for m in self.tphi0.reshape(KM,)]).reshape(self.K, self.M)
    c_phi0 = np.array([self.pk.encrypt(m) for m in self.phi0.reshape(KM,)]).reshape(self.K, self.M)
    c_tphi0_xm0 = np.array([self.pk.encrypt(m) for m in (self.tphi0 * self.xm0).reshape(KM,)]).reshape(self.K, self.M)
    C_pack1 = (c_xm0, c_xm02, c_tphi0, c_phi0, c_tphi0_xm0)
    return [C0, C_pack1]
  def up_truth(self, C):
    tw = 1 / np.array([self.sk.decrypt(c) for c in C])
    self.tw = tw
    KM = self.K * self.M
    c_tw = np.array([self.pk.encrypt(m) for m in tw])
    c_tw_xm0 = np.array([self.pk.encrypt(m) for m in (np.tile(tw, self.M).reshape(self.M, self.K).T * self.xm0).reshape(KM,)]).reshape(self.K, self.M)
    c_tw_phi0 = np.array([self.pk.encrypt(m) for m in (np.tile(tw, self.M).reshape(self.M, self.K).T * self.phi0).reshape(KM,)]).reshape(self.K, self.M)
    C_pack2 = (c_tw, c_tw_xm0, c_tw_phi0)
    return C_pack2
  def resolve_xt(self, C5, C6):
    return [self.sk.decrypt(wx) / self.sk.decrypt(wphi) for wx, wphi in zip(C5, C6)]
  # def resolve_tw(self, C):
    # self.tw = self.sk

class S1(object):
  """docstring for S1"""
  def __init__(self, K, M, C0, C_pack1, pk, tphi1, phi1, xm1):
    super(S1, self).__init__()
    self.K = K
    self.M = M
    self.tphi1 = tphi1
    self.phi1 = phi1
    self.xm1 = xm1
    self.C0 = C0
    self.C_pack1 = C_pack1
    self.pk = pk
    self.bk = np.random.random(self.K)
  def up_weight(self, XT):
    dist = self.xm1 - XT
    C1 = np.sum(self.tphi1 * self.C_pack1[1], axis = 1)
    C2 = np.sum(np.multiply(2, dist) * (self.C_pack1[4] + self.tphi1 * self.C_pack1[0]), axis = 1)
    C3 = np.sum(dist ** 2 * self.C_pack1[2], axis = 1)
    C4 = np.array([self.pk.encrypt(m) for m in np.sum(self.tphi1 * dist ** 2, axis = 1)])
    return self.bk * (self.C0 + C1 + C2 + C3 + C4)
  def up_truth(self, C_pack2):
#     C5 = self.bk * np.sum(C_pack2[1] + np.tile(C_pack2[0], self.M).reshape(self.M, self.K).T * self.xm1, axis = 0)
    C5 = np.sum( np.tile(self.bk, self.M).reshape(self.M, self.K).T *(C_pack2[1] + np.tile(C_pack2[0], self.M).reshape(self.M, self.K).T * self.xm1), axis = 0)
    C6 = np.sum( np.tile(self.bk, self.M).reshape(self.M, self.K).T *(C_pack2[2] + np.tile(C_pack2[0], self.M).reshape(self.M, self.K).T * self.phi1), axis = 0)
    return [C5, C6]