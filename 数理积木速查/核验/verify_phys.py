"""第 6--13 章公式与数值常数的符号/数值核验。数值核验只覆盖所测参数。"""
import math, json
import numpy as np, sympy as sp
from scipy import integrate, linalg, optimize, stats, special, constants as C

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(1)
close = lambda a, b, rel=1e-3: abs(a - b) <= rel*abs(b)

# ---------- 第 6 章 ----------
r, h, k, al = sp.symbols('r h k alpha', positive=True)
U = k*r**(al + 1)/(al + 1)                      # F=-k r^alpha
Ueff = U + h**2/(2*r**2); r0 = sp.solve(sp.diff(Ueff, r), r)[0]
wr2 = sp.diff(Ueff, r, 2).subs(r, r0); wth2 = (h/r0**2)**2
check(6, "幂律力 omega_r/omega_theta = sqrt(3+alpha)", sp.simplify(wr2/wth2 - (3 + al)) == 0)
GM, r1, r2 = 1.0, 1.0, 3.7
vc1, vc2 = math.sqrt(GM/r1), math.sqrt(GM/r2); at = (r1 + r2)/2
vp = math.sqrt(GM*(2/r1 - 1/at)); va = math.sqrt(GM*(2/r2 - 1/at))
check(6, "Hohmann 两次 Δv 与转移时间", close(vp - vc1, vc1*(math.sqrt(2*r2/(r1+r2)) - 1), 1e-12) and close(vc2 - va, vc2*(1 - math.sqrt(2*r1/(r1+r2))), 1e-12)
      and close(math.pi*math.sqrt(at**3/GM), math.pi*math.sqrt((r1+r2)**3/(8*GM)), 1e-12))
bt, th, g, m_ = sp.symbols('beta theta g m', positive=True)
a_ = g*sp.sin(th)/(1 + bt); f_ = bt*m_*a_
check(6, "纯滚: 所需摩擦系数", sp.simplify(f_/(m_*g*sp.cos(th)) - bt*sp.tan(th)/(1 + bt)) == 0)
v0, mu, R0 = sp.symbols('v0 mu R', positive=True)
vf = v0/(1 + sp.Rational(2, 5))
check(6, "保龄球 5/7, 时间 2v0/(7 mu g), 损失 2/7", vf == sp.Rational(5, 7)*v0 and sp.simplify((v0 - vf)/(mu*g) - 2*v0/(7*mu*g)) == 0
      and sp.simplify(1 - vf**2*(1 + sp.Rational(2, 5))/v0**2 - sp.Rational(2, 7)) == 0)
m1, m2 = 3.0, 1.0; best = 0
for chi in np.linspace(0, np.pi, 200001):   # 质心系散射角 chi
    best = max(best, math.atan2(m2*math.sin(chi), m1 + m2*math.cos(chi)))
check(6, "弹性碰撞最大偏转角 sin=m2/m1", abs(math.sin(best) - m2/m1) < 1e-6)
Om, Rr, q = sp.symbols('Omega R q', positive=True)
Ue = -m_*Rr**2*Om**2*sp.sin(q)**2/2 - m_*g*Rr*sp.cos(q); q0 = sp.acos(g/(Om**2*Rr))
check(6, "转动圆环珠子 omega^2 = Omega^2 sin^2 theta0", sp.simplify(sp.diff(Ue, q, 2).subs(q, q0)/(m_*Rr**2) - Om**2*sp.sin(q0)**2) == 0
      and sp.simplify(sp.diff(Ue, q, 2).subs(q, 0)/(m_*Rr**2) - (g/Rr - Om**2)) == 0)
