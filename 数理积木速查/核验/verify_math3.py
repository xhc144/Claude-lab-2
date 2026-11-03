"""续写部分（04b--04c、05b--05c）的符号/数值核验。"""
import math, json, itertools
import numpy as np, sympy as sp
from scipy import integrate, linalg, special, stats, optimize, interpolate

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(3)
close = lambda a, b, tol=1e-9: abs(a - b) <= tol*max(1, abs(b))

# ---------- 04b 数值方法 ----------
a, b, c = 1.0, 1e8, 1.0
naive = (-b + math.sqrt(b*b - 4*a*c))/(2*a); x1 = (-b - math.sqrt(b*b - 4*a*c))/(2*a); stable = c/(a*x1)
check('4b', "稳定二次求根公式 (b=1e8)", abs(stable + 1e-8)/1e-8 < 1e-12 and abs(naive + 1e-8)/1e-8 > 1e-3, f"naive rel err {abs(naive+1e-8)/1e-8:.1e}")
f, df = np.sin, np.cos; x0 = 1.0
ec = abs((f(x0 + 6e-6) - f(x0 - 6e-6))/1.2e-5 - df(x0)); ef = abs((f(x0 + 1.5e-8) - f(x0))/1.5e-8 - df(x0))
cs = abs(np.imag(np.sin(x0 + 1e-20j))/1e-20 - df(x0))
check('4b', "中心差 ~1e-11, 前向差 ~1e-8, 复步长 ~机器精度", ec < 1e-10 and 1e-10 < ef < 1e-7 and cs < 1e-15, f"{ec:.1e},{ef:.1e},{cs:.1e}")
xs = np.linspace(0, np.pi, 11); hS = xs[1] - xs[0]
sp_ = interpolate.CubicSpline(xs, np.sin(xs), bc_type=((1, 1.0), (1, -1.0)))
xx = np.linspace(0, np.pi, 5001)
check('4b', "完全样条误差 ≤ 5/384 h^4 |f''''|", np.max(np.abs(sp_(xx) - np.sin(xx))) <= 5/384*hS**4)
check('4b', "Hilbert κ(H_10) ~ 1.6e13 ≈ e^{3.5n} 量级", 1e13 < np.linalg.cond(linalg.hilbert(10)) < 3e13)
seq = [0.5]
for _ in range(6): seq.append(math.cos(seq[-1]))
xs_ = optimize.brentq(lambda u: math.cos(u) - u, 0, 1)
ait = seq[3] - (seq[4] - seq[3])**2/(seq[5] - 2*seq[4] + seq[3])
check('4b', "Aitken 加速显著改善", abs(ait - xs_) < abs(seq[5] - xs_)/20, f"{abs(ait-xs_):.1e} vs {abs(seq[5]-xs_):.1e}")
def ab2(h):
    y = [1.0, math.exp(-h)]   # y'=-y
    for n in range(1, int(round(1/h))): y.append(y[n] + h/2*(3*(-y[n]) - (-y[n - 1])))
    return abs(y[-1] - math.exp(-1))
check('4b', "AB2 二阶收敛", abs(math.log2(ab2(0.01)/ab2(0.005)) - 2) < 0.1)
tS = sp.symbols('t'); hh = sp.symbols('h', positive=True)
ok = all(sp.simplify((p.subs(tS, hh) - sp.Rational(4, 3)*p.subs(tS, 0) + sp.Rational(1, 3)*p.subs(tS, -hh)) - sp.Rational(2, 3)*hh*sp.diff(p, tS).subs(tS, hh)) == 0 for p in (1 + 0*tS, tS, tS**2))
check('4b', "BDF2 系数对 2 次多项式精确", ok)
lamv = np.array([1.0, 3.0, 10.0]); eta = 2/(lamv.min() + lamv.max())
check('4b', "梯度法最优步长收缩因子 (κ-1)/(κ+1)", close(max(abs(1 - eta*lamv)), (10 - 1)/(10 + 1)))
nF = 9; hF = 1/(nF + 1); K = (np.diag([2]*nF) - np.diag([1]*(nF - 1), 1) - np.diag([1]*(nF - 1), -1))/hF
uF = np.linalg.solve(K, hF*np.ones(nF)); xF = np.arange(1, nF + 1)*hF
check('4b', "1D 有限元节点精确 (-u''=1)", np.allclose(uF, xF*(1 - xF)/2))
Asym = rng.normal(size=(8, 8)); Asym = Asym + Asym.T; xq = 0.7
Lm, Dm, perm = linalg.ldl(Asym - xq*np.eye(8))
check('4b', "LDL^T 惯性数特征值", sum(np.linalg.eigvalsh(Dm) < 0) == sum(np.linalg.eigvalsh(Asym) < xq))
U = rng.random(500000); fU, gU = np.exp(U), U
cst = -np.cov(fU, gU)[0, 1]/gU.var(); est = fU + cst*(gU - 0.5); rho = np.corrcoef(fU, gU)[0, 1]
check('4b', "控制变量方差降为 (1-ρ²)", abs(est.var()/fU.var() - (1 - rho**2)) < 1e-3)

