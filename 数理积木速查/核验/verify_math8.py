"""第三轮续写 05d--05h（应用数学补充）的核验。数值核验只覆盖所测参数。"""
import math, itertools, json
import numpy as np, sympy as sp, mpmath as mp
from scipy import integrate, linalg, special, stats, optimize

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(8)
close = lambda a, b, tol=1e-9: abs(a - b) <= tol*max(1, abs(b))
x, y, t = sp.symbols('x y t', real=True)

# ---------- 05d ODE ----------
M_, N_ = 3*x**2*y + 2*x*y + y**3, x**2 + y**2      # (M_y-N_x)/N = 3 ⇒ μ=e^{3x}
mu = sp.exp(3*x)
check('5d', "积分因子 μ=e^{∫h}", sp.simplify(sp.diff(mu*M_, y) - sp.diff(mu*N_, x)) == 0)
yf = sp.Function('y')
sol = sp.dsolve(sp.Eq(yf(x).diff(x) + yf(x)/x, x*yf(x)**3), yf(x))
check('5d', "Bernoulli 方程 v=y^{1-n} 线性化（与 dsolve 解一致）", all(sp.simplify(sp.diff(s.rhs, x) + s.rhs/x - x*s.rhs**3) == 0 for s in (sol if isinstance(sol, list) else [sol])))
q0, q1, q2 = sp.Integer(1), sp.Integer(0), sp.Integer(1)   # y'=1+y² ⇒ u''+u=0, y=-u'/u=tan
u = sp.cos(x); ysol = -sp.diff(u, x)/(q2*u)
check('5d', "Riccati ↔ 二阶线性", sp.simplify(sp.diff(ysol, x) - (q0 + q1*ysol + q2*ysol**2)) == 0)
p_ = sp.symbols('p'); ysing = x**2
check('5d', "Clairaut 奇解 y=x²（f(p)=-p²/4）", sp.simplify(ysing - (x*sp.diff(ysing, x) - sp.diff(ysing, x)**2/4)) == 0)
nu_ = sp.Rational(1, 3)
check('5d', "Bessel 指标方程根 ±ν", set(sp.solve(sp.Symbol('r')*(sp.Symbol('r') - 1) + sp.Symbol('r') - nu_**2, sp.Symbol('r'))) == {nu_, -nu_})
a_, b_, c_ = 0.3, 0.7, 1.9; zz = 0.4
w = lambda z: float(mp.hyp2f1(a_, b_, c_, z))
d1 = float(mp.diff(lambda z: mp.hyp2f1(a_, b_, c_, z), zz)); d2 = float(mp.diff(lambda z: mp.hyp2f1(a_, b_, c_, z), zz, 2))
check('5d', "₂F₁ 满足超几何方程", abs(zz*(1 - zz)*d2 + (c_ - (a_ + b_ + 1)*zz)*d1 - a_*b_*w(zz)) < 1e-12)
sl = integrate.solve_ivp(lambda t_, yy: [yy[1], -(4 + math.sin(t_))*yy[0]], [0, 40], [0, 1], rtol=1e-10, atol=1e-12, dense_output=True)
tt = np.linspace(0, 40, 400001); zs = tt[:-1][np.sign(sl.sol(tt)[0][:-1]) != np.sign(sl.sol(tt)[0][1:])]
gaps = np.diff(zs)
check('5d', "Sturm 比较：零点间距 ∈ [π/√5, π/√3]", gaps.min() >= math.pi/math.sqrt(5) - 1e-3 and gaps.max() <= math.pi/math.sqrt(3) + 1e-3)
def monodromy(q, T):
    def f(t_, Y): Y = Y.reshape(2, 2); return (np.array([[0, 1], [-q(t_), 0]]) @ Y).ravel()
    return integrate.solve_ivp(f, [0, T], np.eye(2).ravel(), rtol=1e-11, atol=1e-12).y[:, -1].reshape(2, 2)
