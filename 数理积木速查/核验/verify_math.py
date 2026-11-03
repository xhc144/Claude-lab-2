"""第 1--5 章公式的符号/数值核验。每项输出 PASS/FAIL 及说明。
数值核验只覆盖所测的具体参数，不等于一般证明；一般性依赖所引教材定理。"""
import itertools, math
import numpy as np, sympy as sp
from scipy import integrate, linalg, optimize, stats

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(0)
x, t, a, b, n, k, lam = sp.symbols('x t a b n k lambda', real=True)

# ---------- 第 1 章 ----------
xs = 1.3; N = 37
lhs = sum(math.sin(j*xs) for j in range(1, N+1))
check(1, "sin 部分和闭式", abs(lhs - math.sin(N*xs/2)*math.sin((N+1)*xs/2)/math.sin(xs/2)) < 1e-12)
def iterate(f, x0, n):
    v = x0
    for _ in range(n): v = f(v)
    return v
nn = 10**6
check(1, "x_{n+1}=sin x_n ~ sqrt(3/n)", abs(iterate(math.sin, 1.0, nn)*math.sqrt(nn/3) - 1) < 2e-3)
check(1, "x_{n+1}=ln(1+x_n) ~ 2/n", abs(iterate(math.log1p, 1.0, nn)*nn/2 - 1) < 2e-3)
v = integrate.quad(lambda s: (math.exp(-2*s)-math.exp(-5*s))/s, 0, np.inf)[0]
check(1, "Frullani e^{-x}, a=2,b=5", abs(v - math.log(5/2)) < 1e-8)
I = integrate.quad(lambda s: math.exp(-0.7*s)*np.sinc(s/np.pi), 0, 200, limit=400)[0]
check(1, "I(a)=pi/2-arctan a (a=0.7)", abs(I - (math.pi/2 - math.atan(0.7))) < 1e-8)
A = np.array([[2.0, 0.6], [0.6, 1.0]]); bb = np.array([0.3, -0.5])
g = integrate.dblquad(lambda y, x_: math.exp(-0.5*np.array([x_, y])@A@np.array([x_, y]) + bb@np.array([x_, y])), -12, 12, -12, 12)[0]
check(1, "多元 Gauss 积分 n=2", abs(g - 2*math.pi/math.sqrt(np.linalg.det(A))*math.exp(0.5*bb@np.linalg.solve(A, bb))) < 1e-7)
an = sp.simplify(sp.integrate(x**2*sp.cos(n*x), (x, -sp.pi, sp.pi))/sp.pi)
nint = sp.symbols('m', integer=True, positive=True)
an_i = sp.simplify(an.subs(n, nint))
z4 = (sp.integrate(x**4, (x, -sp.pi, sp.pi))/sp.pi - (sp.integrate(x**2, (x, -sp.pi, sp.pi))/sp.pi)**2/2)/16
check(1, "Parseval x^2: a_n=4(-1)^n/n^2, zeta(4)=pi^4/90", sp.simplify(an_i - 4*(-1)**nint/nint**2) == 0 and sp.simplify(z4 - sp.pi**4/90) == 0)
M = rng.normal(size=(5, 5)) + 5*np.eye(5); u = rng.normal(size=5); w = rng.normal(size=5)
ok = abs(np.linalg.det(M + np.outer(u, w)) - np.linalg.det(M)*(1 + w@np.linalg.solve(M, u))) < 1e-9
Mi = np.linalg.inv(M); SM = Mi - np.outer(Mi@u, w@Mi)/(1 + w@Mi@u)
check(1, "行列式引理 + Sherman-Morrison", ok and np.allclose(SM, np.linalg.inv(M + np.outer(u, w))))
aa, bv, nd = 1.7, 0.4, 6; J = np.ones((nd, nd))
ev = np.sort(np.linalg.eigvalsh(aa*np.eye(nd) + bv*J))
check(1, "aI+bJ 特征值/逆", np.allclose(ev, sorted([aa]*(nd-1) + [aa + nd*bv])) and np.allclose(np.linalg.inv(aa*np.eye(nd)+bv*J), (np.eye(nd) - bv/(aa+nd*bv)*J)/aa))
Ab, Bb, Cb, Db = (rng.normal(size=(3, 3)) for _ in range(4))
Mb = np.block([[Ab, Bb], [Cb, Db]])
S = Db - Cb@np.linalg.solve(Ab, Bb)
inv_blk = np.block([[np.linalg.inv(Ab) + np.linalg.inv(Ab)@Bb@np.linalg.inv(S)@Cb@np.linalg.inv(Ab), -np.linalg.inv(Ab)@Bb@np.linalg.inv(S)], [-np.linalg.inv(S)@Cb@np.linalg.inv(Ab), np.linalg.inv(S)]])
Cc = 2*Ab@Ab - Ab + np.eye(3)  # 与 Ab 对易
check(1, "Schur 补行列式/分块逆/对易情形", abs(np.linalg.det(Mb) - np.linalg.det(Ab)*np.linalg.det(S)) < 1e-9 and np.allclose(inv_blk, np.linalg.inv(Mb))
      and abs(np.linalg.det(np.block([[Ab, Bb], [Cc, Db]])) - np.linalg.det(Ab@Db - Cc@Bb)) < 1e-8)
