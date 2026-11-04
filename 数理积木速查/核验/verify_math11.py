"""第四轮续写 05i--05l 的核验。数值核验只覆盖所测参数。"""
import math, itertools, json
import numpy as np, sympy as sp, mpmath as mp
from scipy import integrate, linalg, special, signal, optimize

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(11)
close = lambda a, b, tol=1e-9: abs(a - b) <= tol*max(1, abs(b))

# ---------- 05i 张量 ----------
eps = np.zeros((3, 3, 3))
for p in itertools.permutations(range(3)):
    eps[p] = np.linalg.det(np.eye(3)[list(p)])
d = np.eye(3)
check('5i', "ε_ijk ε_imn = δδ-δδ，ε_ijkε_ijn=2δ，εε=6", np.allclose(np.einsum('ijk,imn->jkmn', eps, eps), np.einsum('jm,kn->jkmn', d, d) - np.einsum('jn,km->jkmn', d, d))
      and np.allclose(np.einsum('ijk,ijn->kn', eps, eps), 2*d) and close(np.sum(eps*eps), 6))
A = rng.normal(size=(3, 3))
check('5i', "det A=ε A1i A2j A3k，ε_lmn det A=ε A_il A_jm A_kn", close(np.einsum('ijk,i,j,k', eps, A[0], A[1], A[2]), np.linalg.det(A)) and
      np.allclose(np.einsum('ijk,il,jm,kn->lmn', eps, A, A, A), eps*np.linalg.det(A)))
Q = linalg.qr(rng.normal(size=(3, 3)))[0]
T4 = 1.3*np.einsum('ij,kl->ijkl', d, d) + 0.7*np.einsum('ik,jl->ijkl', d, d) - 0.4*np.einsum('il,jk->ijkl', d, d)
check('5i', "四阶各向同性张量在转动下不变", np.allclose(np.einsum('ai,bj,ck,dl,ijkl->abcd', Q, Q, Q, Q, T4), T4))
I1, I2, I3 = np.trace(A), 0.5*(np.trace(A)**2 - np.trace(A@A)), np.linalg.det(A)
check('5i', "主不变量与 Cayley--Hamilton", np.allclose(A@A@A - I1*A@A + I2*A - I3*np.eye(3), 0) and close(np.trace(Q@A@Q.T), I1))
S = rng.normal(size=(3, 3)); S = S + S.T; s = S - np.trace(S)/3*d; sig = np.linalg.eigvalsh(S)
vm1 = math.sqrt(1.5*np.sum(s*s)); vm2 = math.sqrt(0.5*((sig[0] - sig[1])**2 + (sig[1] - sig[2])**2 + (sig[2] - sig[0])**2))
J2 = 0.5*np.sum(s*s)
check('5i', "von Mises：√(3J₂)=√(3/2 sᵢⱼsᵢⱼ)=主应力形式；纯剪 √3τ", close(vm1, vm2) and close(vm1, math.sqrt(3*J2)) and
      close(math.sqrt(1.5*np.sum(np.array([[0, 1.0, 0], [1, 0, 0], [0, 0, 0]])**2)), math.sqrt(3)))
w = rng.normal(size=3); Aw = -np.einsum('ijk,k->ij', eps, w); vv = rng.normal(size=3)
check('5i', "反对称张量 ↔ 轴矢量：Av=ω×v，ω=-½εA", np.allclose(Aw@vv, np.cross(w, vv)) and np.allclose(-0.5*np.einsum('kij,ij->k', eps, Aw), w))
sx, sy, txy = 3.0, -1.0, 2.0
s12 = np.linalg.eigvalsh([[sx, txy], [txy, sy]])[::-1]
thp = 0.5*math.atan2(2*txy, sx - sy); n1 = np.array([math.cos(thp), math.sin(thp)])
check('5i', "Mohr 圆主应力与主方向 tan2θ", np.allclose(s12, [(sx + sy)/2 + math.hypot((sx - sy)/2, txy), (sx + sy)/2 - math.hypot((sx - sy)/2, txy)])
      and np.allclose(np.array([[sx, txy], [txy, sy]])@n1, s12[0]*n1))
x, y, z = sp.symbols('x y z')
u1, u2 = sp.sin(x*y) + x**3*y, sp.exp(x)*sp.cos(y) + y**2*x
exx, eyy, exy = sp.diff(u1, x), sp.diff(u2, y), (sp.diff(u1, y) + sp.diff(u2, x))/2
check('5i', "二维 Saint-Venant 相容方程", sp.simplify(sp.diff(exx, y, 2) + sp.diff(eyy, x, 2) - 2*sp.diff(exy, x, y)) == 0)
E_, nu = 200.0, 0.3
lam = E_*nu/((1 + nu)*(1 - 2*nu)); mu = E_/(2*(1 + nu))
eps_ = rng.normal(size=(3, 3)); eps_ = (eps_ + eps_.T)/2
sigma = lam*np.trace(eps_)*d + 2*mu*eps_
check('5i', "Lamé 常数与逆关系 ε=(1+ν)/E σ-ν/E tr σ δ，K=λ+2μ/3", np.allclose((1 + nu)/E_*sigma - nu/E_*np.trace(sigma)*d, eps_) and close(lam + 2*mu/3, E_/(3*(1 - 2*nu))))
Ev, Bv, c = rng.normal(size=3), rng.normal(size=3), 1.0
F = np.zeros((4, 4))
F[0, 1:] = -Ev/c; F[1:, 0] = Ev/c
F[1:, 1:] = -np.einsum('ijk,k->ij', eps, Bv)
g = np.diag([1, -1, -1, -1]); Fl = g@F@g
eps4 = np.zeros((4, 4, 4, 4))
for p in itertools.permutations(range(4)):
    eps4[p] = np.linalg.det(np.eye(4)[list(p)])