w, w0, gam = sp.symbols('omega omega0 gamma', positive=True)
check(6, "振幅峰位置 sqrt(w0^2-g^2/2)", sp.simplify(sp.solve(sp.diff((w0**2 - w**2)**2 + gam**2*w**2, w), w)[-1]**2 - (w0**2 - gam**2/2)) == 0)
d, kk = sp.symbols('d k', positive=True)
check(6, "复摆周期在 d=k 最短", sp.solve(sp.diff((kk**2 + d**2)/d, d), d) == [kk])
th0 = 0.2; Tex = 4*special.ellipk(math.sin(th0/2)**2)
check(6, "大振幅 T≈T0(1+θ0²/16)", abs(Tex/(2*math.pi) - (1 + th0**2/16)) < 1e-4)
aa, xx = sp.symbols('a x', positive=True)
y = aa*sp.cosh(xx/aa)    # T = T0 sqrt(1+y'^2) = lambda g y
check(6, "悬链线张力 T = lambda g y", sp.simplify(aa*sp.sqrt(1 + sp.diff(y, xx)**2) - y) == 0)

# ---------- 第 7 章 ----------
I1, I2, I3, W2 = 3.0, 2.0, 1.0, 1.0
Jm = np.array([[0, 0, (I2 - I3)/I1*W2], [0, 0, 0], [(I1 - I2)/I3*W2, 0, 0]])
lam_max = max(np.linalg.eigvals(Jm).real)
check(7, "中间轴不稳定增长率", abs(lam_max**2 - (I1 - I2)*(I2 - I3)/(I1*I3)*W2**2) < 1e-12)
Z0 = math.sqrt(C.mu_0/C.epsilon_0)
check(7, "短天线 2π/3 Z0 ≈ 790 Ω", abs(2*math.pi/3*Z0 - 790) < 1.5, f"{2*math.pi/3*Z0:.1f}")
xs = optimize.minimize_scalar(lambda x: -(x**2*math.exp(x)/(1 + math.exp(x))**2), bounds=(0.5, 5), method='bounded').x
check(7, "Schottky 峰 kT≈0.42Δ", abs(1/xs - 0.417) < 0.003, f"kT/Δ={1/xs:.4f}")
x4 = integrate.quad(lambda x: x**3/math.expm1(x), 0, 100)[0]; x2 = integrate.quad(lambda x: x**2/math.expm1(x), 0, 100)[0]
wien = optimize.brentq(lambda x: 5*(1 - math.exp(-x)) - x, 1, 10)
check(7, "黑体: π⁴/15、平均光子能 2.70kT、Wien 常数", close(x4, math.pi**4/15, 1e-9) and abs(x4/x2 - 2.701) < 1e-3
      and close(C.h*C.c/(wien*C.k), 2.898e-3, 1e-3))