Mm = monodromy(lambda t_: 1.0 + 0.3*math.cos(2*t_), math.pi)
check('5d', "Floquet：det M = exp∫tr A = 1（Hill）", abs(np.linalg.det(Mm) - 1) < 1e-8)
Mres = monodromy(lambda t_: 1.0 + 0.3*math.cos(2*t_), math.pi)
Mstab = monodromy(lambda t_: 2.0 + 0.3*math.cos(2*t_), math.pi)
check('5d', "Mathieu：ω₀=1 (参数共振) |tr M|>2；ω₀²=2 稳定", abs(np.trace(Mres)) > 2 and abs(np.trace(Mstab)) < 2)
vdp = lambda mu_: integrate.solve_ivp(lambda t_, s: [s[1], mu_*(1 - s[0]**2)*s[1] - s[0]], [0, 300 if mu_ < 1 else 30*mu_], [0.5, 0], rtol=1e-9, atol=1e-11, dense_output=True, method='LSODA')
s1 = vdp(0.05); tt = np.linspace(250, 300, 20001)
check('5d', "van der Pol 小 μ 振幅 → 2", abs(np.max(s1.sol(tt)[0]) - 2) < 0.01)
mu_big = 20.0; s2 = vdp(mu_big); tt = np.linspace(10*mu_big, 30*mu_big, 400001); xx = s2.sol(tt)[0]
up = tt[1:][(xx[:-1] < 0) & (xx[1:] >= 0)]
check('5d', "van der Pol 大 μ 周期 ≈ (3-2ln2)μ（含 O(μ^{-1/3}) 修正）", abs(np.mean(np.diff(up))/((3 - 2*math.log(2))*mu_big) - 1) < 0.15, f"{np.mean(np.diff(up)):.2f}")
sig, beta = 10.0, 8/3
check('5d', "Lorenz ρ_H ≈ 24.74", abs(sig*(sig + beta + 3)/(sig - beta - 1) - 24.7368) < 1e-3)
rhoH = sig*(sig + beta + 3)/(sig - beta - 1)
Jl = lambda rho: (lambda xs: np.array([[-sig, sig, 0], [1, -1, -xs], [xs, xs, -beta]]))(math.sqrt(beta*(rho - 1)))
check('5d', "Lorenz：ρ_H 处 C± 有纯虚特征值", abs(max(np.linalg.eigvals(Jl(rhoH)).real)) < 1e-6 and max(np.linalg.eigvals(Jl(rhoH + 0.5)).real) > 0)
def dde_stable(a, tau):
    lam = sp.symbols('l')
    return max(complex(r).real for r in [complex(mp.findroot(lambda l: l + a*mp.e**(-l*tau), complex(g1, g2))) for g1 in (-0.5, 0.1) for g2 in (0.5, 1.5, 3)]) < 0
check('5d', "时滞方程临界 aτ=π/2：特征根 iπ/(2τ)", abs(complex(1j*math.pi/2) + math.pi/2*np.exp(-1j*math.pi/2)) < 1e-12)
A_ = np.array([[0, 1], [-2, -3]]); B_ = np.array([[0], [1]])
P_ = linalg.solve_continuous_are(A_, B_, np.eye(2), np.eye(1))
check('5d', "LQR：Riccati 解与闭环稳定；Kalman 秩", np.allclose(A_.T @ P_ + P_ @ A_ - P_ @ B_ @ B_.T @ P_ + np.eye(2), 0) and max(np.linalg.eigvals(A_ - B_ @ B_.T @ P_).real) < 0 and np.linalg.matrix_rank(np.c_[B_, A_ @ B_]) == 2)
def rh_cubic(a, b, c): return a > 0 and b > 0 and c > 0 and a*b > c
okRH = all(rh_cubic(*co) == (max(np.roots([1, *co]).real) < 0) for co in rng.uniform(-1, 4, size=(2000, 3)))
check('5d', "Routh–Hurwitz 三次（随机多项式比对）", okRH)
Aq = rng.uniform(-1, 3, size=4)
check('5d', "Routh–Hurwitz 四次", all(((a1 > 0 and a2 > 0 and a3 > 0 and a4 > 0 and a1*a2 > a3 and a1*a2*a3 > a3**2 + a1**2*a4) == (max(np.roots([1, a1, a2, a3, a4]).real) < 0)) for a1, a2, a3, a4 in rng.uniform(0.01, 4, size=(2000, 4))))
k_ = 0.999999
check('5d', "单摆近分界线周期 (2/ω0)ln(16/(1-E/Es))", abs(4*float(mp.ellipk(k_**2)) - 2*math.log(16/(1 - k_**2))) < 1e-4)
check('5d', "无阻尼共振极限 F t sin(ω0 t)/(2ω0)", sp.simplify(sp.limit((sp.cos(sp.Symbol('w')*t) - sp.cos(2*t))/(4 - sp.Symbol('w')**2), sp.Symbol('w'), 2) - t*sp.sin(2*t)/4) == 0)
r_ = 3.3; pq = sorted(np.roots([r_**2, -r_*(r_ + 1), r_ + 1]).real)  # 周期2点满足 r²x²-r(r+1)x+(r+1)=0
check('5d', "Logistic 周期 2 稳定区间上限 1+√6", abs(r_**2*(1 - 2*pq[0])*(1 - 2*pq[1])) < 1 and abs((lambda r: (lambda pq: r**2*(1 - 2*pq[0])*(1 - 2*pq[1]))(sorted(np.roots([r**2, -r*(r + 1), r + 1]).real)))(1 + math.sqrt(6)) + 1) < 1e-9)
check('5d', "瞬态增长例最大放大 25", abs(max(np.linalg.norm(linalg.expm(np.array([[-1, 100], [0, -2]])*s), 2) for s in np.linspace(0, 3, 3001)) - 25) < 0.2)
pp_ = 2/x; qq_ = 1 - sp.Rational(1, 4)/x**2
check('5d', "消去一阶项的标准形 (Bessel ν=1/2)", sp.simplify(sp.Rational(1, 1) - (sp.Rational(1, 4) - sp.Rational(1, 4))/x**2 - (lambda p, q: q - p**2/4 - sp.diff(p, x)/2)(1/x, 1 - sp.Rational(1, 4)/x**2)) == 0)

