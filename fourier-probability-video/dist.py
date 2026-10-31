"""片中反复用到的几个分布：密度、特征函数、按分位数取的“样本”。

样本用分位数 F⁻¹((i+½)/N) 而不是随机数，这样几千个点的平均和理论值几乎一样，
画出来的重心正好落在特征函数上。
"""

import numpy as np
from scipy.special import iv, gammaln


class Mixture:
    """几个正态的混合：Σ w N(μ, σ²)。"""

    def __init__(self, w, mu, sd):
        self.w = np.asarray(w, float)
        self.mu = np.asarray(mu, float)
        self.sd = np.asarray(sd, float)

    def pdf(self, x):
        x = np.asarray(x, float)[..., None]
        return np.sum(self.w * np.exp(-0.5 * ((x - self.mu) / self.sd) ** 2) / (self.sd * np.sqrt(2 * np.pi)), -1)

    def cf(self, t):
        t = np.asarray(t, float)[..., None]
        return np.sum(self.w * np.exp(1j * t * self.mu - 0.5 * (self.sd * t) ** 2), -1)

    @property
    def mean(self):
        return float(np.sum(self.w * self.mu))

    @property
    def var(self):
        m = self.mean
        return float(np.sum(self.w * (self.sd ** 2 + self.mu ** 2)) - m * m)

    def standardized(self):
        m, s = self.mean, np.sqrt(self.var)
        return Mixture(self.w, (self.mu - m) / s, self.sd / s)

    def quantiles(self, n, lo=-8, hi=8, seed=0):
        xs = np.linspace(lo, hi, 20001)
        cdf = np.cumsum(self.pdf(xs))
        cdf /= cdf[-1]
        q = (np.arange(n) + 0.5) / n
        out = np.interp(q, cdf, xs)
        rng = np.random.default_rng(seed)
        return out[rng.permutation(n)]


# 第 1 章和片头用的“双峰”分布：均值约为 0
X1 = Mixture([0.6, 0.4], [-0.75, 1.15], [0.45, 0.38])


def vonmises_mix_coef(w, mu, kappa, kmax):
    """圆上几个 von Mises 混合的傅里叶系数 c_k = E[e^{ikΘ}]，k = 0..kmax。"""
    k = np.arange(kmax + 1)[:, None]
    w, mu, kappa = (np.asarray(v, float) for v in (w, mu, kappa))
    return np.sum(w * iv(k, kappa) / iv(0, kappa) * np.exp(1j * k * mu), -1)


def circle_density(coef, theta):
    """由 c_0..c_K 合成圆上的密度 p(θ) = (1/2π) Σ_k c_k e^{-ikθ}（负 k 取共轭）。"""
    theta = np.asarray(theta, float)
    k = np.arange(1, len(coef))
    s = np.real(np.sum(coef[1:, None] * np.exp(-1j * k[:, None] * theta[None, :]), 0)) if len(coef) > 1 else 0
    return (1 + 2 * s) / (2 * np.pi)


def gamma_std_pdf(z, n):
    """(G − n)/√n 的密度，G ~ Gamma(n, 1)；n 可以不是整数。"""
    z = np.asarray(z, float)
    x = n + np.sqrt(n) * z
    out = np.zeros_like(z)
    ok = x > 0
    out[ok] = np.exp(0.5 * np.log(n) + (n - 1) * np.log(x[ok]) - x[ok] - gammaln(n))
    return out


def gamma_std_cf(t, n):
    """同上的特征函数：(e^{-it/√n} / (1 − it/√n))^n。"""
    t = np.asarray(t, float)
    s = t / np.sqrt(n)
    return np.exp(n * (-1j * s - np.log(1 - 1j * s)))