TD = 0.01; deb = 9*TD**3*integrate.quad(lambda x: x**4*math.exp(x)/math.expm1(x)**2, 0, 1/TD)[0]
check(7, "Debye 低温 12π⁴/5 (T/Θ)^3", close(deb, 12*math.pi**4/5*TD**3, 1e-6))
a_, b_, T, Tc = sp.symbols('a b T T_c', positive=True)
Fm = -a_**2*(Tc - T)**2/(4*b_)
check(7, "Landau 比热跃变 a²Tc/(2b)", sp.simplify(-T*sp.diff(Fm, T, 2) - a_**2*T/(2*b_)) == 0)
Pv, V, nR = sp.symbols('P V nR', positive=True); Tg = Pv*V/nR
alpha = sp.diff(nR*T/Pv, T)/(nR*T/Pv); kap = -sp.diff(nR*T/Pv, Pv)/(nR*T/Pv)
check(7, "理想气体 Cp-Cv=nR, Tα=1", sp.simplify(T*(nR*T/Pv)*alpha**2/kap - nR) == 0 and sp.simplify(T*alpha - 1) == 0)
Nn = 60; ad = np.diag(np.sqrt(np.arange(1, Nn)), 1); X = (ad + ad.T)/math.sqrt(2)  # hbar=m=omega=1
X2 = X@X; X4 = X2@X2
check(7, "<x^2>, <x^4> 谐振子矩阵元", all(abs(X2[n, n] - (n + 0.5)) < 1e-10 and abs(X4[n, n] - 0.75*(2*n*n + 2*n + 1)) < 1e-9 for n in range(10)))
lam_ = 0.3; Ht = np.diag(np.arange(Nn) + 0.5) + lam_*X
check(7, "λx 微扰: 二阶 = 精确 -λ²/2", abs(np.linalg.eigvalsh(Ht)[0] - (0.5 - lam_**2/2)) < 1e-10)
bb = sp.symbols('b', positive=True); rr = sp.symbols('r', positive=True)
psi = sp.exp(-rr**2/bb**2); norm = sp.integrate(4*sp.pi*rr**2*psi**2, (rr, 0, sp.oo))
Tkin = sp.integrate(4*sp.pi*rr**2*psi*(-sp.Rational(1, 2))*(sp.diff(rr**2*sp.diff(psi, rr), rr)/rr**2), (rr, 0, sp.oo))/norm
Vpot = sp.integrate(4*sp.pi*rr**2*psi**2*(-1/rr), (rr, 0, sp.oo))/norm
Eb = sp.simplify(Tkin + Vpot); bmin = [s for s in sp.solve(sp.diff(Eb, bb), bb) if s.is_positive][0]
check(7, "Gauss 试探氢原子 -8/(3π) Ry", sp.simplify(Eb.subs(bb, bmin)/sp.Rational(-1, 2) - sp.Rational(8, 3)/sp.pi) == 0)
from sympy.physics.hydrogen import R_nl
ok = True
for n_, l_ in [(2, 1), (3, 1), (3, 2), (4, 2)]:
    Rn = R_nl(n_, l_, rr, 1); ev = lambda f: sp.integrate(Rn**2*f*rr**2, (rr, 0, sp.oo))
    ok &= sp.simplify(ev(1/rr) - sp.Rational(1, n_**2)) == 0
    ok &= sp.simplify(ev(rr) - sp.Rational(1, 2)*(3*n_**2 - l_*(l_ + 1))) == 0
    ok &= sp.simplify(ev(1/rr**2) - 1/(n_**3*(l_ + sp.Rational(1, 2)))) == 0
    ok &= sp.simplify(ev(1/rr**3) - 1/(n_**3*l_*(l_ + sp.Rational(1, 2))*(l_ + 1))) == 0
check(7, "氢原子 <1/r>,<r>,<1/r^2>,<1/r^3>", ok)
c = 1.0; vb = np.array([0.6, 0, 0]); gm = 1/math.sqrt(1 - 0.36)
E = rng.normal(size=3); B = rng.normal(size=3); vh = vb/np.linalg.norm(vb)
Ep = np.dot(E, vh)*vh + gm*((E + np.cross(vb, B)) - np.dot(E + np.cross(vb, B), vh)*vh)
Bp = np.dot(B, vh)*vh + gm*((B - np.cross(vb, E)) - np.dot(B - np.cross(vb, E), vh)*vh)
check(7, "场变换不变量 E²-c²B², E·B", abs((Ep@Ep - Bp@Bp) - (E@E - B@B)) < 1e-12 and abs(Ep@Bp - E@B) < 1e-12)
jv, lv, sv = 1.5, 1, 0.5
check(7, "Landé g (p3/2 = 4/3)", abs(1 + (jv*(jv+1) + sv*(sv+1) - lv*(lv+1))/(2*jv*(jv+1)) - 4/3) < 1e-12)