A1 = rng.normal(size=(2, 4)); B1 = rng.normal(size=(4, 2)); L = 0.37
check(1, "AB 与 BA 特征多项式", abs(L**4*np.linalg.det(L*np.eye(2) - A1@B1) - L**2*np.linalg.det(L*np.eye(4) - B1@A1)) < 1e-12)
blocks = [3, 2, 2, 1]; Nmat = linalg.block_diag(*[np.diag(np.ones(s-1), 1) for s in blocks])
r = [8] + [np.linalg.matrix_rank(np.linalg.matrix_power(Nmat, j)) for j in range(1, 6)]
cnt = {kk: r[kk-1] - 2*r[kk] + r[kk+1] for kk in range(1, 4)}
check(1, "秩序列读 Jordan 块(块 3,2,2,1)", cnt == {1: 1, 2: 2, 3: 1} and 8 - r[1] == 4)
ok = True
for _ in range(200):
    X = rng.normal(size=(6, 6)); Y = rng.normal(size=(6, 6)); X = X + X.T; Y = Y + Y.T
    la, lb, lc = (np.sort(np.linalg.eigvalsh(Z))[::-1] for Z in (X, Y, X + Y))
    for i in range(6):
        for j in range(6 - i):
            ok &= lc[i + j] <= la[i] + lb[j] + 1e-9
    lsub = np.sort(np.linalg.eigvalsh(X[:5, :5]))[::-1]
    ok &= all(la[q] + 1e-9 >= lsub[q] >= la[q + 1] - 1e-9 for q in range(5))
check(1, "Weyl 不等式与交错(随机 200 例)", ok)
def necklaces(nb, kc, flips):
    seen = set(); cnt = 0
    for c in itertools.product(range(kc), repeat=nb):
        if c in seen: continue
        cnt += 1
        orbit = [c[s:] + c[:s] for s in range(nb)]
        if flips: orbit += [tuple(reversed(o)) for o in orbit]
        seen.update(orbit)
    return cnt