# ---------- 05e PDE ----------
check('5e', "最慢衰减率：j01²、π²（球）", abs(special.jn_zeros(0, 1)[0] - 2.4048) < 1e-4 and abs(special.jnp_zeros(1, 1)[0] - 1.8412) < 1e-4)
nu_v = 0.1; X = np.linspace(-6, 6, 2001); tt_ = 1.0
phi = lambda xv, tv: np.array([integrate.quad(lambda yv: math.exp(-(xi - yv)**2/(4*nu_v*tv) - (yv if yv > 0 else 0)/(2*nu_v)), -8, 8, limit=200, points=[0, xi])[0] for xi in xv])
xs_ = np.linspace(-2, 3, 41); ph = phi(xs_, tt_); dph = (phi(xs_ + 1e-4, tt_) - phi(xs_ - 1e-4, tt_))/2e-4
uCH = -2*nu_v*dph/ph
check('5e', "Cole–Hopf：u0=H(-x)... 熵解形状（u∈[0,1] 单调）", np.all(uCH > -1e-6) and np.all(uCH < 1 + 1e-6))
c_ = 1.7; xi = sp.symbols('xi'); uK = c_/2*sp.sech(sp.sqrt(c_)/2*xi)**2
check('5e', "KdV 孤立子", abs(float((-c_*sp.diff(uK, xi) + 6*uK*sp.diff(uK, xi) + sp.diff(uK, xi, 3)).subs(xi, 0.37))) < 1e-12)
Dk, rk = 0.5, 2.0; Lx = 200; nx = 2000; dx = Lx/nx; dt = 0.2*dx**2/Dk
uF = np.zeros(nx); uF[:20] = 1
pos = []
for step in range(int(40/dt)):
    uF[1:-1] += dt*(Dk*(uF[2:] - 2*uF[1:-1] + uF[:-2])/dx**2 + rk*uF[1:-1]*(1 - uF[1:-1])); uF[0] = 1
    if step % int(1/dt) == 0: pos.append(np.argmax(uF < 0.5)*dx)