# ---------- 第 8 章 ----------
Rs, dq = 1.0, 2.5; qi, bi = -Rs/dq, Rs**2/dq
pts = [np.array([math.cos(t), math.sin(t)]) for t in np.linspace(0, 2*math.pi, 50)]
check(8, "接地球镜像电荷使球面电势为零", max(abs(1/np.linalg.norm(p - [dq, 0]) + qi/np.linalg.norm(p - [bi, 0])) for p in pts) < 1e-12)
rho, dd = sp.symbols('rho d', positive=True)
check(8, "平面感应电荷总量 -q", sp.simplify(sp.integrate(-dd/(2*sp.pi*(rho**2 + dd**2)**sp.Rational(3, 2))*2*sp.pi*rho, (rho, 0, sp.oo)) + 1) == 0)
er, E0, A, Ei = sp.symbols('epsilon_r E_0 A E_in')
sol = sp.solve([-E0*1 + A/1 + Ei*1, er*Ei - (E0 + 2*A)], [A, Ei], dict=True)[0]   # R=1: V 连续, D_r 连续
check(8, "介质球内场 3/(εr+2) E0", sp.simplify(sol[Ei] - 3*E0/(er + 2)) == 0)
z, Rl = sp.symbols('z R', positive=True)
Bz = lambda zz: Rl**2/(Rl**2 + zz**2)**sp.Rational(3, 2)/2      # mu0 I = 1
Btot = Bz(z - Rl/2) + Bz(z + Rl/2)
check(8, "Helmholtz: 中点二阶导为零, 系数 (4/5)^{3/2}", sp.simplify(sp.diff(Btot, z, 2).subs(z, 0)) == 0 and sp.simplify(Btot.subs(z, 0)*Rl - (sp.Rational(4, 5))**sp.Rational(3, 2)) == 0)
Rinf = sp.symbols('Rinf', positive=True)
check(8, "无限梯形网 (1+√5)/2 R", sp.solve(Rinf - 1 - Rinf/(1 + Rinf), Rinf) == [(1 + sp.sqrt(5))/2])
import itertools
Vt = list(itertools.product([0, 1], repeat=3)); Lp = np.zeros((8, 8))
for i, p in enumerate(Vt):
    for j, q_ in enumerate(Vt):
        if sum(abs(a - b) for a, b in zip(p, q_)) == 1: Lp[i, j] = -1; Lp[i, i] += 1
Lpi = np.linalg.pinv(Lp); e = np.zeros(8); e[0], e[7] = 1, -1
check(8, "立方体对顶点 5/6 R", abs(e@Lpi@e - 5/6) < 1e-12)
Ng = 401; c0 = Ng//2
import scipy.sparse as ssp, scipy.sparse.linalg as sla
Lg = ssp.lil_matrix((Ng*Ng, Ng*Ng)); idx = lambda i, j: i*Ng + j
for i in range(Ng):
    for j in range(Ng):
        for di, dj in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            ii, jj = i + di, j + dj
            if 0 <= ii < Ng and 0 <= jj < Ng: Lg[idx(i, j), idx(ii, jj)] = -1; Lg[idx(i, j), idx(i, j)] += 1
Lg[0, :] = 0; Lg[0, 0] = 1
bvec = np.zeros(Ng*Ng); bvec[idx(c0, c0)] = 1; bvec[idx(c0, c0 + 1)] = -1
vsol = sla.spsolve(Lg.tocsr(), bvec)
check(8, "无限方格相邻节点 R/2 (401² 网格)", abs(vsol[idx(c0, c0)] - vsol[idx(c0, c0 + 1)] - 0.5) < 1e-3, f"{vsol[idx(c0, c0)] - vsol[idx(c0, c0+1)]:.5f}")
dCu = lambda f: math.sqrt(2/(C.mu_0*5.96e7*2*math.pi*f))
check(8, "铜趋肤深度 60 Hz≈8.4 mm, 1 MHz≈65 μm", abs(dCu(60) - 8.4e-3) < 0.1e-3 and abs(dCu(1e6) - 65e-6) < 1.5e-6)
Rres, Lres, Cres = 50.0, 1e-3, 1e-9
check(8, "充电电阻耗散 CV²/2 与 R 无关", abs(integrate.quad(lambda t: (1/Rres)**2*math.exp(-2*t/(Rres*Cres))*Rres, 0, 50*Rres*Cres)[0] - Cres/2) < 1e-6*Cres)