# ---------- 04c 统计 ----------
lam_, nP = sp.symbols('lambda n', positive=True); T = sp.symbols('T', integer=True, nonnegative=True)
Eumvue = sp.summation((1 - 1/nP)**T*sp.exp(-nP*lam_)*(nP*lam_)**T/sp.factorial(T), (T, 0, sp.oo))
check('4c', "UMVUE (1-1/n)^T 无偏", sp.simplify(Eumvue - sp.exp(-lam_)) == 0)
nn, th = sp.symbols('n theta', positive=True)
VarMax = nn*th**2/((nn + 1)**2*(nn + 2))
check('4c', "Var((n+1)/n X_(n)) = θ²/(n(n+2))", sp.simplify(((nn + 1)/nn)**2*VarMax - th**2/(nn*(nn + 2))) == 0)
check('4c', "样本量常数 (1.96+0.84)² ≈ 7.85", abs((stats.norm.ppf(0.975) + stats.norm.ppf(0.8))**2 - 7.85) < 0.01)
check('4c', "20 个检验至少一次假阳性 64%", abs(1 - 0.95**20 - 0.6415) < 1e-3)
kW, nW = 3, 20; z = stats.norm.ppf(0.975); ph = kW/nW
wil = ((ph + z*z/(2*nW) - z*math.sqrt(ph*(1 - ph)/nW + z*z/(4*nW*nW)))/(1 + z*z/nW), (ph + z*z/(2*nW) + z*math.sqrt(ph*(1 - ph)/nW + z*z/(4*nW*nW)))/(1 + z*z/nW))
ci = stats.binomtest(kW, nW).proportion_ci(method='wilson')
check('4c', "Wilson 区间与 scipy 一致", abs(wil[0] - ci.low) < 1e-9 and abs(wil[1] - ci.high) < 1e-9)
check('4c', "三法则: (1-3/n)^n ≈ 0.05", abs((1 - 3/1000)**1000 - 0.05) < 0.001)
x1, x2 = rng.normal(0, 1, 12), rng.normal(0.5, 3, 7)
v1, v2 = x1.var(ddof=1)/12, x2.var(ddof=1)/7; nu = (v1 + v2)**2/(v1**2/11 + v2**2/6)
tt_ = (x1.mean() - x2.mean())/math.sqrt(v1 + v2)
check('4c', "Welch t 与自由度", abs(2*stats.t.sf(abs(tt_), nu) - stats.ttest_ind(x1, x2, equal_var=False).pvalue) < 1e-10)
n1, n2 = 4, 5; Us = []
for comb in itertools.combinations(range(n1 + n2), n1):
    Us.append(sum(1 for i in comb for j in set(range(n1 + n2)) - set(comb) if i > j))