Fd = 0.5*np.einsum('abcd,cd->ab', eps4, Fl)
check('5i', "F_μνF^μν=2(B²-E²/c²)，F_μνF̃^μν=-(4/c)E·B（ε^0123=+1）", close(np.sum(Fl*F), 2*(Bv@Bv - Ev@Ev/c**2)) and close(np.sum(Fl*Fd), -4/c*Ev@Bv))
Tem = F@g@F + 0.25*g*np.sum(Fl*F)     # T^{μν}=F^{μα}F_α^ν+¼g^{μν}F²（μ0=c=1）
check('5i', "电磁能动张量无迹，T⁰⁰=u", close(np.trace(g@Tem), 0, 1e-9) and close(Tem[0, 0], 0.5*(Ev@Ev + Bv@Bv), 1e-9))
def riem_count(n):
    idx = list(itertools.product(range(n), repeat=4)); pos = {t: i for i, t in enumerate(idx)}; rows = []
    def row(pairs):
        r = np.zeros(len(idx))
        for coef, t in pairs: r[pos[t]] += coef
        return r
    for a, b, c_, d_ in idx:
        rows += [row([(1, (a, b, c_, d_)), (1, (b, a, c_, d_))]), row([(1, (a, b, c_, d_)), (1, (a, b, d_, c_))]),
                 row([(1, (a, b, c_, d_)), (-1, (c_, d_, a, b))]), row([(1, (a, b, c_, d_)), (1, (a, c_, d_, b)), (1, (a, d_, b, c_))])]
    return len(idx) - np.linalg.matrix_rank(np.array(rows))
check('5i', "Riemann 张量独立分量 n²(n²-1)/12：1,6,20", [riem_count(n) for n in (2, 3, 4)] == [1, 6, 20])
th = 0.37; Rm = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
Tt = np.array([[2.0, 0.7], [0.7, -1.0]]); Tp = Rm.T@Tt@Rm
check('5i', "二维对称张量转动依赖 2θ", close(Tp[0, 0], (Tt[0, 0] + Tt[1, 1])/2 + (Tt[0, 0] - Tt[1, 1])/2*math.cos(2*th) + Tt[0, 1]*math.sin(2*th)) and
      close(Tp[0, 1], -(Tt[0, 0] - Tt[1, 1])/2*math.sin(2*th) + Tt[0, 1]*math.cos(2*th)))
T9 = rng.normal(size=(3, 3)); tr0 = np.trace(T9)/3*d; anti = (T9 - T9.T)/2; stl = (T9 + T9.T)/2 - tr0
check('5i', "二阶张量 9=1⊕3⊕5 分解", np.allclose(tr0 + anti + stl, T9) and close(np.trace(stl), 0) and np.linalg.matrix_rank(np.array([m.ravel() for m in [np.eye(3)]])) == 1)

# ---------- 05j Fokker--Planck ----------
xs, kT, gam = sp.symbols('x kT gamma', positive=True)
V = xs**4/4 - xs**2
Aa, Bb = -sp.diff(V, xs)/gam, 2*kT/gam
ps = 1/Bb*sp.exp(sp.integrate(2*Aa/Bb, xs))
check('5j', "零流稳态 → Boltzmann e^{-V/kT}", sp.simplify(ps*sp.exp(V/kT)).free_symbols <= {gam, kT} and sp.simplify(-sp.diff(Aa*ps, xs) + sp.diff(Bb*ps, xs, 2)/2) == 0)
bs_, dt, Np, Tn = 0.5, 1e-3, 200000, 1.0
X = np.ones(Np)
for _ in range(int(Tn/dt)):
    dW = rng.normal(size=Np)*math.sqrt(dt)
    Xp = X + bs_*X*dW; X = X + 0.5*bs_*(X + Xp)*dW     # Heun = Stratonovich
check('5j', "Stratonovich dX=bX∘dW ⇔ Itô 漂移 ½b²X（E X_T=e^{b²T/2}）", abs(X.mean() - math.exp(bs_**2*Tn/2)) < 0.01)
a_, b_, D_, x0 = sp.symbols('a b D x0', real=True)
Tf = (b_ - xs)*(b_ + xs - 2*a_)/(2*D_)
check('5j', "无势平均首达时间 (b-x)(b+x-2a)/2D", sp.simplify(D_*sp.diff(Tf, xs, 2) + 1) == 0 and sp.simplify(sp.diff(Tf, xs).subs(xs, a_)) == 0 and sp.simplify(Tf.subs(xs, b_)) == 0)
Vb = lambda y: 0.5*y*y
Tgen = lambda xx_, aa, bb, Dd, beta: integrate.quad(lambda yy: math.exp(beta*Vb(yy))*integrate.quad(lambda zz: math.exp(-beta*Vb(zz)), aa, yy)[0], xx_, bb)[0]/Dd
hh = 1e-3; aa, bb, Dd, beta = -1.0, 1.5, 0.7, 2.0; xx0 = 0.2
d2 = (Tgen(xx0 + hh, aa, bb, Dd, beta) - 2*Tgen(xx0, aa, bb, Dd, beta) + Tgen(xx0 - hh, aa, bb, Dd, beta))/hh**2
d1 = (Tgen(xx0 + hh, aa, bb, Dd, beta) - Tgen(xx0 - hh, aa, bb, Dd, beta))/(2*hh)
check('5j', "平均首达时间公式满足后向方程 L†T=-1", abs(Dd*d2 - Dd*beta*xx0*d1 + 1) < 1e-4)
vv_ = sp.symbols('v', positive=True)
pib = (1 - sp.exp(-vv_*(xs - a_)/D_))/(1 - sp.exp(-vv_*(b_ - a_)/D_))
check('5j', "有漂移的分流概率", sp.simplify(vv_*sp.diff(pib, xs) + D_*sp.diff(pib, xs, 2)) == 0 and sp.simplify(pib.subs(xs, a_)) == 0 and sp.simplify(pib.subs(xs, b_) - 1) == 0)
def gillespie(k, g, burst, T_end, n_paths=2000):
    out = []
    for _ in range(n_paths):
        t = 0.0; n = 0
        while True:
            a1, a2 = k, g*n; a0 = a1 + a2
            t += rng.exponential(1/a0)
            if t > T_end: break
            if rng.random()*a0 < a1: n += (rng.geometric(1/(1 + burst)) - 1) if burst else 1
            else: n -= 1
        out.append(n)
    return np.array(out)