# ---------- 第 9 章 ----------
check(9, "反质子阈能 7 m_p", (16 - 2)/2 == 7)
Mpi, Mmu = 139.57039, 105.6583755
pmu = (Mpi**2 - Mmu**2)/(2*Mpi)
check(9, "π→μν: p≈29.8, T≈4.1 MeV", abs(pmu - 29.79) < 0.01 and abs(math.hypot(pmu, Mmu) - Mmu - 4.12) < 0.01)
Eg, me = sp.symbols('E m_e', positive=True)
Ep_ = Eg/(1 + Eg/me*2)
check(9, "Compton 边 2E²/(mc²+2E)", sp.simplify(Eg - Ep_ - 2*Eg**2/(me + 2*Eg)) == 0)
check(9, "Rindler c²/g ≈ 0.97 ly", abs(C.c**2/9.8/C.light_year - 0.97) < 0.01)
nq, jq, a2 = sp.symbols('n j alpha2', positive=True)
kq = jq + sp.Rational(1, 2); Edirac = (1 + a2/(nq - kq + sp.sqrt(kq**2 - a2))**2)**sp.Rational(-1, 2) - 1
ser = sp.series(Edirac, a2, 0, 3).removeO()
tgt = (-a2/(2*nq**2))*(1 + a2/nq**2*(nq/kq - sp.Rational(3, 4)))
rel = [abs(float(((Edirac - tgt)/Edirac).subs({nq: nv, jq: jv, a2: C.alpha**2}))) for nv, jv in [(1, .5), (2, .5), (2, 1.5), (3, 2.5)]]
check(9, "精细结构 = Dirac 公式 α⁴ 阶展开 (残差 ~α⁴ 相对)", max(rel) < C.alpha**4, f"max rel {max(rel):.1e}")
Ry = C.Rydberg*C.h*C.c/C.e
hf = 8/3*5.5857*C.m_e/C.m_p*C.alpha**2*Ry
check(9, "超精细 ≈ 5.9 μeV, 1420 MHz", abs(hf - 5.87e-6) < 0.05e-6 and abs(hf*C.e/C.h/1e6 - 1420) < 10, f"{hf*1e6:.3f} μeV")
l1, l2, tt = sp.symbols('lambda1 lambda2 t', positive=True)
N2 = l1/(l2 - l1)*(sp.exp(-l1*tt) - sp.exp(-l2*tt))
check(9, "Bateman t_max", all(abs(float(sp.diff(N2, tt).subs(tt, sp.log(l2/l1)/(l2 - l1)).subs({l1: a, l2: b}))) < 1e-14 for a, b in [(0.3, 1.1), (2, 0.5), (0.01, 0.2)]))
dR, thR = sp.symbols('d theta', positive=True); bR = dR/2*sp.cot(thR/2)
check(9, "Rutherford: b(θ) → dσ/dΩ", sp.simplify(bR/sp.sin(thR)*sp.Abs(sp.diff(bR, thR)) - (dR/4)**2/sp.sin(thR/2)**4) == 0)
lam_e = lambda V: C.h/math.sqrt(2*C.m_e*C.e*V*(1 + C.e*V/(2*C.m_e*C.c**2)))
check(9, "电子波长 1.226/√V nm, 10 kV 修正≈0.5%", abs(C.h/math.sqrt(2*C.m_e*C.e*1)*1e9 - 1.226) < 1e-3 and abs(1 - lam_e(1e4)/(C.h/math.sqrt(2*C.m_e*C.e*1e4)) - 0.0049) < 2e-4)
check(9, "热中子 25 meV → 0.18 nm", abs(C.h/math.sqrt(2*C.m_n*0.025*C.e)*1e9 - 0.18) < 0.005)
check(9, "hc=1240 eV nm, ħc=197.3 MeV fm", abs(C.h*C.c/C.e*1e9 - 1239.84) < 0.01 and abs(C.hbar*C.c/C.e/1e6*1e15 - 197.33) < 0.01)
GMs = 1.32712440018e20; Rsun = 6.957e8
check(9, "光偏折 1.75″", abs(4*GMs/(C.c**2*Rsun)*206264.806 - 1.75) < 0.01)
aM, eM, TM = 5.7909e10, 0.2056, 87.969
check(9, "水星进动 43″/世纪", abs(6*math.pi*GMs/(C.c**2*aM*(1 - eM**2))*206264.806*36525/TM - 43.0) < 0.3)
GMe, Re, rg = 3.986004418e14, 6.371e6, 2.6561e7
sr = -0.5*(GMe/rg)/C.c**2*86400e6; gr = (GMe/Re - GMe/rg)/C.c**2*86400e6
check(9, "GPS: -7, +45, 净 +38 μs/天", abs(sr + 7.2) < 0.3 and abs(gr - 45.7) < 0.5 and abs(sr + gr - 38.5) < 0.6, f"SR {sr:.1f}, GR {gr:.1f}")