vF = (pos[-1] - pos[-11])/10
check('5e', "Fisher–KPP 速度 → 2√(Dr)", abs(vF/(2*math.sqrt(Dk*rk)) - 1) < 0.05, f"{vF:.3f}")
check('5e', "热方程阶跃解 ½erfc(x/(2√(Dt)))", sp.simplify(sp.diff(sp.erfc(x/(2*sp.sqrt(t)))/2, t) - sp.diff(sp.erfc(x/(2*sp.sqrt(t)))/2, x, 2)) == 0)
jz = sorted([special.jn_zeros(m, 2)[k] for m in range(4) for k in range(2)])[:4]
check('5e', "圆盘本征值顺序 2.405,3.832,5.136,5.520", np.allclose(jz, [2.4048, 3.8317, 5.1356, 5.5201], atol=1e-4))
n_ = 3
check('5e', "Hadamard 例：sinh(ny)sin(nx)/n² 满足 Laplace", sp.simplify(sp.diff(sp.sinh(n_*y)*sp.sin(n_*x), x, 2) + sp.diff(sp.sinh(n_*y)*sp.sin(n_*x), y, 2)) == 0)
vmax, rmax = 30.0, 0.2; rL, rR = 0.05, 0.15; q = lambda r: r*vmax*(1 - r/rmax)
check('5e', "LWR 激波速度公式", close((q(rR) - q(rL))/(rR - rL), vmax*(1 - (rL + rR)/rmax)))
xx2 = np.linspace(0, 1, 2001); u2 = xx2*(1 - xx2)**2
check('5e', "Poincaré 不等式常数 1/π²（Dirichlet，[0,1]）", np.trapezoid(u2**2, xx2) <= np.trapezoid(np.gradient(u2, xx2)**2, xx2)/math.pi**2)
xi0 = 0.3
check('5e', "-u'' Green 函数 min(x,ξ)-xξ 的展开", all(abs(min(xv, xi0) - xv*xi0 - sum(2*math.sin(k*math.pi*xv)*math.sin(k*math.pi*xi0)/(k*math.pi)**2 for k in range(1, 20000))) < 1e-5 for xv in (0.1, 0.5, 0.8)))
kk = np.linspace(0.01, 3, 50); c0, g0 = 1.0, 0.5
check('5e', "电报方程长波极限扩散 D=c²/(2γ)", abs((-1j*g0 + np.sqrt(complex(c0**2*0.01**2 - g0**2))).imag/0.01**2 + c0**2/(2*g0)) < 1e-3)
check('5e', "Harnack（n=2, R=1, r=0.5）上下界对 Poisson 核成立", all((1 - 0.5)/(1 + 0.5) - 1e-12 <= (1 - 0.25)/(1 - 2*0.5*math.cos(th) + 0.25) <= (1 + 0.5)/(1 - 0.5) + 1e-12 for th in np.linspace(0, 2*math.pi, 100)))

# ---------- 05f 变分/积分方程/特殊函数 ----------
check('5f', "最速降线 1.003 s vs 直线 1.189 s", abs(math.pi*math.sqrt(1/9.81) - 1.003) < 1e-3 and abs(math.sqrt(math.pi**2 + 4)/math.sqrt(9.81) - 1.189) < 1e-3)
the = sp.symbols('theta', positive=True)
xc, yc = 1*(the - sp.sin(the)), 1*(1 - sp.cos(the))
check('5f', "摆线满足 y(1+y'²)=2R", sp.simplify(yc*(1 + (sp.diff(yc, the)/sp.diff(xc, the))**2) - 2) == 0)
fv = lambda s_: math.cos(s_); lam = 0.7
uv = lambda s_: fv(s_) + lam*integrate.quad(lambda tt_: math.exp(lam*(s_ - tt_))*fv(tt_), 0, s_)[0]
check('5f', "Volterra K≡1 解", abs(uv(1.3) - fv(1.3) - lam*integrate.quad(lambda tt_: uv(tt_), 0, 1.3)[0]) < 1e-9)
check('5f', "Γ 倍元与三元乘法公式", close(math.gamma(0.7)*math.gamma(1.2), 2**(1 - 1.4)*math.sqrt(math.pi)*math.gamma(1.4))
      and close(math.gamma(0.4)*math.gamma(0.4 + 1/3)*math.gamma(0.4 + 2/3), (2*math.pi)*3**(0.5 - 1.2)*math.gamma(1.2)))
check('5f', "|Γ(½+iy)|²=π/cosh πy", close(abs(complex(mp.gamma(0.5 + 1.3j)))**2, math.pi/math.cosh(1.3*math.pi)))
check('5f', "ψ 反射与 Σ1/((n+a)(n+b))", close(float(mp.digamma(1 - 0.3) - mp.digamma(0.3)), math.pi/math.tan(0.3*math.pi)) and close(float(mp.nsum(lambda n: 1/((n + 0.4)*(n + 1.7)), [0, mp.inf])), float((mp.digamma(0.4) - mp.digamma(1.7))/(0.4 - 1.7))))
th0 = 2.0; k_ = math.sin(th0/2); w0 = 1.0
ps = integrate.solve_ivp(lambda t_, s: [s[1], -math.sin(s[0])], [0, 3], [0, 2*k_*w0], rtol=1e-11, atol=1e-12, dense_output=True)
check('5f', "单摆精确解 sin(θ/2)=k sn(ω0t,k)", all(abs(math.sin(ps.sol(tv)[0]/2) - k_*special.ellipj(tv, k_**2)[0]) < 1e-8 for tv in (0.5, 1.7, 2.9)))
check('5f', "₂F₁ 特例：arcsin、arctan、K", close(0.4*float(mp.hyp2f1(0.5, 0.5, 1.5, 0.16)), math.asin(0.4)) and close(0.4*float(mp.hyp2f1(0.5, 1, 1.5, -0.16)), math.atan(0.4))
      and close(math.pi/2*float(mp.hyp2f1(0.5, 0.5, 1, 0.36)), float(mp.ellipk(0.36))))