nb = gillespie(10.0, 1.0, 0, 8.0)
check('5j', "Gillespie：恒定产生/降解的稳态 Poisson（Fano=1）", abs(nb.mean() - 10) < 0.3 and abs(nb.var()/nb.mean() - 1) < 0.1)
nbb = gillespie(2.0, 1.0, 4.0, 10.0)
check('5j', "爆发式产生：Fano=1+b", abs(nbb.mean() - 8) < 0.4 and abs(nbb.var()/nbb.mean() - 5) < 0.5, f"Fano={nbb.var()/nbb.mean():.2f}")
mW, sW, be = 3.0, 1.2, 1.5
Ws = rng.normal(mW, sW, 2000000); dF = mW - be*sW**2/2
check('5j', "Jarzynski（Gauss 功分布）⟨e^{-βW}⟩=e^{-βΔF}，⟨W⟩≥ΔF", abs(np.mean(np.exp(-be*Ws))/math.exp(-be*dF) - 1) < 0.02 and mW >= dF)
Wsym = sp.symbols('W', real=True); mws, sws, bes = sp.symbols('m s beta', positive=True)
dFs = mws - bes*sws**2/2
PF = sp.exp(-(Wsym - mws)**2/(2*sws**2)); PR = sp.exp(-(-Wsym - (-(mws - bes*sws**2)))**2/(2*sws**2))
check('5j', "Crooks 关系（Gauss 情形）", sp.simplify(sp.log(PF/PR) - bes*(Wsym - dFs)) == 0)
f_ = np.logspace(-1, 1, 5); l1, l2 = 1e-7, 1e7
S1f = [integrate.quad(lambda lnl: math.exp(lnl)/(math.exp(2*lnl) + (math.pi*ff)**2), math.log(l1), math.log(l2), limit=400, points=[math.log(math.pi*ff)])[0] for ff in f_]
check('5j', "对数均匀速率的 Lorentz 叠加 ∝ 1/f", np.allclose(np.array(S1f)*f_, S1f[2]*f_[2], rtol=1e-3))
kk, gg = 10.0, 1.0
check('5j', "线性噪声近似：生灭过程 JC+CJᵀ+D=0 给 C=k/γ", close(linalg.solve_continuous_lyapunov(np.array([[-gg]]), -np.array([[2*kk]]))[0, 0], kk/gg))
m, v = sp.symbols('m v', positive=True)
Pmb = sp.exp(-bes*(m*v**2/2 + V))
Vx = sp.diff(V, xs)
KK = -v*sp.diff(Pmb, xs) + sp.diff((gam*v + Vx)*Pmb, v)/m + gam/(m**2*bes)*sp.diff(Pmb, v, 2)
check('5j', "Klein--Kramers 稳态 Maxwell--Boltzmann（kT=1/β）", sp.simplify(KK) == 0)

# ---------- 05k 控制 ----------
for zeta in (0.3, 0.5, 0.7):
    wn = 2.0
    sys = signal.TransferFunction([wn**2], [1, 2*zeta*wn, wn**2])
    t_ = np.linspace(0, 20, 200001); _, yv = signal.step(sys, T=t_)
    Mp = yv.max() - 1; tp = t_[np.argmax(yv)]
    ok = abs(Mp - math.exp(-zeta*math.pi/math.sqrt(1 - zeta**2))) < 1e-4 and abs(tp - math.pi/(wn*math.sqrt(1 - zeta**2))) < 1e-3
    check('5k', f"二阶阶跃响应超调与峰时（ζ={zeta}）", ok)
check('5k', "ζ=0.5 超调 16%，ζ=0.7 约 5%", abs(math.exp(-0.5*math.pi/math.sqrt(0.75)) - 0.163) < 0.001 and abs(math.exp(-0.7*math.pi/math.sqrt(0.51)) - 0.046) < 0.001)
sysL = signal.TransferFunction([10], [1, 2, 10])     # 闭环：L=10/(s(s+2))
t_ = np.linspace(0, 30, 30001); _, yr, _ = signal.lsim(sysL, U=t_, T=t_)
check('5k', "1 型系统斜坡稳态误差 1/K_v（K_v=5）", abs((t_ - yr)[-1] - 0.2) < 1e-3)
for zeta in (0.2, 0.4, 0.6):
    w_ = np.linspace(0.01, 3, 300001); Gm = np.abs(1/(1 - w_**2 + 2j*zeta*w_))
    check('5k', f"谐振峰 M_r=1/(2ζ√(1-ζ²))（ζ={zeta}）", abs(Gm.max() - 1/(2*zeta*math.sqrt(1 - zeta**2))) < 1e-6 and abs(w_[np.argmax(Gm)] - math.sqrt(1 - 2*zeta**2)) < 1e-4)