# ---------- 第 10 章 ----------
n1, n2 = 1.0, 1.5; thB = math.atan(n2/n1); thT = math.asin(n1*math.sin(thB)/n2)
rp = (n2*math.cos(thB) - n1*math.cos(thT))/(n2*math.cos(thB) + n1*math.cos(thT))
check(10, "Brewster r_p=0, 正入射 4%", abs(rp) < 1e-14 and abs(((n1 - n2)/(n1 + n2))**2 - 0.04) < 1e-12)
check(10, "F-P 精细度 R=0.99 ≈ 313", abs(math.pi*math.sqrt(0.99)/0.01 - 312.6) < 0.1)
zR, zz, lam = sp.symbols('z_R z lambda', positive=True)
qb = zz + sp.I*zR; inv = sp.simplify(1/qb)
Rz = zz*(1 + (zR/zz)**2); wz2 = (lam*zR/sp.pi)*(1 + (zz/zR)**2)
check(10, "Gauss 光束 1/q = 1/R - iλ/(πw²)", sp.simplify(sp.re(inv) - 1/Rz) == 0 and sp.simplify(sp.im(inv) + lam/(sp.pi*wz2)) == 0)
tq, ph = 0.37, 0.9
Rm = lambda a: np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
HWP = Rm(tq)@np.diag([1, -1])@Rm(-tq); out = HWP@np.array([math.cos(ph), math.sin(ph)])
check(10, "半波片: φ → 2θ-φ", abs(math.atan2(out[1], out[0]) - (2*tq - ph)) < 1e-12)
wS, nS = sp.symbols('omega', positive=True), sp.Function('n')
lamS = sp.symbols('lambda', positive=True); cS = sp.symbols('c', positive=True)
nl = sp.Function('N')(lamS)            # n(λ), λ = 2πc/ω
k_of_w = (wS/cS)*nl.subs(lamS, 2*sp.pi*cS/wS)
vg = 1/sp.diff(k_of_w, wS)
vg_l = (cS/(nl - lamS*sp.diff(nl, lamS))).subs(lamS, 2*sp.pi*cS/wS)
check(10, "群速度 ω 形式与 λ 形式一致", sp.simplify(vg - vg_l) == 0)
Z1, Z2 = sp.symbols('Z1 Z2', positive=True)
rS = (Z1 - Z2)/(Z1 + Z2); tS = 2*Z1/(Z1 + Z2)
check(10, "阻抗失配 R+T=1", sp.simplify(rS**2 + Z2/Z1*tS**2 - 1) == 0)
check(10, "等离子体 f_p≈9√n Hz", abs(math.sqrt(C.e**2/(C.epsilon_0*C.m_e))/(2*math.pi) - 8.98) < 0.01)
check(10, "偏振片极限 cos^{2N}(π/2N) → 1", abs(math.cos(math.pi/2000)**2000 - math.exp(-math.pi**2/4000)) < 1e-6)

# ---------- 第 11 章 ----------
check(11, "μB/h=14.0 GHz/T, γp/2π=42.58 MHz/T, ge μB/h=28.0 GHz/T", abs(C.physical_constants['Bohr magneton in Hz/T'][0]/1e9 - 14.0) < 0.01
      and abs(C.physical_constants['proton gyromag. ratio in MHz/T'][0] - 42.58) < 0.01 and abs(C.physical_constants['electron gyromag. ratio in MHz/T'][0]/1e3 - 28.02) < 0.01)