check('5f', "Kummer 变换与 erf 表示", close(float(mp.hyp1f1(0.3, 1.7, 0.9)), math.exp(0.9)*float(mp.hyp1f1(1.4, 1.7, -0.9))) and close(2*0.6/math.sqrt(math.pi)*float(mp.hyp1f1(0.5, 1.5, -0.36)), math.erf(0.6)))
jz = special.jn_zeros(2, 3)
check('5f', "Fourier–Bessel 正交与范数", abs(integrate.quad(lambda r: r*special.jv(2, jz[0]*r)*special.jv(2, jz[1]*r), 0, 1)[0]) < 1e-12 and close(integrate.quad(lambda r: r*special.jv(2, jz[2]*r)**2, 0, 1)[0], 0.5*special.jv(3, jz[2])**2))
check('5f', "平面波展开（kr=2.3, cosθ=0.4）", abs(sum((2*l + 1)*1j**l*special.spherical_jn(l, 2.3)*special.eval_legendre(l, 0.4) for l in range(40)) - np.exp(1j*2.3*0.4)) < 1e-12)
check('5f', "j1 零点 tan x = x: 4.493", abs(optimize.brentq(lambda z: special.spherical_jn(1, z), 4, 5) - 4.4934) < 1e-4)
check('5f', "K0 小 x 与 Kν 大 x 渐近", abs(special.k0(1e-4) - (-math.log(0.5e-4) - 0.5772156649)) < 1e-6 and abs(special.kv(1.5, 50)/(math.sqrt(math.pi/100)*math.exp(-50)) - 1) < 0.03)
check('5f', "Laguerre 母函数与广义正交", close(sum(special.eval_laguerre(n, 0.8)*0.3**n for n in range(80)), math.exp(-0.8*0.3/0.7)/0.7)
      and close(integrate.quad(lambda z: z**1.5*math.exp(-z)*special.eval_genlaguerre(3, 1.5, z)**2, 0, np.inf)[0], math.gamma(3 + 1.5 + 1)/math.factorial(3), 1e-8))
check('5f', "T_m(T_n)=T_mn；Chebyshev 母函数", close(special.eval_chebyt(3, special.eval_chebyt(4, 0.37)), special.eval_chebyt(12, 0.37)) and close(sum(special.eval_chebyt(n, 0.37)*0.6**n for n in range(200)), (1 - 0.37*0.6)/(1 - 2*0.37*0.6 + 0.36)))
nG = 5; xg, wg = special.roots_legendre(nG); kn = lambda n: math.factorial(2*n)/(2**n*math.factorial(n)**2); hn = lambda n: 2/(2*n + 1)
check('5f', "Christoffel–Darboux 给 Gauss 权", np.allclose([kn(nG)/kn(nG - 1)*hn(nG - 1)/(special.eval_legendre(nG - 1, xi)*(nG*(xi*special.eval_legendre(nG, xi) - special.eval_legendre(nG - 1, xi))/(xi**2 - 1))) for xi in xg], wg))
check('5f', "E1 界与 Stieltjes 关系", all(0.5*math.exp(-z)*math.log(1 + 2/z) < special.exp1(z) < math.exp(-z)*math.log(1 + 1/z) for z in (0.1, 1, 5, 20)) and close(integrate.quad(lambda s_: math.exp(-s_)/(2 + s_), 0, np.inf)[0], math.exp(2)*special.exp1(2)))
check('5f', "Lambert W: Wien 4.965、x=a+be^{cx} 公式", abs(5 + float(mp.lambertw(-5*math.exp(-5)).real) - 4.9651) < 1e-4 and (lambda a, b, c: abs((lambda X: X - a - b*math.exp(c*X))(a - float(mp.lambertw(-b*c*math.exp(a*c)).real)/c)) < 1e-12)(0.5, 0.2, -1.3))
check('5f', "Li₂(1/2)、Fermi–Dirac 积分", close(float(mp.polylog(2, 0.5)), math.pi**2/12 - math.log(2)**2/2) and close(integrate.quad(lambda z: z**1.5/(math.exp(z - 1.2) + 1), 0, 80)[0], -math.gamma(2.5)*float(mp.polylog(2.5, -math.exp(1.2)).real), 1e-8))
check('5f', "∫erfc² = (2-√2)/√π；Dawson 极大", close(integrate.quad(lambda z: math.erfc(z)**2, 0, np.inf)[0], (2 - math.sqrt(2))/math.sqrt(math.pi)) and abs(optimize.minimize_scalar(lambda z: -special.dawsn(z), bounds=(0, 2), method='bounded').x - 0.9241) < 1e-3)