ok = True
for nb, kc in [(6, 3), (5, 2), (8, 2), (7, 3)]:
    rot = sum(sp.totient(d)*kc**(nb//d) for d in sp.divisors(nb))
    refl = nb*kc**((nb+1)//2) if nb % 2 else nb//2*(kc**(nb//2+1) + kc**(nb//2))
    ok &= necklaces(nb, kc, False) == rot//nb and necklaces(nb, kc, True) == (rot + refl)//(2*nb)
check(1, "Burnside 项链(旋转/二面体, 4 组)", ok)
p = 7; coeffs = sp.Poly(sp.expand(((x+1)**p - 1)/x), x).all_coeffs()
check(1, "Phi_7(x+1) Eisenstein", coeffs[0] == 1 and all(c % p == 0 for c in coeffs[1:]) and coeffs[-1] % p**2 != 0)
Am = rng.normal(size=(4, 4))
H1 = np.zeros((3, 3)); H1[0, 1] = 0.7; H2 = np.zeros((3, 3)); H2[1, 2] = -1.1
check(1, "det e^A=e^trA, BCH(Heisenberg)", abs(np.linalg.det(linalg.expm(Am)) - math.exp(np.trace(Am))) < 1e-9
      and np.allclose(linalg.expm(H1)@linalg.expm(H2), linalg.expm(H1 + H2 + 0.5*(H1@H2 - H2@H1))))

# ---------- 第 2 章 ----------
aS, bS = sp.symbols('a b', positive=True)
rr = sp.Matrix([aS*sp.cos(t), aS*sp.sin(t), bS*t]); r1, r2, r3 = rr.diff(t), rr.diff(t, 2), rr.diff(t, 3)
kap = sp.simplify(r1.cross(r2).norm()/r1.norm()**3); tau = sp.simplify(r1.cross(r2).dot(r3)/r1.cross(r2).norm()**2)
check(2, "螺线 kappa, tau", sp.simplify(kap - aS/(aS**2 + bS**2)) == 0 and sp.simplify(tau - bS/(aS**2 + bS**2)) == 0)
X_, Y_ = sp.symbols('X Y', real=True)
f = X_**3/3 + X_*Y_**2 - 2*Y_**2 + X_*Y_
P = sp.Matrix([X_, Y_, f]); Pu, Pv = P.diff(X_), P.diff(Y_); nrm = Pu.cross(Pv); nrm = nrm/nrm.norm()
E_, F_, G_ = Pu.dot(Pu), Pu.dot(Pv), Pv.dot(Pv); L_, M_, N_ = P.diff(X_, 2).dot(nrm), P.diff(X_, Y_).dot(nrm), P.diff(Y_, 2).dot(nrm)
Kff = (L_*N_ - M_**2)/(E_*G_ - F_**2); Hff = (E_*N_ - 2*F_*M_ + G_*L_)/(2*(E_*G_ - F_**2))
fx, fy, fxx, fyy, fxy = f.diff(X_), f.diff(Y_), f.diff(X_, 2), f.diff(Y_, 2), f.diff(X_, Y_); W = 1 + fx**2 + fy**2
Kf = (fxx*fyy - fxy**2)/W**2; Hf = ((1 + fy**2)*fxx - 2*fx*fy*fxy + (1 + fx**2)*fyy)/(2*W**sp.Rational(3, 2))
pt = {X_: 0.4, Y_: -0.7}
check(2, "图像曲面 K、H 与基本形式一致", abs(float((Kff - Kf).subs(pt))) < 1e-12 and abs(float((Hff - Hf).subs(pt))) < 1e-12)
u_, v_, r_ = sp.symbols('u v r', positive=True)
def K_conf(lmb):
    return sp.simplify(-1/(2*lmb)*(sp.diff(sp.log(lmb), u_, 2) + sp.diff(sp.log(lmb), v_, 2)))
check(2, "共形 K: Poincare -1 / 球极 +1", sp.simplify(K_conf(4/(1 - u_**2 - v_**2)**2) + 1) == 0 and sp.simplify(K_conf(4/(1 + u_**2 + v_**2)**2) - 1) == 0)
Eo, Go = 1, sp.sin(u_)**2
Ko = -1/(2*sp.sqrt(Eo*Go))*(sp.diff(sp.diff(Go, u_)/sp.sqrt(Eo*Go), u_))
check(2, "正交度量公式(单位球) / 测地极坐标", abs(float(Ko.subs(u_, 0.9)) - 1) < 1e-12 and abs(float(Ko.subs(u_, 2.1)) - 1) < 1e-12 and sp.simplify(-sp.diff(sp.sinh(r_), r_, 2)/sp.sinh(r_) + 1) == 0)
Vn = [math.pi**(m/2)/math.gamma(m/2 + 1) for m in range(1, 15)]
check(2, "|S^2|=4pi, V_n(1) 在 n=5 最大", abs(2*math.pi**1.5/math.gamma(1.5) - 4*math.pi) < 1e-12 and int(np.argmax(Vn)) + 1 == 5)
th = np.linspace(0, 2*np.pi, 400, endpoint=False); dth = th[1] - th[0]
c1 = np.stack([np.cos(th), np.sin(th), 0*th], 1); d1 = np.stack([-np.sin(th), np.cos(th), 0*th], 1)*dth
c2 = np.stack([1 + np.cos(th), 0*th, np.sin(th)], 1); d2 = np.stack([-np.sin(th), 0*th, np.cos(th)], 1)*dth
diff = c1[:, None, :] - c2[None, :, :]
lk = np.sum(np.einsum('ijk,ijk->ij', diff, np.cross(d1[:, None, :], d2[None, :, :]))/np.linalg.norm(diff, axis=2)**3)/(4*np.pi)
check(2, "Hopf 链环绕数 = ±1", abs(abs(lk) - 1) < 1e-6, f"lk={lk:.8f}")

# ---------- 第 3 章 ----------
fp = [sum(1 for i in range(5) if s[i] == i) for s in itertools.permutations(range(5))]
check(3, "置换不动点 E=Var=1 (n=5 穷举)", abs(np.mean(fp) - 1) < 1e-12 and abs(np.var(fp) - 1) < 1e-12)
nc = 50; Hn = sum(1/j for j in range(1, nc+1)); var = sum((1-(nc-i+1)/nc)/((nc-i+1)/nc)**2 for i in range(1, nc+1))
check(3, "集卡 E=nH_n 渐近, Var<pi^2 n^2/6", abs(nc*Hn - (nc*math.log(nc) + 0.5772156649*nc + 0.5)) < 0.01 and var < math.pi**2*nc**2/6)
NN, pp = 10, 0.4; qq = 1 - pp; rr_ = qq/pp
Am_ = np.zeros((NN+1, NN+1)); bP = np.zeros(NN+1); bT = np.zeros(NN+1)
for i in range(NN+1):
    Am_[i, i] = 1
    if 0 < i < NN: Am_[i, i+1] -= pp; Am_[i, i-1] -= qq; bT[i] = 1
bP[NN] = 1
Pk = np.linalg.solve(Am_, bP); Tk = np.linalg.solve(Am_, bT); kk = 3
check(3, "赌徒破产概率与期望时长 (p=0.4,N=10,k=3)", abs(Pk[kk] - (1 - rr_**kk)/(1 - rr_**NN)) < 1e-12 and abs(Tk[kk] - (kk/(qq-pp) - NN/(qq-pp)*(1 - rr_**kk)/(1 - rr_**NN))) < 1e-9)
Am_[1:NN, :] = 0
for i in range(1, NN): Am_[i, i] = 1; Am_[i, i+1] = -0.5; Am_[i, i-1] = -0.5
check(3, "对称游走 E tau = k(N-k)", abs(np.linalg.solve(Am_, bT)[kk] - kk*(NN-kk)) < 1e-9)
deg = sum(sum(1 for dx, dy in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)] if 0 <= i+dx < 8 and 0 <= j+dy < 8) for i in range(8) for j in range(8))
check(3, "马步图度数和 336 -> 角格返回 168", deg == 336 and deg//2 == 168)
av, bvv = 5, 3; good = tot = 0
for perm in set(itertools.permutations('A'*av + 'B'*bvv)):
    tot += 1; s = 0; ok = True
    for c in perm:
        s += 1 if c == 'A' else -1
        if s <= 0: ok = False; break
    good += ok
check(3, "选票定理 (a,b)=(5,3)", abs(good/tot - (av-bvv)/(av+bvv)) < 1e-12)
nst, aq = 10, 3; cnt_max = cnt_gt = cnt_eq = 0
for steps in itertools.product([1, -1], repeat=nst):
    S_ = np.cumsum(steps); cnt_max += S_.max() >= aq; cnt_gt += S_[-1] > aq; cnt_eq += S_[-1] == aq
check(3, "反射原理 n=10,a=3", cnt_max == 2*cnt_gt + cnt_eq)
nq, kq = 9, 4
check(3, "均匀次序统计量方差", abs(stats.beta(kq, nq-kq+1).var() - kq*(nq-kq+1)/((nq+1)**2*(nq+2))) < 1e-14)
rho = 0.6; mvn = stats.multivariate_normal([0, 0], [[1, rho], [rho, 1]])
check(3, "二元正态象限概率", abs(mvn.cdf([0, 0]) - (0.25 + math.asin(rho)/(2*math.pi))) < 1e-6)
Gs = lambda s: math.exp(2.0*(s - 1)); qext = optimize.brentq(lambda s: Gs(s) - s, 0, 0.99)
qn = 0.0
for _ in range(2000): qn = Gs(qn)
check(3, "分支过程: G_n(0) -> 最小根 (Poisson 2)", abs(qn - qext) < 1e-10, f"q={qext:.6f}")

# ---------- 第 4 章 ----------
fm = lambda s: (s - 1)**3*(s + 2); dfm = lambda s: 3*(s-1)**2*(s+2) + (s-1)**3
xv = 1.5; errs = []
for _ in range(12): xv = xv - fm(xv)/dfm(xv); errs.append(xv - 1)
check(4, "三重根 Newton 线性率 2/3", abs(errs[-1]/errs[-2] - 2/3) < 1e-3)
xv = 1.5
for _ in range(8):
    if fm(xv) == 0: break
    xv = xv - 3*fm(xv)/dfm(xv)
check(4, "重数修正后快速收敛", abs(xv - 1) < 1e-10)
nodes, wts = np.polynomial.legendre.leggauss(2)
err = 2/5 - np.sum(wts*nodes**4)
const = 2**5*math.factorial(2)**4/(5*math.factorial(4)**3)*24
check(4, "Gauss 2 点误差常数 (f=x^4)", abs(err - const) < 1e-14)
h = 0.5; xs_ = np.arange(0, 2 + 1e-12, h)
T = h*(np.sum(xs_**2) - (xs_[0]**2 + xs_[-1]**2)/2); Sm = h/3*(xs_[0]**4 + xs_[-1]**4 + 4*np.sum(xs_[1:-1:2]**4) + 2*np.sum(xs_[2:-1:2]**4))
check(4, "复化梯形/Simpson 误差常数与符号", abs((T - 8/3) - 2*h**2/12*2) < 1e-12 and abs((Sm - 32/5) - 2*h**4/180*24) < 1e-12)
for hh in [0.1]:
    xg = np.arange(0, 1 + 1e-12, hh); Tg = hh*(np.sum(np.exp(xg)) - (1 + math.e)/2)
    em = hh**2/12*(math.e - 1) - hh**4/720*(math.e - 1)
check(4, "Euler-Maclaurin 前两项", abs((Tg - (math.e - 1)) - em) < 1e-9)
aT = 1.0; Nn = 16; fper = lambda s: 1/(2 - np.cos(s))  # 极点 Im z = ln(2+sqrt3)
th = 2*np.pi*np.arange(Nn)/Nn; IN = 2*np.pi/Nn*np.sum(fper(th)); Iex = 2*np.pi/math.sqrt(3)
Mb_ = 1/(2 - math.cosh(aT))  # |f|<=1/(2-cosh a) 在带形 |Im z|<a 内
check(4, "周期梯形指数收敛满足界", abs(IN - Iex) <= 4*math.pi*abs(Mb_)/(math.exp(aT*Nn) - 1), f"err={abs(IN-Iex):.2e}")
for nn_ in [4, 7]:
    ck = np.cos((2*np.arange(1, nn_+1) - 1)*np.pi/(2*nn_)); xx = np.linspace(-1, 1, 20001)
    check(4, f"Chebyshev 节点 max|prod|=2^(1-n), n={nn_}", abs(np.max(np.abs(np.prod(xx[:, None] - ck[None, :], 1))) - 2.0**(1-nn_)) < 1e-6)
rk4 = lambda z: 1 + z + z**2/2 + z**3/6 + z**4/24
check(4, "RK4 实轴稳定界 ≈ -2.785", abs(optimize.brentq(lambda z: abs(rk4(z)) - 1, -3, -2) + 2.7853) < 1e-3)
rS, thS = sp.symbols('r theta', real=True)
Gv = 1 + rS*(sp.exp(sp.I*thS) - 2 + sp.exp(-sp.I*thS))
check(4, "FTCS 放大因子", sp.simplify(sp.expand_complex(Gv) - (1 - 4*rS*sp.sin(thS/2)**2)) == 0)
nS = 8; sims = rng.normal(size=(200000, nS)).var(axis=1, ddof=1)
check(4, "Var S^2 = 2 sigma^4/(n-1) (正态 MC)", abs(sims.var() - 2/(nS - 1)) < 0.01)
pS = sp.symbols('p', positive=True)
check(4, "Delta 法: arcsin sqrt p 与 logit 方差", sp.simplify(sp.diff(sp.asin(sp.sqrt(pS)), pS)**2*pS*(1-pS) - sp.Rational(1, 4)) == 0
      and sp.simplify(sp.diff(sp.log(pS/(1-pS)), pS)**2*pS*(1-pS) - 1/(pS*(1-pS))) == 0)

# ---------- 第 5 章 ----------
lam_ = 400.0; xx = np.linspace(-3, 3, 600001)
lap = np.trapezoid(np.cos(xx)*np.exp(lam_*(-xx**2/2 + xx**4/50)), xx)  # f''(0)=-1, g(0)=1
check(5, "Laplace 方法 (相对误差 < 1%)", abs(lap/math.sqrt(2*math.pi/lam_) - 1) < 1e-2)
check(5, "驻相 f=x^2: sqrt(pi/lambda) e^{i pi/4}", abs(complex(sp.N(sp.integrate(sp.exp(sp.I*3*x**2), (x, -sp.oo, sp.oo)) - sp.sqrt(sp.pi/3)*sp.exp(sp.I*sp.pi/4)))) < 1e-14)
kv, av_ = 1.3, 0.8
v1 = integrate.quad(lambda s: 1/(s**2 + av_**2), -np.inf, np.inf, weight='cos', wvar=kv)[0] if False else 2*integrate.quad(lambda s: 1/(s**2 + av_**2), 0, np.inf, weight='cos', wvar=kv)[0]
v2 = integrate.quad(lambda s: 1/(2 + 1.5*math.cos(s)), 0, 2*math.pi)[0]
check(5, "留数: 余弦积分 / 三角积分", abs(v1 - math.pi/av_*math.exp(-kv*av_)) < 1e-8 and abs(v2 - 2*math.pi/math.sqrt(4 - 2.25)) < 1e-10)
s_ = sum(1/(j**2 + av_**2) for j in range(-200000, 200001))
check(5, "pi cot 求和", abs(s_ - math.pi/av_/math.tanh(math.pi*av_)) < 1e-5)
xg = 0.3; Gint = integrate.quad(lambda s: min(xg, s)*(1 - max(xg, s))*math.sin(3*s), 0, 1, points=[xg])[0]
uex = (math.sin(3*xg) - xg*math.sin(3))/9  # -u''=sin 3x, u(0)=u(1)=0
check(5, "Green 函数 x_<(1-x_>)", abs(Gint - uex) < 1e-10)
Rr, rp, thp = 1.0, 0.6, 0.4
pk = integrate.quad(lambda ph: (Rr**2 - rp**2)/(Rr**2 - 2*Rr*rp*math.cos(thp - ph) + rp**2)*math.cos(2*ph), 0, 2*math.pi)[0]/(2*math.pi)
check(5, "Poisson 核: 边值 cos2φ -> r^2 cos2θ", abs(pk - rp**2*math.cos(2*thp)) < 1e-10)
eps = 0.01; r1_, r2_ = np.roots([eps, 1, 1])
Aco = np.linalg.solve([[1, 1], [math.exp(r1_), math.exp(r2_)]], [0, 1])
xx = np.linspace(0, 1, 2001); yex = Aco[0]*np.exp(r1_*xx) + Aco[1]*np.exp(r2_*xx)
check(5, "边界层复合解误差 O(eps)", np.max(np.abs(yex - (np.exp(1 - xx) - np.exp(1 - xx/eps)))) < 5*eps)
aC, thC = sp.symbols('a theta', positive=True)
xc, yc = aC*(thC - sp.sin(thC)), aC*(1 - sp.cos(thC)); yp = sp.diff(yc, thC)/sp.diff(xc, thC)
check(5, "摆线满足 y(1+y'^2)=2a", sp.simplify(yc*(1 + yp**2) - 2*aC) == 0)
uL, uR = sp.symbols('u_L u_R')
check(5, "Burgers 激波速度", sp.simplify((uL**2/2 - uR**2/2)/(uL - uR) - (uL + uR)/2) == 0)

npass = sum(r[2] for r in R); print(f"\n第1-5章: {npass}/{len(R)} PASS")
import json; json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