check(11, "Johnson 300 K 1 kΩ: 4.07 nV/√Hz", abs(math.sqrt(4*C.k*300*1e3)*1e9 - 4.07) < 0.01)
eta, a_m, rho_o, v1, v2, Ef, gg = sp.symbols('eta a rho v1 v2 E g', positive=True)
asol = sp.sqrt(9*eta*v1/(2*rho_o*gg)); mg = sp.Rational(4, 3)*sp.pi*asol**3*rho_o*gg
check(11, "Millikan: 6πηa v1 = mg, q = 6πηa(v1+v2)/E", sp.simplify(6*sp.pi*eta*asol*v1 - mg) == 0)
tt_ = np.linspace(0, 2*np.pi, 100001); phi_ = 0.7
check(11, "锁相 X = ½VsVr cosφ", abs(np.mean(np.sin(tt_ + phi_)*np.sin(tt_)) - 0.5*math.cos(phi_)) < 1e-4)
tau = 1.0; enbw = integrate.quad(lambda f: 1/(1 + (2*math.pi*f*tau)**2), 0, np.inf)[0]
check(11, "一阶 RC 等效噪声带宽 1/(4τ)", abs(enbw - 0.25) < 1e-10)
check(11, "van der Pauw 对称 R_s=πR/ln2", abs(2*math.exp(-math.pi*1/(math.pi/math.log(2))) - 1) < 1e-12)

# ---------- 第 12 章 ----------
xd = np.linspace(0, 9, 10); sg = 0.2 + 0.05*xd; yd = 1.3 + 0.7*xd + rng.normal(0, sg)
wgt = 1/sg**2; S, Sx, Sxx, Sy, Sxy = wgt.sum(), (wgt*xd).sum(), (wgt*xd**2).sum(), (wgt*yd).sum(), (wgt*xd*yd).sum()
D_ = S*Sxx - Sx**2; Xd = np.stack([np.ones_like(xd), xd], 1); Cov = np.linalg.inv(Xd.T@np.diag(wgt)@Xd)
beta = Cov@Xd.T@np.diag(wgt)@yd
check(12, "加权直线拟合闭式解与协方差", np.allclose(beta, [(Sxx*Sy - Sx*Sxy)/D_, (S*Sxy - Sx*Sy)/D_]) and np.allclose(Cov, [[Sxx/D_, -Sx/D_], [-Sx/D_, S/D_]]))
check(12, "Δχ²: 2.30 (68.3%), 6.18 (95.4%), 5.99 (95%)", abs(stats.chi2.ppf(0.6827, 2) - 2.30) < 0.01 and abs(stats.chi2.ppf(0.9545, 2) - 6.18) < 0.01 and abs(stats.chi2.ppf(0.95, 2) - 5.99) < 0.01)
check(12, "t_4=2.78, t_9=2.26", abs(stats.t.ppf(0.975, 4) - 2.776) < 1e-3 and abs(stats.t.ppf(0.975, 9) - 2.262) < 1e-3)
sims = rng.normal(size=(200000, 10)).std(axis=1, ddof=1)
check(12, "σ_s/σ ≈ 1/√(2(n-1)) (n=10)", abs(sims.std() - 1/math.sqrt(18)) < 0.01, f"MC {sims.std():.4f} vs {1/math.sqrt(18):.4f}")
Rsb, Rb, Ttot = 9.0, 1.0, 1.0
ts = optimize.minimize_scalar(lambda s: Rsb/s + Rb/(Ttot - s), bounds=(0.01, 0.99), method='bounded').x
check(12, "最优时间分配 √(R_{s+b}/R_b)", abs(ts/(Ttot - ts) - 3.0) < 1e-3)
ntrue1, ntrue2, tau_d = 2e4, 3e4, 2e-6; obs = lambda n: n/(1 + n*tau_d)
m1o, m2o, m12o = obs(ntrue1), obs(ntrue2), obs(ntrue1 + ntrue2)
check(12, "双源法死时间一阶近似 (误差 <15%)", abs((m1o + m2o - m12o)/(2*m1o*m2o)/tau_d - 1) < 0.15)
data = rng.normal(size=25); jk = np.array([np.delete(data, i).mean() for i in range(25)])
check(12, "Jackknife 对均值给出 s²/n", abs((24/25)*np.sum((jk - jk.mean())**2) - data.var(ddof=1)/25) < 1e-12)