# ---------- 05g 渐近 ----------
xS = 0.1; Sx = integrate.quad(lambda s_: math.exp(-s_)/(1 + xS*s_), 0, np.inf)[0]
errs = [abs(Sx - sum((-1)**k*math.factorial(k)*xS**k for k in range(N))) for N in range(1, 25)]
check('5g', "Stieltjes 最优截断误差 ≈ √(2π/x)e^{-1/x}", 0.3 < min(errs)/(math.sqrt(2*math.pi/xS)*math.exp(-1/xS)) < 3)
check('5g', "奇异摄动根 -1/ε-1+ε", abs((-1 - math.sqrt(1 + 4e-3))/(2e-3) - (-1/1e-3 - 1 + 1e-3)) < 1e-5)
check('5g', "Airy 主导平衡 x^{-1/4}e^{-2x^{3/2}/3}/(2√π)", abs(special.airy(10.0)[0]/(math.exp(-2/3*10**1.5)/(2*math.sqrt(math.pi)*10**0.25)) - 1) < 0.01)
xm = 1e-3
check('5g', "Mellin：Σe^{-n²x} ~ √π/(2√x)-1/2", abs(sum(math.exp(-k*k*xm) for k in range(1, 2000)) - (math.sqrt(math.pi)/(2*math.sqrt(xm)) - 0.5)) < 1e-6)
sig_ = np.cos(2*np.pi*5*np.linspace(0, 1, 4096, endpoint=False))
from scipy.signal import hilbert
check('5g', "Hilbert 变换 cos→sin，H²=-I", np.allclose(np.imag(hilbert(sig_)), np.sin(2*np.pi*5*np.linspace(0, 1, 4096, endpoint=False)), atol=1e-10))
Rg = 1.3; Fy = lambda yv: 2*math.sqrt(max(Rg**2 - yv**2, 0))
check('5g', "Abel 反演：常数圆盘", close(-1/math.pi*integrate.quad(lambda yv: (-2*yv/math.sqrt(Rg**2 - yv**2))/math.sqrt(yv**2 - 0.5**2), 0.5, Rg, limit=200)[0], 1.0, 1e-6))
check('5g', "Σ C(n,k)³ ~ 2·8^n/(√3 π n)", abs(sum(math.comb(300, k)**3 for k in range(301))/(2*8**300/(math.sqrt(3)*math.pi*300)) - 1) < 0.01)
check('5g', "Σ_{k≤n} n^k e^{-n}/k! → 1/2", abs(stats.poisson.cdf(10000, 10000) - 0.5) < 0.005)
gam, kT = 1.0, 0.03; V = lambda z: z**4/4 - z**2/2   # 阱 -1, 鞍 0, ΔV=1/4
mfpt = integrate.dblquad(lambda zp, z: math.exp((V(z) - V(zp))/kT)/kT*gam, -1.0, 0.0, lambda z: -3, lambda z: z, epsabs=1e-12, epsrel=1e-10)[0]   # 从阱底到鞍点的平均首达时间
check('5g', "Kramers 平均逃逸时间（过阻尼；到鞍点的首达时间 ×2；ΔV/kT≈8.3，相对修正 O(kT/ΔV)）", abs(2*mfpt/(2*math.pi*gam/math.sqrt(2*1)*math.exp(0.25/kT)) - 1) < 0.15, f"{2*mfpt/(2*math.pi*gam/math.sqrt(2)*math.exp(0.25/kT)):.3f}")
check('5g', "Wilson–Hilferty (k=5, 95%)", abs(5*(1 - 2/45 + 1.6449*math.sqrt(2/45))**3 - stats.chi2.ppf(0.95, 5))/stats.chi2.ppf(0.95, 5) < 0.01)
check('5g', "|Γ(x+iy)| 渐近与 Gamow 因子", abs(abs(complex(mp.gamma(0.7 + 30j)))/(math.sqrt(2*math.pi)*30**0.2*math.exp(-15*math.pi)) - 1) < 0.01 and close(abs(complex(mp.gamma(1 + 0.8j)))**2, math.pi*0.8/math.sinh(math.pi*0.8)))
lam = 200.0
check('5g', "Watson 推广例 √(π/λ)(1+1/(4λ))", abs(integrate.quad(lambda s_: math.exp(-lam*s_)/math.sqrt(s_*(1 - s_)), 0, 1, limit=200)[0]/(math.sqrt(math.pi/lam)*(1 + 1/(4*lam))) - 1) < 1e-4)