check('4c', "Mann-Whitney U 均值/方差 (穷举)", close(np.mean(Us), n1*n2/2) and close(np.var(Us), n1*n2*(n1 + n2 + 1)/12))
groups = [rng.normal(m, 1, 10) for m in (0, 0.5, 1.2)]; allv = np.concatenate(groups)
ssb = sum(len(g)*(g.mean() - allv.mean())**2 for g in groups); ssw = sum(((g - g.mean())**2).sum() for g in groups)
check('4c', "单因素 ANOVA F 与 scipy 一致", close((ssb/2)/(ssw/27), stats.f_oneway(*groups).statistic))
X = rng.normal(size=(30, 4)); yv = X@np.array([1, -2, 0.5, 0]) + rng.normal(size=30); lr = 2.5
Ub, d, Vt = np.linalg.svd(X, full_matrices=False)
check('4c', "岭回归 SVD 收缩形式", np.allclose(np.linalg.solve(X.T@X + lr*np.eye(4), X.T@yv), Vt.T@np.diag(d/(d**2 + lr))@Ub.T@yv))
Hm = X@np.linalg.solve(X.T@X, X.T); res = yv - Hm@yv
loo = [(yv[i] - np.delete(X, i, 0)[0:0].sum() - X[i]@np.linalg.lstsq(np.delete(X, i, 0), np.delete(yv, i), rcond=None)[0])**2 for i in range(30)]
check('4c', "留一交叉验证捷径", close(np.mean(loo), np.mean((res/(1 - np.diag(Hm)))**2)))
phi = 0.9; nA = 1000
k_ = np.arange(1, nA); varmean = (1 + 2*np.sum((1 - k_/nA)*phi**k_))/nA
check('4c', "AR(1) 有效样本量 ≈ n(1-φ)/(1+φ)", abs((1/varmean)/(nA*(1 - phi)/(1 + phi)) - 1) < 0.02)
pp = sp.symbols('p', positive=True); xb = sp.symbols('x_b'); ell = xb*sp.log(pp) + (1 - xb)*sp.log(1 - pp); Ib = sp.simplify(-(sp.diff(ell, pp, 2)).subs(xb, pp))
check('4c', "Jeffreys: √I(p) ∝ p^{-1/2}(1-p)^{-1/2}", sp.simplify(Ib - 1/(pp*(1 - pp))) == 0)
Xd = rng.normal(size=(200, 3))@np.array([[2, 0, 0], [0.5, 1, 0], [0, 0.3, 0.2]]); Xc = Xd - Xd.mean(0)
check('4c', "PCA: σ_k²/(n-1) = 协方差特征值", np.allclose(np.sort(np.linalg.svd(Xc, compute_uv=False)**2/199), np.sort(np.linalg.eigvalsh(np.cov(Xd.T)))))

# ---------- 05b ODE 与特殊函数 ----------
t, w = sp.symbols('t omega', positive=True)
yp = t*sp.sin(w*t)/(2*w)
check('5b', "共振特解 t sin ωt/(2ω)", sp.simplify(sp.diff(yp, t, 2) + w**2*yp - sp.cos(w*t)) == 0)
xv = sp.symbols('x'); y1, y2, gfun = sp.exp(xv), sp.exp(-xv), xv
Wr = y1*sp.diff(y2, xv) - sp.diff(y1, xv)*y2
ypv = -y1*sp.integrate(y2*gfun/Wr, xv) + y2*sp.integrate(y1*gfun/Wr, xv)
check('5b', "常数变易公式 (y''-y=x)", sp.simplify(sp.diff(ypv, xv, 2) - ypv - xv) == 0)
y2r = sp.exp(xv)*sp.integrate(sp.exp(-sp.integrate(-2, xv))/sp.exp(2*xv), xv)
check('5b', "降阶得 x e^x", sp.simplify(y2r - xv*sp.exp(xv)) == 0)
check('5b', "Bessel 零点与渐近", np.allclose(special.jn_zeros(0, 3), [2.4048, 5.5201, 8.6537], atol=1e-4) and np.allclose(special.jn_zeros(1, 2), [3.8317, 7.0156], atol=1e-4)
      and abs(special.jv(2, 400.0) - math.sqrt(2/(math.pi*400))*math.cos(400 - math.pi - math.pi/4)) < 1e-3)
tt = sp.symbols('t')
ser = sp.series(1/sp.sqrt(1 - 2*xv*tt + tt**2), tt, 0, 5).removeO()
check('5b', "Legendre 母函数与归一化", all(sp.expand(ser.coeff(tt, k) - sp.legendre(k, xv)) == 0 for k in range(5))
      and all(sp.integrate(sp.legendre(k, xv)**2, (xv, -1, 1)) == sp.Rational(2, 2*k + 1) for k in range(5)))