# ---------- 第 13 章 ----------
f, fc, kT, gm_ = sp.symbols('f f_c kT gamma', positive=True)
Sx = kT/(sp.pi**2*gm_*(f**2 + fc**2))
check(13, "光镊谱积分 = kT/κ", sp.simplify(sp.integrate(Sx, (f, 0, sp.oo)) - kT/(2*sp.pi*gm_*fc)) == 0)
tq_, m__ = sp.symbols('t m', positive=True)
check(13, "Green-Kubo D = kT/(mγ)", sp.simplify(sp.integrate(kT/m__*sp.exp(-gm_*tq_), (tq_, 0, sp.oo)) - kT/(m__*gm_)) == 0)
qq, muY, rY = sp.symbols('q mu r', positive=True)
FT = sp.integrate(4*sp.pi*rY**2*sp.sin(qq*rY)/(qq*rY)*sp.exp(-muY*rY)/rY, (rY, 0, sp.oo))
check(13, "Yukawa Fourier 变换 4π/(q²+μ²)", sp.simplify(FT - 4*sp.pi/(qq**2 + muY**2)) == 0)
w0k, gk, wk = 1.0, 0.3, 0.6
chi = lambda w: 1/(w0k**2 - w**2 - 1j*gk*w)
pv = integrate.quad(lambda wp: wp*chi(wp).imag/(wp + wk), 0, 200, weight='cauchy', wvar=wk, limit=500)[0]
check(13, "Kramers-Kronig (Lorentz 振子)", abs(2/np.pi*pv - chi(wk).real) < 2e-3, f"{2/np.pi*pv:.5f} vs {chi(wk).real:.5f}")
Dl, Vc, tR = 0.8, 0.5, 2.3
U2 = linalg.expm(-1j*np.array([[Dl/2, Vc], [Vc, -Dl/2]])*tR)
Om_ = math.sqrt(Vc**2 + Dl**2/4)
check(13, "Rabi 公式", abs(abs(U2[1, 0])**2 - Vc**2/Om_**2*math.sin(Om_*tR)**2) < 1e-12)
from scipy.integrate import solve_ivp
vLZ, VLZ = 4.0, 0.6
def rhs(t, y):
    c = y[:2] + 1j*y[2:]; H = np.array([[vLZ*t/2, VLZ], [VLZ, -vLZ*t/2]]); d = -1j*H@c
    return np.concatenate([d.real, d.imag])
sl = solve_ivp(rhs, [-60, 60], [1, 0, 0, 0], rtol=1e-10, atol=1e-12)
Pd = sl.y[0, -1]**2 + sl.y[2, -1]**2
check(13, "Landau-Zener exp(-2πV²/(ħ|dΔ/dt|))", abs(Pd - math.exp(-2*math.pi*VLZ**2/vLZ)) < 5e-3, f"{Pd:.4f} vs {math.exp(-2*math.pi*VLZ**2/vLZ):.4f}")
check(13, "Lorenz 数 2.44e-8", abs(math.pi**2/3*(C.k/C.e)**2 - 2.443e-8) < 0.002e-8)
kk_, ta, ah = sp.symbols('k t a', positive=True)
Ek = -2*ta*sp.cos(kk_*ah)
check(13, "紧束缚带底有效质量 ħ²/(2ta²)", sp.simplify(ah**0*sp.Symbol('hbar')**2/sp.diff(Ek, kk_, 2).subs(kk_, 0) - sp.Symbol('hbar')**2/(2*ta*ah**2)) == 0)
wh = 0.3; Me = np.array([[1, wh], [-wh, 1]])   # 前向 Euler 作用于 (ωx, v)
check(13, "前向 Euler 能量因子 1+ω²h²", abs(abs(np.linalg.eigvals(Me)[0])**2 - (1 + wh**2)) < 1e-12)
ok = True
for wh in [1.9, 2.1]:
    Mv = np.array([[2 - wh**2, -1], [1, 0]]); ok &= (max(abs(np.linalg.eigvals(Mv))) <= 1 + 1e-12) == (wh < 2)
check(13, "Verlet 稳定条件 ωh<2", ok)
check(13, "Gauss 时间带宽积 0.441 = 2ln2/π", abs(2*math.log(2)/math.pi - 0.441) < 5e-4)

npass = sum(r[2] for r in R); print(f"\n第6-13章: {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