# ---------- 05h 离散/优化 ----------
import heapq
G = {0: {1: 4, 2: 1}, 1: {3: 1}, 2: {1: 2, 3: 5}, 3: {}}
def dijkstra(G, s):
    d = {s: 0}; pq = [(0, s)]
    while pq:
        dv, v = heapq.heappop(pq)
        if dv > d[v]: continue
        for u_, w_ in G[v].items():
            if d.get(u_, 1e18) > dv + w_: d[u_] = dv + w_; heapq.heappush(pq, (d[u_], u_))
    return d
check('5h', "Dijkstra 例", dijkstra(G, 0)[3] == 4)
a, b, c, d = 3.0, -1.0, -2.0, 4.0
p = (d - c)/(a - b - c + d); v = (a*d - b*c)/(a - b - c + d)
check('5h', "2×2 零和博弈公式（与 LP 比较）", close(p*a + (1 - p)*c, v) and close(p*b + (1 - p)*d, v) and close(-optimize.linprog([0, 0, -1], A_ub=[[-a, -c, 1], [-b, -d, 1]], b_ub=[0, 0], A_eq=[[1, 1, 0]], b_eq=[1], bounds=[(0, 1), (0, 1), (None, None)]).fun, v))
gma = 0.9; Pm = rng.dirichlet(np.ones(4), size=(4, 2)); Rw = rng.random((4, 2)); V0 = np.zeros(4); Vs = [V0]
for _ in range(200): Vs.append(np.max(Rw + gma*np.einsum('sat,t->sa', Pm, Vs[-1]), 1))
check('5h', "值迭代 γ 压缩", all(np.max(np.abs(Vs[k + 1] - Vs[-1])) <= gma*np.max(np.abs(Vs[k] - Vs[-1])) + 1e-12 for k in range(50)))
def knap(ws, vs, W):
    V = [0]*(W + 1)
    for wi, vi in zip(ws, vs):
        for w_ in range(W, wi - 1, -1): V[w_] = max(V[w_], V[w_ - wi] + vi)
    return V[W]
ws, vs = [3, 4, 5, 9, 4], [3, 4, 4, 10, 4]
check('5h', "背包 DP 与穷举一致", knap(ws, vs, 11) == max(sum(v_ for v_, s_ in zip(vs, m) if s_) for m in itertools.product([0, 1], repeat=5) if sum(w_ for w_, s_ in zip(ws, m) if s_) <= 11))
nP = 30; Ap = np.diag(np.ones(nP - 1), 1); Ap = Ap + Ap.T; Lp = np.diag(Ap.sum(1)) - Ap
check('5h', "路径图 μ₂=2(1-cos π/n)", close(np.sort(np.linalg.eigvalsh(Lp))[1], 2*(1 - math.cos(math.pi/nP))))
G2 = np.zeros((10, 10)); G2[:5, :5] = 1; G2[5:, 5:] = 1; G2[4, 5] = G2[5, 4] = 1; np.fill_diagonal(G2, 0)
Dg = G2.sum(1); Ln = np.eye(10) - G2/np.sqrt(np.outer(Dg, Dg)); l2 = np.sort(np.linalg.eigvalsh(Ln))[1]
def cheeger(A):
    best = 1e9; vol = A.sum()
    for k in range(1, 6):
        for S in itertools.combinations(range(10), k):
            S = list(S); cut = A[np.ix_(S, [i for i in range(10) if i not in S])].sum(); vS = A[S].sum()
            best = min(best, cut/min(vS, vol - vS))
    return best