ok = all(sp.expand(sp.hermite(k + 1, xv) - 2*xv*sp.hermite(k, xv) + 2*k*sp.hermite(k - 1, xv)) == 0 for k in range(1, 6))
ok &= all(sp.simplify(sp.integrate(sp.hermite(k, xv)**2*sp.exp(-xv**2), (xv, -sp.oo, sp.oo)) - sp.sqrt(sp.pi)*2**k*sp.factorial(k)) == 0 for k in range(4))
check('5b', "Hermite 递推与归一化", ok)
thv, phv = 0.7, 1.9
uns = sum(abs(special.sph_harm_y(2, m, thv, phv))**2 for m in range(-2, 3)) if hasattr(special, 'sph_harm_y') else sum(abs(special.sph_harm(m, 2, phv, thv))**2 for m in range(-2, 3))
check('5b', "Unsöld 定理 (l=2)", close(uns, 5/(4*math.pi)))
w0, hM, eps = 1.0, 0.1, 0.02; gam = 2*w0 + eps; Tp = 2*math.pi/gam
sol = integrate.solve_ivp(lambda tt_, Y: [Y[1], -w0**2*(1 + hM*math.cos(gam*tt_))*Y[0], Y[3], -w0**2*(1 + hM*math.cos(gam*tt_))*Y[2]], [0, Tp], [1, 0, 0, 1], rtol=1e-12, atol=1e-12)
Mon = np.array([[sol.y[0, -1], sol.y[2, -1]], [sol.y[1, -1], sol.y[3, -1]]]); sF = math.log(max(abs(np.linalg.eigvals(Mon))))/Tp
check('5b', "Mathieu 参数共振增长率", abs(sF - 0.5*math.sqrt((hM*w0/2)**2 - eps**2)) < 0.1*0.5*math.sqrt((hM*w0/2)**2 - eps**2), f"{sF:.5f} vs {0.5*math.sqrt((hM*w0/2)**2-eps**2):.5f}")
ai_p = special.airy(6.0)[0]; ai_m = special.airy(-6.0)[0]
check('5b', "Airy 渐近与零点", abs(ai_p/(math.exp(-2/3*6**1.5)/(2*math.sqrt(math.pi)*6**0.25)) - 1) < 0.02 and abs(ai_m - math.sin(2/3*6**1.5 + math.pi/4)/(math.sqrt(math.pi)*6**0.25)) < 0.01
      and np.allclose(special.ai_zeros(2)[0], [-2.3381, -4.0879], atol=1e-4))
muV = 20.0
vdp = integrate.solve_ivp(lambda tt_, Y: [Y[1], muV*(1 - Y[0]**2)*Y[1] - Y[0]], [0, 400], [2, 0], rtol=1e-9, atol=1e-9, dense_output=True, max_step=0.05)
tz = [vdp.t[i] for i in range(1, len(vdp.t)) if vdp.y[0, i - 1] < 0 <= vdp.y[0, i] and vdp.t[i] > 100]
check('5b', "Van der Pol 张弛周期 ≈ (3-2ln2)μ (μ=20, 10%)", abs(np.mean(np.diff(tz))/((3 - 2*math.log(2))*muV) - 1) < 0.1, f"{np.mean(np.diff(tz)):.2f} vs {(3-2*math.log(2))*muV:.2f}")
Ast = np.array([[-1, 2], [-3, -0.5]]); Pl = linalg.solve_continuous_lyapunov(Ast.T, -np.eye(2))
check('5b', "Lyapunov 方程解正定", np.all(np.linalg.eigvalsh((Pl + Pl.T)/2) > 0))