def winding(L, wmax=1e4, n=2000001):
    w_ = np.concatenate([-np.logspace(4, -4, n//2), np.logspace(-4, 4, n//2)])
    ph = np.unwrap(np.angle(1 + L(1j*w_)))
    return (ph[-1] - ph[0])/(2*math.pi)
Lu = lambda s: 3/((s - 1)*(s + 2))
check('5k', "Nyquist：P=1、闭环稳定时逆时针绕 -1 一圈", abs(winding(Lu) - 1) < 1e-3 and np.all(np.roots([1, 1, 1]).real < 0))
den = np.poly([0, -1, -2])
Ks = 1e6; rts = np.roots(den + np.r_[0, 0, 0, Ks])
ang = sorted((math.degrees(math.atan2((r_ + 1).imag, (r_ + 1).real)) % 360) for r_ in rts)
check('5k', "根轨迹渐近线：中心 -1，角度 60°/180°/300°", np.allclose(ang, [60, 180, 300], atol=0.5))
sb = sp.symbols('s'); Kexpr = -(sb*(sb + 1)*(sb + 2))
check('5k', "分离点 dK/ds=0 → s=-1+1/√3", any(abs(complex(r_) - (-1 + 1/math.sqrt(3))) < 1e-12 for r_ in sp.solve(sp.diff(Kexpr, sb), sb)))
for al in (0.1, 0.25, 0.5):
    wz, wp = 1.0, 1/al
    w_ = np.logspace(-3, 3, 200001); ph = np.arctan(w_/wz) - np.arctan(w_/wp)
    check('5k', f"超前校正 sinφmax=(1-α)/(1+α)（α={al}）", abs(math.sin(ph.max()) - (1 - al)/(1 + al)) < 1e-8 and abs(w_[np.argmax(ph)] - math.sqrt(wz*wp)) < 1e-3)
for zeta in (0.3, 0.5, 0.6):
    wc = math.sqrt(math.sqrt(1 + 4*zeta**4) - 2*zeta**2)
    Lz = lambda w: 1/(1j*w*(1j*w + 2*zeta))
    pm = 180 + math.degrees(np.angle(Lz(wc)))
    check('5k', f"相位裕度公式（ζ={zeta}）", close(abs(Lz(wc)), 1, 1e-12) and close(pm, math.degrees(math.atan(2*zeta/wc)), 1e-9) and abs(pm - 100*zeta) < 6)
for kT in (1.5, 1.6):
    # s+k e^{-sT}=0 的根：用 Lambert W，最右支 s=W(-kT)/T
    s_root = complex(mp.lambertw(-kT, 0))
    check('5k', f"积分+时延 kT={kT} 稳定性（界 π/2）", (s_root.real < 0) == (kT < math.pi/2))
def bode_int(num, den):
    f = lambda w: math.log(abs(1/(1 + np.polyval(num, 1j*w)/np.polyval(den, 1j*w))))
    return integrate.quad(f, 0, np.inf, limit=500)[0]
check('5k', "Bode 灵敏度积分：稳定开环为 0，开环极点 p=1 时为 π", abs(bode_int([5], np.poly([-1, -2]))) < 1e-6 and abs(bode_int([5], np.poly([1, -2])) - math.pi) < 1e-6)
P_ = lambda s: (3 - s)/((s - 1)*(s + 5)); kc = 2.5
w_ = np.linspace(0, 200, 400001); Smax = np.max(np.abs(1/(1 + kc*P_(1j*w_))))
check('5k', "‖S‖∞ ≥ |(z+p)/(z-p)|（z=3,p=1）", np.all(np.roots([1, 4 - kc, -5 + 3*kc]).real < 0) and Smax >= 2 - 1e-9)
w0 = 1.0
dlnG = lambda u: -2*math.exp(2*u)/(1 + math.exp(2*u))          # G=1/(s+1)²，u=ln ω
phase = integrate.quad(lambda u: dlnG(u)*math.log(1/math.tanh(abs(u)/2)) if u != 0 else 0, -40, 40, points=[0], limit=400)[0]/math.pi
check('5k', "Bode 增益--相位积分（1/(s+1)² 在 ω=1 为 -90°）", abs(math.degrees(phase) + 90) < 1e-6)
A = rng.normal(size=(4, 4)); B = rng.normal(size=(4, 1))
Cc = np.hstack([np.linalg.matrix_power(A, k)@B for k in range(4)])
poles = [-1, -2, -3, -4]; coeff = np.poly(poles)
alphaA = sum(c_*np.linalg.matrix_power(A, 4 - i) for i, c_ in enumerate(coeff))
Kack = np.r_[np.zeros(3), 1]@np.linalg.inv(Cc)@alphaA
check('5k', "Ackermann 公式", np.allclose(np.sort(np.linalg.eigvals(A - B@Kack[None, :]).real), [-4, -3, -2, -1], atol=1e-6))
C = rng.normal(size=(1, 4))
Lo = signal.place_poles(A.T, C.T, [-5, -6, -7, -8]).gain_matrix.T
Acl = np.block([[A - B@Kack[None, :], B@Kack[None, :]], [np.zeros((4, 4)), A - Lo@C]])
check('5k', "分离原理：闭环特征值 = 控制 ∪ 观测", np.allclose(np.sort(np.linalg.eigvals(Acl).real), [-8, -7, -6, -5, -4, -3, -2, -1], atol=1e-5))
a0, a1, a2, b0, b1, b2 = sp.symbols('a0 a1 a2 b0 b1 b2')
Ac = sp.Matrix([[0, 1, 0], [0, 0, 1], [-a0, -a1, -a2]]); Bc = sp.Matrix([0, 0, 1]); Ccn = sp.Matrix([[b0, b1, b2]])
Gs = sp.simplify((Ccn*(sb*sp.eye(3) - Ac).inv()*Bc)[0])
check('5k', "可控标准形实现 C(sI-A)⁻¹B", sp.simplify(Gs - (b2*sb**2 + b1*sb + b0)/(sb**3 + a2*sb**2 + a1*sb + a0)) == 0)
n_ = 6
Ar = rng.normal(size=(n_, n_)); Ar -= (max(np.linalg.eigvals(Ar).real) + 0.5)*np.eye(n_)
Br = rng.normal(size=(n_, 1)); Cr = rng.normal(size=(1, n_))
Wc = linalg.solve_continuous_lyapunov(Ar, -Br@Br.T); Wo = linalg.solve_continuous_lyapunov(Ar.T, -Cr.T@Cr)
Lc = np.linalg.cholesky(Wc); U_, sv, _ = np.linalg.svd(Lc.T@Wo@Lc)
hsv = np.sqrt(sv); Tb = Lc@U_@np.diag(hsv**-0.5); Ti = np.linalg.inv(Tb)
Ab, Bb_, Cb = Ti@Ar@Tb, Ti@Br, Cr@Tb
rr_ = 2
Gf = lambda A_, B_, C_, w: (C_@np.linalg.solve(1j*w*np.eye(len(A_)) - A_, B_))[0, 0]
err = max(abs(Gf(Ar, Br, Cr, w) - Gf(Ab[:rr_, :rr_], Bb_[:rr_], Cb[:, :rr_], w)) for w in np.concatenate([[0], np.logspace(-3, 3, 3000)]))
check('5k', "平衡截断误差 ≤ 2Σ_{i>r}σ_i", err <= 2*hsv[rr_:].sum() + 1e-9 and np.allclose(np.sort(np.linalg.eigvals(Wc@Wo).real)[::-1], hsv**2))
H2_int = integrate.quad(lambda w: abs(Gf(Ar, Br, Cr, w))**2, -np.inf, np.inf, limit=500)[0]/(2*math.pi)
check('5k', "H₂ 范数 = tr(C W_c Cᵀ)；1/(s+a) 给 1/2a", close(H2_int, (Cr@Wc@Cr.T)[0, 0], 1e-6) and close(integrate.quad(lambda w: 1/(w*w + 4), -np.inf, np.inf)[0]/(2*math.pi), 1/4))
Tsm = 0.1; wd = 7.0
zd = np.exp(1j*wd*Tsm); s_t = 2/Tsm*(zd - 1)/(zd + 1)
check('5k', "Tustin 频率畸变 ω_a=(2/T)tan(ω_dT/2)", close(s_t.imag, 2/Tsm*math.tan(wd*Tsm/2)) and abs(s_t.real) < 1e-12)
Ad = linalg.expm(Ar*Tsm); Bd = integrate.quad_vec(lambda tau: linalg.expm(Ar*tau)@Br, 0, Tsm)[0]
Mbig = linalg.expm(np.block([[Ar, Br], [np.zeros((1, n_ + 1))]])*Tsm)
check('5k', "ZOH 离散化：A_d=e^{AT}，B_d=∫e^{Aτ}dτ B", np.allclose(Mbig[:n_, :n_], Ad) and np.allclose(Mbig[:n_, n_:], Bd))
ok = True
for _ in range(5000):
    a1_, a0_ = rng.uniform(-3, 3, 2)
    ok &= (np.all(np.abs(np.roots([1, a1_, a0_])) < 1)) == (abs(a0_) < 1 and abs(a1_) < 1 + a0_)
check('5k', "二阶离散系统稳定判据 |a0|<1，|a1|<1+a0", ok)
Mrel, Arel = 1.3, 0.8
check('5k', "继电器描述函数 4M/(πA)（方波基波）", close(integrate.quad(lambda t: Mrel*np.sign(math.sin(t))*math.sin(t), 0, 2*math.pi, points=[math.pi])[0]/math.pi/Arel, 4*Mrel/(math.pi*Arel)))
G1, G2, H1, H2 = sp.symbols('G1 G2 H1 H2')
Xs = sp.symbols('X1 X2 Y')
sol = sp.solve([sp.Eq(Xs[0], 1 - H2*Xs[2]), sp.Eq(Xs[1], G1*Xs[0] - H1*Xs[1]), sp.Eq(Xs[2], G2*Xs[1])], Xs)
mason = G1*G2/(1 - (-H1 - G1*G2*H2))
check('5k', "Mason 公式（两个接触回路）", sp.simplify(sol[Xs[2]] - mason) == 0)
tau_, dt_ = sp.symbols('tau Delta_t', positive=True)
zi = sp.Symbol('zinv'); alf = tau_/(tau_ + dt_); sd = (1 - zi)/dt_
check('5k', "互补滤波 H_L+H_H=1；后向 Euler 得 θ_k=α(θ_{k-1}+ω_kΔt)+(1-α)θ_acc", sp.simplify(1/(tau_*sb + 1) + tau_*sb/(tau_*sb + 1) - 1) == 0 and
      sp.simplify(1/(tau_*sd + 1) - (1 - alf)/(1 - alf*zi)) == 0 and sp.simplify(tau_/(tau_*sd + 1) - alf*dt_/(1 - alf*zi)) == 0)
hh_ = lambda t: np.exp(-t)*np.cos(3*t)
check('5k', "BIBO：sup|y| = ‖h‖₁ 由 u=sgn h 取到", close(integrate.quad(lambda t: abs(hh_(t)), 0, 50, limit=500)[0], integrate.quad(lambda t: hh_(t)*np.sign(hh_(t)), 0, 50, limit=500)[0], 1e-8))

# ---------- 05l 积分变换与 Green 函数 ----------
t, s = sp.symbols('t s', positive=True)
a = sp.symbols('a', positive=True)
check('5l', "Laplace：t^n e^{at}，sin ωt，t^ν", sp.simplify(sp.laplace_transform(t**3*sp.exp(2*t), t, s, noconds=True) - 6/(s - 2)**4) == 0 and
      sp.simplify(sp.laplace_transform(sp.sin(3*t), t, s, noconds=True) - 3/(s**2 + 9)) == 0 and sp.simplify(sp.laplace_transform(t**sp.Rational(1, 3), t, s, noconds=True) - sp.gamma(sp.Rational(4, 3))/s**sp.Rational(4, 3)) == 0)
Lnum = lambda f, sv_: integrate.quad(lambda tt: f(tt)*math.exp(-sv_*tt), 0, np.inf, limit=400)[0]
aa = 0.8
check('5l', "1/√(πt)↔1/√s，erfc(a/2√t)↔e^{-a√s}/s，a e^{-a²/4t}/(2√π t^{3/2})↔e^{-a√s}", all(
    close(Lnum(lambda tt: 1/math.sqrt(math.pi*tt), sv_), 1/math.sqrt(sv_), 1e-7) and close(Lnum(lambda tt: math.erfc(aa/(2*math.sqrt(tt))), sv_), math.exp(-aa*math.sqrt(sv_))/sv_, 1e-7)
    and close(Lnum(lambda tt: aa/(2*math.sqrt(math.pi)*tt**1.5)*math.exp(-aa*aa/(4*tt)), sv_), math.exp(-aa*math.sqrt(sv_)), 1e-7) for sv_ in (0.5, 2.0)))
Tp = 2.0
sq = lambda tt: 1.0 if (tt % Tp) < Tp/2 else -1.0
saw = lambda tt: (tt % Tp)/Tp
check('5l', "周期函数：方波 tanh(sT/4)/s，锯齿波公式", all(close(sum(integrate.quad(lambda tt: sq(tt)*math.exp(-sv_*tt), k*Tp/2, (k + 1)*Tp/2)[0] for k in range(80)), math.tanh(sv_*Tp/4)/sv_, 1e-7)
    and close(sum(integrate.quad(lambda tt: saw(tt)*math.exp(-sv_*tt), k*Tp, (k + 1)*Tp)[0] for k in range(40)), 1/(Tp*sv_**2) - math.exp(-sv_*Tp)/(sv_*(1 - math.exp(-sv_*Tp))), 1e-7) for sv_ in (0.7, 1.9)))
tau = sp.symbols('tau', positive=True)
check('5l', "卷积方程 f=1+∫(t-τ)f 的解 cosh t", sp.simplify(1 + sp.integrate((t - tau)*sp.cosh(tau), (tau, 0, t)) - sp.cosh(t)) == 0)
check('5l', "∫sin t/t=π/2，∫e^{-at}sin bt/t=arctan(b/a)，∫sin²t/t²=π/2", close(float(mp.quadosc(lambda tt: mp.sin(tt)/tt, [0, mp.inf], omega=1)), math.pi/2, 1e-10)
      and close(integrate.quad(lambda tt: math.exp(-0.7*tt)*math.sin(1.3*tt)/tt, 0, np.inf)[0], math.atan(1.3/0.7), 1e-9) and close(float(mp.quadosc(lambda tt: mp.sin(tt)**2/tt**2, [0, mp.inf], omega=1)), math.pi/2, 1e-10))
k_ = 1.7; a_ = 0.9
Hk = lambda f: float(mp.quadosc(lambda r: f(r)*mp.besselj(0, k_*r)*r, [0, mp.inf], omega=k_))
check('5l', "Hankel 变换对：Gauss、e^{-ar}/r、e^{-ar}、1/r、圆盘", close(Hk(lambda r: mp.exp(-a_*r*r)), math.exp(-k_*k_/(4*a_))/(2*a_), 1e-8) and
      close(Hk(lambda r: mp.exp(-a_*r)/r), 1/math.sqrt(k_*k_ + a_*a_), 1e-8) and close(Hk(lambda r: mp.exp(-a_*r)), a_/(k_*k_ + a_*a_)**1.5, 1e-8) and
      close(Hk(lambda r: 1/r), 1/k_, 1e-7) and close(integrate.quad(lambda r: special.j0(k_*r)*r, 0, a_)[0], a_*special.j1(k_*a_)/k_, 1e-10))
sm_, am_ = 0.6, 1.7
check('5l', "Mellin：(1+x)^{-a}，e^{-x²}，1/(1+x)", close(integrate.quad(lambda xx: xx**(sm_ - 1)*(1 + xx)**-am_, 0, np.inf)[0], math.gamma(sm_)*math.gamma(am_ - sm_)/math.gamma(am_), 1e-8) and
      close(integrate.quad(lambda xx: xx**(sm_ - 1)*math.exp(-xx*xx), 0, np.inf)[0], math.gamma(sm_/2)/2, 1e-8) and close(integrate.quad(lambda xx: xx**(sm_ - 1)/(1 + xx), 0, np.inf)[0], math.pi/math.sin(math.pi*sm_), 1e-7))
def riesz_num(n, al, k):
    # |x|^{-α}=(1/Γ(α/2))∫t^{α/2-1}e^{-t|x|²}dt，逐项用 Gauss 的 Fourier 变换
    return integrate.quad(lambda tt: tt**(al/2 - 1)*(math.pi/tt)**(n/2)*math.exp(-k*k/(4*tt)), 0, np.inf)[0]/math.gamma(al/2)
riesz = lambda n, al, k: math.pi**(n/2)*2**(n - al)*math.gamma((n - al)/2)/math.gamma(al/2)*k**(al - n)
check('5l', "Riesz 势 Fourier 变换（含 4π/k²、2π²/k）", all(close(riesz_num(n, al, 1.3), riesz(n, al, 1.3), 1e-8) for n, al in [(3, 1), (3, 2), (2, 1), (5, 2.5), (1, 0.4)])
      and close(riesz(3, 1, 2.0), 4*math.pi/4) and close(riesz(3, 2, 2.0), 2*math.pi**2/2))
cw, tw, rw = 1.0, 2.0, 1.2
wid = 2e-3
g3 = lambda zz: math.exp(-(tw - math.hypot(rw, zz)/cw)**2/(2*wid**2))/(math.sqrt(2*math.pi)*wid)/(4*math.pi*math.hypot(rw, zz))
zr = math.sqrt((cw*tw)**2 - rw**2)
G2num = 2*integrate.quad(g3, zr - 0.05, zr + 0.05, points=[zr], limit=200)[0]
check('5l', "降维：三维推迟 Green 沿直线积分得二维 c/(2π√(c²t²-r²))", abs(G2num - cw/(2*math.pi*math.sqrt((cw*tw)**2 - rw**2))) < 1e-4)
xw = 0.7
G1num = integrate.quad(lambda yy: cw/(2*math.pi)/math.sqrt((cw*tw)**2 - xw**2 - yy*yy), -math.sqrt((cw*tw)**2 - xw**2), math.sqrt((cw*tw)**2 - xw**2))[0]
check('5l', "降维：二维沿直线积分得一维 c/2", close(G1num, cw/2, 1e-8))
mo, gm, w0 = 1.3, 0.4, 2.0
w1 = math.sqrt(w0**2 - gm**2/4)
Gt = lambda tt: math.exp(-gm*tt/2)*math.sin(w1*tt)/(mo*w1)
sol = integrate.solve_ivp(lambda tt, yy: [yy[1], -gm*yy[1] - w0**2*yy[0]], [0, 10], [0, 1/mo], rtol=1e-11, atol=1e-13, dense_output=True)
wq = 1.1
chi_num = integrate.quad(Gt, 0, 200, weight='cos', wvar=wq, limit=400)[0] + 1j*integrate.quad(Gt, 0, 200, weight='sin', wvar=wq, limit=400)[0]
check('5l', "阻尼振子 Green 函数与 χ(ω)=1/[m(ω₀²-ω²-iγω)]", all(close(sol.sol(tt)[0], Gt(tt), 1e-8) for tt in (0.5, 3.0, 7.0)) and abs(chi_num - 1/(mo*(w0**2 - wq**2 - 1j*gm*wq))) < 1e-7)
Ls = rng.normal(size=(5, 5)); Ls = Ls + Ls.T; lam_, Phi = np.linalg.eigh(Ls); zc = 0.3 + 0.2j
check('5l', "Green 函数谱表示 Σφφ*/(λ-z)", np.allclose(np.linalg.inv(Ls - zc*np.eye(5)), (Phi/(lam_ - zc))@Phi.T))
X_, Y_, L_ = sp.symbols('x y L', positive=True)
Glo = (X_**2 + Y_**2)/(2*L_) - Y_; Ghi = (X_**2 + Y_**2)/(2*L_) - X_
check('5l', "Neumann 广义 Green 函数：-G''=-1/L，G'(0)=G'(L)=0，跳跃 -1", sp.simplify(-sp.diff(Glo, X_, 2) + 1/L_) == 0 and sp.diff(Glo, X_).subs(X_, 0) == 0 and
      sp.simplify(sp.diff(Ghi, X_).subs(X_, L_)) == 0 and sp.simplify((sp.diff(Ghi, X_) - sp.diff(Glo, X_)).subs(X_, Y_)) == -1 and sp.simplify((Ghi - Glo).subs(X_, Y_)) == 0)
xg = np.linspace(-math.pi, math.pi, 13)
ser = np.array([sum(math.cos(n*xx)/n**2 for n in range(1, 200000)) for xx in xg])
check('5l', "Σcos nx/n² = π²/6-π|x|/2+x²/4（|x|≤π），圆周 Green 函数零均值", np.allclose(ser, math.pi**2/6 - math.pi*np.abs(xg)/2 + xg**2/4, atol=1e-5) and
      abs(integrate.quad(lambda xx: math.pi**2/3 - math.pi*abs(xx) + xx*xx/2, -math.pi, math.pi)[0]) < 1e-10)
Rb = 1.0; xin = np.array([0.3, -0.2, 0.4])
uh = lambda p: p[0]**2 - p[1]**2 + 2*p[0]*p[2]
def poisson_ball(f):
    def integrand(th, ph):
        xi = np.array([math.sin(th)*math.cos(ph), math.sin(th)*math.sin(ph), math.cos(th)])*Rb
        return (Rb**2 - xin@xin)/(4*math.pi*Rb*np.linalg.norm(xin - xi)**3)*f(xi)*Rb**2*math.sin(th)
    return integrate.dblquad(integrand, 0, 2*math.pi, 0, math.pi, epsabs=1e-11, epsrel=1e-11)[0]
check('5l', "球的 Poisson 核重构调和函数", close(poisson_ball(uh), uh(xin), 1e-8) and close(poisson_ball(lambda p: 1.0), 1.0, 1e-8))
zx, zy, wx, wy = sp.symbols('zx zy wx wy', real=True)
Guh = -sp.log(((zx - wx)**2 + (zy - wy)**2)/((zx - wx)**2 + (zy + wy)**2))/(4*sp.pi)
check('5l', "上半平面 Green 函数调和且边界为零", sp.simplify(sp.diff(Guh, zx, 2) + sp.diff(Guh, zy, 2)) == 0 and sp.simplify(Guh.subs(zy, 0)) == 0)
r = sp.symbols('r', positive=True)
lap2 = lambda f: sp.diff(r*sp.diff(f, r), r)/r; lap3 = lambda f: sp.diff(r**2*sp.diff(f, r), r)/r**2
check('5l', "双调和基本解：Δ(r²ln r/8π)=(ln r+1)/2π，Δ(-r/8π)=-1/(4πr)", sp.simplify(lap2(r**2*sp.log(r)/(8*sp.pi)) - (sp.log(r) + 1)/(2*sp.pi)) == 0 and sp.simplify(lap3(-r/(8*sp.pi)) + 1/(4*sp.pi*r)) == 0)
xr, kap, kw = sp.symbols('x kappa k', positive=True)
check('5l', "一维 Green 三件套的导数跳跃 -1", all(sp.simplify(sp.diff(G, xr).subs(xr, 0)*2) == -1 for G in (-xr/2, sp.exp(-kap*xr)/(2*kap))) and
      sp.simplify(2*sp.diff(sp.I/(2*kw)*sp.exp(sp.I*kw*xr), xr).subs(xr, 0)) == -1 and sp.simplify(sp.diff(sp.exp(-kap*xr)/(2*kap), xr, 2) - kap**2*sp.exp(-kap*xr)/(2*kap)) == 0)
check('5l', "θ 函数变换 Σe^{-πn²t}=t^{-1/2}Σe^{-πn²/t}", all(close(sum(math.exp(-math.pi*n*n*tt) for n in range(-60, 61)), sum(math.exp(-math.pi*n*n/tt) for n in range(-60, 61))/math.sqrt(tt), 1e-13) for tt in (0.3, 1.0, 2.7)))
def herm_fn(n, xx): return special.eval_hermite(n, xx)*math.exp(-xx*xx/2)
ok = True
for n in range(6):
    for kq in (0.4, 1.3):
        ft = (integrate.quad(lambda xx: herm_fn(n, xx)*math.cos(kq*xx), -30, 30, limit=300)[0] - 1j*integrate.quad(lambda xx: herm_fn(n, xx)*math.sin(kq*xx), -30, 30, limit=300)[0])/math.sqrt(2*math.pi)
        ok &= abs(ft - (-1j)**n*herm_fn(n, kq)) < 1e-9
check('5l', "Hermite 函数是 Fourier 变换的本征函数 (-i)^n", ok)
def rl_half(f, tt, h=1e-5):
    J = lambda T_: integrate.quad(lambda u: f(T_ - u), 0, T_, weight='alg', wvar=(-0.5, 0))[0]/math.gamma(0.5)
    return (J(tt + h) - J(tt - h))/(2*h)
check('5l', "半阶导数 D^{1/2}t=2√(t/π)，D^{1/2}1=1/√(πt)", close(rl_half(lambda u: u, 0.8), 2*math.sqrt(0.8/math.pi), 1e-7) and close(rl_half(lambda u: 1.0, 0.8), 1/math.sqrt(math.pi*0.8), 1e-7))
check('5l', "D^α t^β = Γ(β+1)/Γ(β+1-α) t^{β-α}（α=1/2, β=2）", close(rl_half(lambda u: u*u, 0.9), math.gamma(3)/math.gamma(2.5)*0.9**1.5, 1e-7))
def stehfest(F, tt, N=14):
    Vk = []
    for k in range(1, N + 1):
        sm = 0
        for j in range((k + 1)//2, min(k, N//2) + 1):
            sm += j**(N//2)*math.factorial(2*j)/(math.factorial(N//2 - j)*math.factorial(j)*math.factorial(j - 1)*math.factorial(k - j)*math.factorial(2*j - k))
        Vk.append((-1)**(k + N//2)*sm)
    return math.log(2)/tt*sum(Vk[k - 1]*F(k*math.log(2)/tt) for k in range(1, N + 1))
check('5l', "Gaver--Stehfest 反演 1/(s+1) → e^{-t}", all(abs(stehfest(lambda sv_: 1/(sv_ + 1), tt) - math.exp(-tt)) < 1e-4 for tt in (0.5, 1.0, 2.0)))

npass = sum(r[2] for r in R); print(f"\n第四轮数学（三）: {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