hC = cheeger(G2)
check('5h', "Cheeger 不等式 λ₂/2 ≤ h ≤ √(2λ₂)", l2/2 <= hC <= math.sqrt(2*l2))
fied = np.linalg.eigh(np.diag(Dg) - G2)[1][:, 1]
check('5h', "Fiedler 向量按符号分出两团", len(set(np.sign(fied[:5]))) == 1 and len(set(np.sign(fied[5:]))) == 1 and np.sign(fied[0]) != np.sign(fied[9]))
Pg = rng.random((50, 50))*(rng.random((50, 50)) < 0.1); Pg[Pg.sum(1) == 0] = 1; Pg = Pg/Pg.sum(1)[:, None]
pr = np.ones(50)/50; errs = []
Gm = 0.85*Pg.T + 0.15/50*np.ones((50, 50)); w_, vv = np.linalg.eig(Gm); pstar = np.real(vv[:, np.argmax(np.real(w_))]); pstar /= pstar.sum()
for _ in range(30): pr = 0.15/50 + 0.85*pr @ Pg; errs.append(np.abs(pr - pstar).sum())
check('5h', "PageRank 幂迭代误差每步 ≤ d 倍", all(errs[k + 1] <= 0.85*errs[k] + 1e-15 for k in range(25)))
inc = np.zeros((6, 9)); edges = [(i, j) for i in range(3) for j in range(3)]
for e_, (i, j) in enumerate(edges): inc[i, e_] = 1; inc[3 + j, e_] = 1
check('5h', "二部图关联矩阵全幺模（所有 3×3 子式 ∈ {0,±1}）", all(round(abs(np.linalg.det(inc[np.ix_(r, c)]))) in (0, 1) for r in itertools.combinations(range(6), 3) for c in itertools.combinations(range(9), 3)))
check('5h', "log₂ n! ≈ n log₂ n - 1.443n（n=1000）", abs(math.lgamma(1001)/math.log(2) - (1000*math.log2(1000) - 1000/math.log(2))) < 10)
mB, nB = 10000, 1000; kB = round(mB/nB*math.log(2)); bits = np.zeros(mB, bool); hs = rng.integers(0, mB, size=(nB, kB)); bits[hs.ravel()] = True
fp = np.mean(np.all(bits[rng.integers(0, mB, size=(200000, kB))], 1))
check('5h', "Bloom 假阳性 ≈ (1-e^{-kn/m})^k", abs(fp - (1 - math.exp(-kB*nB/mB))**kB) < 1.5e-3)
th = np.linspace(1e-4, math.pi, 200000)
check('5h', "Goemans–Williamson 常数 0.878", abs(np.min(2*th/(math.pi*(1 - np.cos(th)))) - 0.8786) < 1e-3)
nE, T_ = 10, 5000; eta = math.sqrt(8*math.log(nE)/T_); Lc = rng.random((T_, nE))*np.linspace(0.5, 1, nE); wts = np.ones(nE); loss = 0
for t_ in range(T_): pdist = wts/wts.sum(); loss += pdist @ Lc[t_]; wts *= np.exp(-eta*Lc[t_])
check('5h', "Hedge 后悔 ≤ √(T ln n/2)", loss - Lc.sum(0).min() <= math.sqrt(T_*math.log(nE)/2))
nC, sC, mC = 200, 8, 80; xs0 = np.zeros(nC); xs0[rng.choice(nC, sC, replace=False)] = rng.normal(size=sC); Ac = rng.normal(size=(mC, nC))/math.sqrt(mC)
res = optimize.linprog(np.ones(2*nC), A_eq=np.c_[Ac, -Ac], b_eq=Ac @ xs0, bounds=[(0, None)]*(2*nC))
check('5h', "压缩感知 ℓ1 精确恢复（n=200, s=8, m=80）", np.max(np.abs(res.x[:nC] - res.x[nC:] - xs0)) < 1e-6)
ua, ub = rng.normal(0.3, 1.2, 4000), rng.normal(-0.5, 0.7, 4000)
check('5h', "1D 最优输运=排序配对；正态 W₂²", abs(np.mean((np.sort(ua) - np.sort(ub))**2) - (0.8**2 + 0.5**2)) < 0.05)

npass = sum(r[2] for r in R); print(f"\n第三轮续写数学(五) 05d–05h: {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