# ---------- 05c PDE、渐近与优化 ----------
z01 = special.jn_zeros(0, 2); z11 = special.jn_zeros(1, 1)[0]; z21 = special.jn_zeros(2, 1)[0]
check('5c', "圆膜频率比 1.593, 2.136, 2.295", np.allclose([z11/z01[0], z21/z01[0], z01[1]/z01[0]], [1.593, 2.136, 2.295], atol=1e-3))
xL, hP = sp.symbols('x h', positive=True); nI = sp.symbols('n', integer=True, positive=True)
u0 = sp.Piecewise((2*hP*xL, xL <= sp.Rational(1, 2)), (2*hP*(1 - xL), True))
bn = [sp.simplify(2*sp.integrate(u0*sp.sin(k*sp.pi*xL), (xL, 0, 1))) for k in range(1, 6)]
check('5c', "拨弦系数 8h sin(nπ/2)/(n²π²)", all(sp.simplify(bn[k - 1] - 8*hP*sp.sin(k*sp.pi/2)/(k**2*sp.pi**2)) == 0 for k in range(1, 6)))
xv_, yv_ = 0.4, 0.9; uh = integrate.quad(lambda s_: yv_/math.pi/((xv_ - s_)**2 + yv_**2), 0, np.inf)[0]
check('5c', "半平面 Poisson 例: 1-θ/π", close(uh, 1 - math.atan2(yv_, xv_)/math.pi, 1e-8))
ep, A = 0.05, 1.0
duff = integrate.solve_ivp(lambda tt_, Y: [Y[1], -Y[0] - ep*Y[0]**3], [0, 200], [A, 0], rtol=1e-11, atol=1e-11, max_step=0.05)
tz = [duff.t[i] for i in range(1, len(duff.t)) if duff.y[1, i - 1] > 0 >= duff.y[1, i]]
check('5c', "Duffing 频移 1+3εA²/8", abs(2*math.pi/np.mean(np.diff(tz)) - (1 + 3/8*ep*A**2)) < ep**2 and abs(2*math.pi/np.mean(np.diff(tz)) - (1 + 3/8*ep*A**2 - 21/256*ep**2*A**4)) < 2e-5, f"{2*math.pi/np.mean(np.diff(tz)):.5f}")
vp = integrate.solve_ivp(lambda tt_, Y: [Y[1], -Y[0] + 0.05*(1 - Y[0]**2)*Y[1]], [0, 600], [0.5, 0], rtol=1e-9, max_step=0.1)
check('5c', "Van der Pol 弱非线性振幅 → 2", abs(np.max(np.abs(vp.y[0, vp.t > 500])) - 2) < 0.02)
def shoot(lmb):
    s_ = integrate.solve_ivp(lambda xx, Y: [Y[1], -lmb**2*(1 + xx)**2*Y[0]], [0, 1], [0, 1], rtol=1e-10, atol=1e-12)
    return s_.y[0, -1]
l5 = optimize.brentq(shoot, 5*math.pi/1.5 - 1, 5*math.pi/1.5 + 1)
check('5c', "WKB 本征值 nπ/∫√q (n=5)", abs(l5/(5*math.pi/1.5) - 1) < 0.01, f"{l5:.4f} vs {5*math.pi/1.5:.4f}")
xe = 4.0
check('5c', "erfc 渐近三项", abs(special.erfc(xe)/(math.exp(-xe**2)/(xe*math.sqrt(math.pi))*(1 - 1/(2*xe**2) + 3/(4*xe**4))) - 1) < 2e-3)
from scipy.optimize import linprog
cL = np.array([3, 5]); AL = np.array([[1, 0], [0, 2], [3, 2]]); bL = np.array([4, 12, 18])
pr = linprog(-cL, A_ub=AL, b_ub=bL); du = linprog(bL, A_ub=-AL.T, b_ub=-cL)
check('5c', "LP 强对偶 (Wyndor 例 36)", close(-pr.fun, du.fun, 1e-8) and close(-pr.fun, 36, 1e-8))
yC = sp.symbols('y', positive=True); xC = sp.symbols('x', real=True)
check('5c', "凸共轭 e^x ↔ y ln y - y", sp.simplify((xC*yC - sp.exp(xC)).subs(xC, sp.log(yC)) - (yC*sp.log(yC) - yC)) == 0)
xA = 0.8; fA = lambda tt_: 2*math.sqrt(tt_)    # φ=1 的 Abel 变换
inner = lambda X: integrate.quad(lambda tt_: fA(tt_)/math.sqrt(X - tt_), 0, X)[0]
check('5c', "Abel 反演公式 (φ=1)", abs((inner(xA + 1e-4) - inner(xA - 1e-4))/2e-4/math.pi - 1) < 1e-4)
aC = 1.0
def tautochrone(th0):
    return integrate.quad(lambda th_: math.sqrt(aC*(1 - math.cos(th_))*2/9.8/(math.cos(th0) - math.cos(th_)))/1, th0, math.pi, limit=200)[0] if False else integrate.quad(lambda th_: math.sqrt(2*aC/9.8)*math.sin(th_/2)/math.sqrt(math.cos(th0) - math.cos(th_)), th0, math.pi, limit=200)[0]
ts = [tautochrone(th0) for th0 in (0.3, 1.0, 2.0)]
check('5c', "摆线等时: 下滑时间与起点无关", max(ts) - min(ts) < 1e-6 and close(ts[0], math.pi*math.sqrt(aC/9.8), 1e-6))

npass = sum(r[2] for r in R); print(f"\n续写数学(二): {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
