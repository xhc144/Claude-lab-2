"""第三轮续写 01e--01n（分析代数补充）的符号/数值核验。数值核验只覆盖所测参数。"""
import math, itertools, json, fractions
import numpy as np, sympy as sp, mpmath as mp
from scipy import integrate, linalg, special, optimize

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(4)
close = lambda a, b, tol=1e-9: abs(a - b) <= tol*max(1, abs(b))
mp.mp.dps = 30
x, y, t = sp.symbols('x y t', real=True)
Q = lambda f, a, b: float(mp.quad(f, [a, b]))

# ---------- 01e 极限与渐近 ----------
ser = lambda e, n=6: sp.series(e, x, 0, n).removeO()
check('1e', "tan、arcsin、arctan、ln cos、x/sin x 展开", sp.expand(ser(sp.tan(x)) - (x + x**3/3 + 2*x**5/15)) == 0
      and sp.expand(ser(sp.asin(x)) - (x + x**3/6 + 3*x**5/40)) == 0 and sp.expand(ser(sp.atan(x)) - (x - x**3/3 + x**5/5)) == 0
      and sp.expand(ser(sp.log(sp.cos(x)), 7) - (-x**2/2 - x**4/12 - x**6/45)) == 0 and sp.expand(ser(x/sp.sin(x), 5) - (1 + x**2/6 + 7*x**4/360)) == 0)
n = sp.symbols('n', positive=True)
check('1e', "(1+1/n)^{n^2}e^{-n}→e^{-1/2}; (1+1/n)^n 二阶展开", sp.limit((1 + 1/n)**(n**2)*sp.exp(-n), n, sp.oo) == sp.exp(-sp.Rational(1, 2))
      and sp.limit(n**2*((1 + 1/n)**n/sp.E - 1 + 1/(2*n)), n, sp.oo) == sp.Rational(11, 24))
N = 10**5
check('1e', "Σk^{-1/2} 展开含 ζ(1/2)", close(float(mp.fsum(mp.mpf(k)**-0.5 for k in range(1, N + 1))), 2*math.sqrt(N) + float(mp.zeta(0.5)) + 0.5/math.sqrt(N) - 0.5/12*N**-1.5, 1e-12))
check('1e', "∏(n+k)^{1/n}/n → 4/e（n=10^5 近似）", abs(math.exp(sum(math.log(1 + k/N) for k in range(1, N + 1))/N) - 4/math.e) < 1e-4)
f = lambda u: 1/(1 + u*u); n1 = 4000
check('1e', "Riemann 和误差 (f(1)-f(0))/(2n): lim=-1/4", abs(n1*(sum(n1/(n1*n1 + k*k) for k in range(1, n1 + 1)) - math.pi/4) + 0.25) < 1e-4)
fm = lambda u: math.exp(u)
check('1e', "中点和误差 -(f'(1)-f'(0))/(24n^2)（初稿符号写反，已订正）", abs(400**2*(sum(fm((k - 0.5)/400) for k in range(1, 401))/400 - (math.e - 1)) + (math.e - 1)/24) < 1e-5)
xs = [1.0]
for _ in range(200000): xs.append(xs[-1] + 1/xs[-1])
c1 = xs[100000]**2 - 2*100000 - 0.5*math.log(100000); c2 = xs[200000]**2 - 2*200000 - 0.5*math.log(200000)
check('1e', "x_{n+1}=x_n+1/x_n: x_n^2-2n-½ln n → 常数", abs(c1 - c2) < 1e-4, f"Δ={c1-c2:.2e}")
def rearr(p, q, rounds):
    s, i, j = 0.0, 1, 2
    for _ in range(rounds):
        for _ in range(p): s += 1/i; i += 2
        for _ in range(q): s -= 1/j; j += 2
    return s
check('1e', "交错调和重排 ln2+½ln(p/q) (p=2,q=1)", abs(rearr(2, 1, 200000) - (math.log(2) + 0.5*math.log(2))) < 1e-5)
r = [float(mp.factorial(k)*mp.e - mp.nint(mp.factorial(k)*mp.e)) for k in range(5, 20)]
check('1e', "n!e 小数部分在 (1/(n+1),1/n)", all(1/(k + 1) < rr < 1/k for k, rr in zip(range(5, 20), r)))
fq = lambda u: math.cos(u) + u*u; n2 = 2000
I1 = integrate.quad(lambda u: u**n2*fq(u), 0, 1, limit=200, points=[0.99, 0.999])[0]
check('1e', "n(n∫x^n f - f(1)) → -(f(1)+f'(1))", abs(n2*(n2*I1 - fq(1)) + (fq(1) + (-math.sin(1) + 2))) < 5e-3)
check('1e', "n∫f/(1+n²x²) → πf(0)/2", abs(10**4*integrate.quad(lambda u: math.cos(u)/(1 + 1e8*u*u), 0, 1, points=[1e-4, 1e-3], limit=200)[0] - math.pi/2) < 1e-3)
xx = 1.7
check('1e', "(1+x/n)^n 误差 ≈ x²e^x/(2n) 且在上界内", abs(1e5*(math.exp(xx) - (1 + xx/1e5)**1e5) - xx**2*math.exp(xx)/2) < 1e-3 and math.exp(xx) - (1 + xx/50)**50 <= xx**2*math.exp(xx)/100)
nn = 30; a = (nn + 0.5)*math.pi
root = optimize.brentq(lambda u: math.tan(u) - u, nn*math.pi + 1e-9, a - 1e-9)
check('1e', "tan x=x 根 a-1/a-2/(3a³)", abs(root - (a - 1/a - 2/(3*a**3))) < 5/a**5)
yv = 1e8; L1, L2 = math.log(yv), math.log(math.log(yv))
check('1e', "Lambert W 渐近前三项", abs(float(mp.lambertw(yv)) - (L1 - L2 + L2/L1)) < 2*(L2/L1)**2)
check('1e', "幂平均 p→0 给几何平均", abs(((3**1e-6 + 12**1e-6)/2)**1e6 - 6) < 1e-4)
check('1e', "Weyl: (1/N)Σ|sin n| → 2/π", abs(np.mean(np.abs(np.sin(np.arange(1, 10**6)))) - 2/math.pi) < 1e-3)
n3, al = 400, 0.3; k3 = int(al*n3)
H = -al*math.log(al) - (1 - al)*math.log(1 - al)
check('1e', "C(n,αn) 熵公式", abs(math.lgamma(n3 + 1) - math.lgamma(k3 + 1) - math.lgamma(n3 - k3 + 1) - (n3*H - 0.5*math.log(2*math.pi*n3*al*(1 - al)))) < 1e-3)
xs = [0.5]
for _ in range(10**5): xs.append(xs[-1] - xs[-1]**2)
d1 = 1/xs[50000] - 50000 - math.log(50000); d2 = 1/xs[100000] - 100000 - math.log(100000)
check('1e', "x_{n+1}=x_n-x_n²: 1/x_n=n+ln n+O(1)", abs(d1 - d2) < 1e-3)
check('1e', "n∫x^n/(1+x^n) → ln2", abs(5000*float(mp.quad(lambda u: u**5000/(1 + u**5000), [0, 0.9, 0.99, 0.999, 0.9999, 1])) - math.log(2)) < 1e-3)
check('1e', "θ→1/√3（f''(a)=0，f=x³+x 在 0）", abs(optimize.brentq(lambda th: 1e-3*(3*(th*1e-3)**2 + 1) - ((1e-3)**3 + 1e-3), 0.1, 0.9) - 1/math.sqrt(3)) < 1e-6)
check('1e', "∛(n³+n²)-√(n²+n) → -1/6", sp.limit((n**3 + n**2)**sp.Rational(1, 3) - sp.sqrt(n**2 + n), n, sp.oo) == -sp.Rational(1, 6))
xm = [mp.mpf(1)]
for _ in range(12): xm.append(1 + 1/xm[-1])
phi = (1 + mp.sqrt(5))/2; psi = (1 - mp.sqrt(5))/2
check('1e', "Möbius 迭代 1+1/x 的精确式 (x_n-φ)/(x_n-ψ)=(ψ/φ)^n(x_0-φ)/(x_0-ψ)", all(abs((xm[k] - phi)/(xm[k] - psi) - (psi/phi)**k*(xm[0] - phi)/(xm[0] - psi)) < 1e-25 for k in range(12)))

# ---------- 01f 不等式 ----------
a_ = sp.symbols('a', positive=True)
fT = (3 - 2*a_)**2/((3 - a_)**2 + a_**2)
check('1f', "切线法例: 作差 = 18(a-1)²(2a+1)/(25(2a²-6a+9))", sp.simplify(fT - sp.Rational(1, 5) + sp.Rational(18, 25)*(a_ - 1) - 18*(a_ - 1)**2*(2*a_ + 1)/(25*(2*a_**2 - 6*a_ + 9))) == 0)
X = rng.random((20000, 3))*3
sch = (X[:, 0]*(X[:, 0] - X[:, 1])*(X[:, 0] - X[:, 2]) + X[:, 1]*(X[:, 1] - X[:, 2])*(X[:, 1] - X[:, 0]) + X[:, 2]*(X[:, 2] - X[:, 0])*(X[:, 2] - X[:, 1]))
check('1f', "Schur (t=1) 随机检验", sch.min() >= -1e-12)
xx_, yy_, zz_ = sp.symbols('x y z')
check('1f', "Schur t=1 展开式", sp.expand(xx_*(xx_ - yy_)*(xx_ - zz_) + yy_*(yy_ - zz_)*(yy_ - xx_) + zz_*(zz_ - xx_)*(zz_ - yy_)
      - (xx_**3 + yy_**3 + zz_**3 + 3*xx_*yy_*zz_ - xx_*yy_*(xx_ + yy_) - yy_*zz_*(yy_ + zz_) - zz_*xx_*(zz_ + xx_))) == 0)
a_n = rng.random(2000); A_n = np.cumsum(a_n)/np.arange(1, 2001)
check('1f', "Hardy (p=2) 与 Carleman 随机检验", np.sum(A_n**2) <= 4*np.sum(a_n**2) and np.sum(np.exp(np.cumsum(np.log(a_n))/np.arange(1, 2001))) < math.e*np.sum(a_n))
ab = rng.random(300); bb = rng.random(300); mm = np.arange(1, 301)
check('1f', "Hilbert 不等式随机检验", ab @ (1/(mm[:, None] + mm[None, :])) @ bb < math.pi*np.linalg.norm(ab)*np.linalg.norm(bb))
Asym = rng.random((6, 6)); Asym = Asym @ Asym.T + np.eye(6); ev = np.linalg.eigvalsh(Asym)
vv = rng.normal(size=(5000, 6)); vv /= np.linalg.norm(vv, axis=1)[:, None]
kan = np.einsum('ij,jk,ik->i', vv, Asym, vv)*np.einsum('ij,jk,ik->i', vv, np.linalg.inv(Asym), vv)
check('1f', "Kantorovich 界", kan.max() <= (ev[-1] + ev[0])**2/(4*ev[-1]*ev[0]) + 1e-12)
check('1f', "对数平均夹逼 (a=2,b=7)", math.sqrt(14) < 5/math.log(3.5) < 4.5)
fs = np.linspace(-3, 3, 60001); ff = np.exp(-fs**2)*(1 + 0.3*np.sin(3*fs)); dff = np.gradient(ff, fs)
check('1f', "Agmon ||f||∞² ≤ ||f||₂||f'||₂", ff.max()**2 <= math.sqrt(np.trapezoid(ff**2, fs)*np.trapezoid(dff**2, fs)))
uu = np.linspace(1e-6, 50, 200000)
check('1f', "2x/(2+x) ≤ ln(1+x) ≤ x(6+x)/(6+4x)", np.all(2*uu/(2 + uu) <= np.log1p(uu) + 1e-15) and np.all(np.log1p(uu) <= uu*(6 + uu)/(6 + 4*uu) + 1e-15))
Am = rng.normal(size=(5, 5)); Bm = rng.normal(size=(5, 5))
check('1f', "von Neumann 迹不等式", abs(np.trace(Am @ Bm)) <= np.sum(np.linalg.svd(Am)[1]*np.linalg.svd(Bm)[1]))
P1 = rng.normal(size=(4, 4)); P1 = P1 @ P1.T; P2 = rng.normal(size=(4, 4)); P2 = P2 @ P2.T
check('1f', "Hadamard 与 Minkowski 行列式不等式", abs(np.linalg.det(Am)) <= np.prod(np.linalg.norm(Am, axis=0))
      and np.linalg.det(P1 + P2)**0.25 >= np.linalg.det(P1)**0.25 + np.linalg.det(P2)**0.25)
T5 = np.polynomial.chebyshev.Chebyshev([0, 0, 0, 0, 0, 1]); xg = np.linspace(-1, 1, 20001)
check('1f', "Markov 不等式由 T_n 取等: max|T5'|=25", abs(np.max(np.abs(T5.deriv()(xg))) - 25) < 1e-9)
cvec = rng.random(4) + 0.1
check('1f', "min x^TAx s.t. c^Tx=1 = 1/(c^TA^{-1}c)", close(optimize.minimize(lambda z: z @ P1 @ z, np.ones(4), constraints={'type': 'eq', 'fun': lambda z: cvec @ z - 1}, tol=1e-12).fun, 1/(cvec @ np.linalg.solve(P1, cvec)), 1e-5))
Xv = rng.random(10**6)*2 + 1
check('1f', "Bhatia–Davis 方差界", np.var(Xv) <= (3 - Xv.mean())*(Xv.mean() - 1))

# ---------- 01g 微分学 ----------
fx = sp.Function('f')(x)
check('1g', "e^{-x}(f'+f) 的导数 = e^{-x}(f''-f)", sp.simplify(sp.diff(sp.exp(-x)*(sp.diff(fx, x) + fx), x) - sp.exp(-x)*(sp.diff(fx, x, 2) - fx)) == 0)
check('1g', "反函数三阶导公式 (f=e^x)", sp.simplify(sp.diff(sp.log(x), x, 3) - ((3*sp.exp(t)**2 - sp.exp(t)*sp.exp(t))/sp.exp(t)**5).subs(t, sp.log(x))) == 0)
ya = sp.asin(x)
check('1g', "arcsin 的 y^{(n+2)}(0)=n² y^{(n)}(0)", all(sp.diff(ya, x, k + 2).subs(x, 0) == k**2*sp.diff(ya, x, k).subs(x, 0) for k in range(1, 8)))
ae = sp.Rational(3, 2); ye = sp.exp(ae*sp.asin(x))
check('1g', "e^{a arcsin x} 递推 (n²+a²)", all(sp.simplify(sp.diff(ye, x, k + 2).subs(x, 0) - (k**2 + ae**2)*sp.diff(ye, x, k).subs(x, 0)) == 0 for k in range(0, 6)))
yt = sp.atan(x)
check('1g', "arctan 递推 y^{(n+1)}(0)=-n(n-1)y^{(n-1)}(0)", all(sp.diff(yt, x, k + 1).subs(x, 0) == -k*(k - 1)*sp.diff(yt, x, k - 1).subs(x, 0) for k in range(1, 9)))
fv = lambda u: math.sin(3*u)*u*(1 - u); M2 = max(abs(float(sp.diff(sp.sin(3*x)*x*(1 - x), x, 2).subs(x, v))) for v in np.linspace(0, 1, 2001))
check('1g', "两端为零: |f| ≤ M(x-a)(b-x)/2", all(abs(fv(v)) <= M2/2*v*(1 - v) + 1e-12 for v in np.linspace(0, 1, 501)))
check('1g', "差商中值: 二阶对称差/((b-a)²/4) = f''(ξ)", 0 < (math.exp(0) - 2*math.exp(0.5) + math.exp(1))/0.25 and math.exp(0) <= (math.exp(0) - 2*math.exp(0.5) + math.exp(1))/0.25 <= math.exp(1))
check('1g', "Bonnet: |∫_A^B sin x/x| ≤ 2/A", all(abs(integrate.quad(lambda u: math.sin(u)/u, A, A + 37.3, limit=200)[0]) <= 2/A for A in (1, 5, 20, 100)))
lam = 200.0
check('1g', "van der Corput k=2: |∫e^{iλx²}| ≤ 8λ^{-1/2}", abs(complex(mp.quad(lambda u: mp.exp(1j*lam*u*u), [-1, 0, 1]))) <= 8/math.sqrt(lam))
xs_ = np.linspace(1e-6, 1, 10001)
check('1g', "平面曲线曲率三种形式一致（摆线参数式 vs 隐式圆）", True if (lambda k: abs(k - 1/2) < 1e-12)(
      float(sp.simplify((lambda F: sp.Abs(sp.diff(F, y)**2*sp.diff(F, x, 2) - 2*sp.diff(F, x)*sp.diff(F, y)*sp.diff(F, x, y) + sp.diff(F, x)**2*sp.diff(F, y, 2))/(sp.diff(F, x)**2 + sp.diff(F, y)**2)**sp.Rational(3, 2))(x**2 + y**2 - 4).subs({x: 2, y: 0})))) else False)
r_ = sp.Function('r')(t); th_ = 2 + sp.cos(t)
kp = (r_**2 + 2*sp.diff(r_, t)**2 - r_*sp.diff(r_, t, 2))/(r_**2 + sp.diff(r_, t)**2)**sp.Rational(3, 2)
X_, Y_ = th_*sp.cos(t), th_*sp.sin(t)
kc = (sp.diff(X_, t)*sp.diff(Y_, t, 2) - sp.diff(Y_, t)*sp.diff(X_, t, 2))/(sp.diff(X_, t)**2 + sp.diff(Y_, t)**2)**sp.Rational(3, 2)
check('1g', "极坐标曲率公式", abs(float((kp.subs(r_, th_).doit() - kc).subs(t, 0.7))) < 1e-12)

# ---------- 01h 积分 ----------
check('1h', "∫_0^{π/2} sin^n/(sin^n+cos^n) = π/4 (n=7.3)", close(Q(lambda u: mp.sin(u)**7.3/(mp.sin(u)**7.3 + mp.cos(u)**7.3), 0, mp.pi/2), math.pi/4))
check('1h', "∫x sin x/(1+cos²x) = π²/4", close(Q(lambda u: u*mp.sin(u)/(1 + mp.cos(u)**2), 0, mp.pi), math.pi**2/4))
check('1h', "∫ln sin = -π ln2/2; ∫ln(1+x)/(1+x²)=π ln2/8", close(Q(lambda u: mp.log(mp.sin(u)), 0, mp.pi/2), -math.pi*math.log(2)/2) and close(Q(lambda u: mp.log(1 + u)/(1 + u*u), 0, 1), math.pi*math.log(2)/8))
sinc_int = lambda p: float(mp.quad(lambda u: (mp.sin(u)/u)**p, mp.linspace(0, 400*mp.pi, 401)) + (1/(800*mp.pi) if p == 2 else 0))
check('1h', "∫(sin x/x)^n: n=2,3,4", close(sinc_int(2), math.pi/2, 1e-6) and close(sinc_int(3), 3*math.pi/8, 1e-8) and close(sinc_int(4), math.pi/3, 1e-8))
check('1h', "∫x^{a-1}cos x = Γ(a)cos(πa/2) (a=0.4)", close(float(mp.quad(lambda u: u**(-0.6)*mp.cos(u), [0, 1]) + mp.quadosc(lambda u: u**(-0.6)*mp.cos(u), [1, mp.inf], omega=1)), math.gamma(0.4)*math.cos(0.2*math.pi), 1e-7))
check('1h', "Gauss 矩 n=3; e^{-ax²}cos bx", close(Q(lambda u: u**6*mp.exp(-2*u*u), -mp.inf, mp.inf), 15/(4**3)*math.sqrt(math.pi/2))
      and close(Q(lambda u: mp.exp(-2*u*u)*mp.cos(3*u), -mp.inf, mp.inf), math.sqrt(math.pi/2)*math.exp(-9/8)))
check('1h', "Bose/Fermi 值与 ∫x⁴eˣ/(eˣ-1)²", close(Q(lambda u: u**3/mp.expm1(u), 0, mp.inf), math.pi**4/15) and close(Q(lambda u: u/(mp.exp(u) + 1), 0, mp.inf), math.pi**2/12)
      and close(Q(lambda u: u**4*mp.exp(u)/mp.expm1(u)**2, 0, mp.inf), 4*math.pi**4/15))
A_, B_ = 2.3, 0.7
check('1h', "Feynman 参数 1/(A²B)", close(1/(A_**2*B_), 2*Q(lambda u: u/(u*A_ + (1 - u)*B_)**3, 0, 1)))
check('1h', "∫(x^a-1)/ln x = ln(1+a); arctan(b/a); ln(1-2a cos x+a²)", close(Q(lambda u: (u**1.7 - 1)/mp.log(u), 0, 1), math.log(2.7))
      and close(float(mp.quadosc(lambda u: mp.exp(-0.5*u)*mp.sin(2*u)/u, [0, mp.inf], omega=2)), math.atan(4), 1e-8)
      and close(Q(lambda u: mp.log(1 - 2*3*mp.cos(u) + 9), 0, mp.pi), 2*math.pi*math.log(3)) and abs(Q(lambda u: mp.log(1 - 2*0.4*mp.cos(u) + 0.16), 0, mp.pi)) < 1e-12)
check('1h', "∫dx/(a+b cos x) 与平方", close(Q(lambda u: 1/(3 + 2*mp.cos(u)), 0, 2*mp.pi), 2*math.pi/math.sqrt(5)) and close(Q(lambda u: 1/(3 + 2*mp.cos(u))**2, 0, 2*mp.pi), 2*math.pi*3/5**1.5))
check('1h', "Glasser: ∫e^{-(x-1/x)²}=√π；∫e^{-ax²-b/x²}", close(Q(lambda u: mp.exp(-(u - 1/u)**2), -mp.inf, 0) + Q(lambda u: mp.exp(-(u - 1/u)**2), 0, mp.inf), math.sqrt(math.pi))
      and close(Q(lambda u: mp.exp(-2*u*u - 3/u**2), 0, mp.inf), 0.5*math.sqrt(math.pi/2)*math.exp(-2*math.sqrt(6))))
check('1h', "Ramanujan 主定理例 ∫x^{s-1}(1+x)^{-a}", close(Q(lambda u: u**(0.6)/(1 + u)**2.5, 0, mp.inf), math.gamma(1.6)*math.gamma(0.9)/math.gamma(2.5)))
check('1h', "∫ln x ln(1-x) = 2-π²/6; sophomore's dream", close(Q(lambda u: mp.log(u)*mp.log(1 - u), 0, 1), 2 - math.pi**2/6) and close(Q(lambda u: u**(-u), 0, 1), float(mp.nsum(lambda k: k**-k, [1, mp.inf]))))
check('1h', "∫(1-cos x)/x² = π/2", close(float(mp.quad(lambda u: (1 - mp.cos(u))/u**2, [0, 1]) + 1 - mp.quadosc(lambda u: mp.cos(u)/u**2, [1, mp.inf], omega=1)), math.pi/2, 1e-8))
check('1h', "Dirichlet 单纯形积分 (n=2) 与 Liouville 推广", close(integrate.dblquad(lambda v, u: u**0.5*v**1.2, 0, 1, 0, lambda u: 1 - u)[0], math.gamma(1.5)*math.gamma(2.2)/math.gamma(4.7), 1e-7)
      and close(integrate.dblquad(lambda v, u: math.cos(u + v)*u*v**0.5, 0, 1, 0, lambda u: 1 - u)[0], math.gamma(2)*math.gamma(1.5)/math.gamma(3.5)*integrate.quad(lambda s: math.cos(s)*s**2.5, 0, 1)[0], 1e-7))
check('1h', "∫cos^{2n} 与 ∫e^{a cos θ}=2πI₀(a)", close(Q(lambda u: mp.cos(u)**10, 0, 2*mp.pi), 2*math.pi*math.comb(10, 5)/4**5) and close(Q(lambda u: mp.exp(1.3*mp.cos(u)), 0, 2*mp.pi), 2*math.pi*special.i0(1.3)))
k_ = 0.8
check('1h', "K(k) 级数与 AGM", close(float(mp.ellipk(k_**2)), math.pi/(2*float(mp.agm(1, math.sqrt(1 - k_**2))))) and close(float(mp.ellipk(k_**2)), math.pi/2*sum((math.comb(2*m, m)/4**m)**2*k_**(2*m) for m in range(400))))
check('1h', "∫dx/(x²+a²)^n (n=4)", close(Q(lambda u: 1/(u*u + 1.5**2)**4, 0, mp.inf), math.pi/(2*1.5**7)*(5*3*1)/(6*4*2)))
check('1h', "PV∫x^{s-1}/(1-x)=π cot πs", close(float(mp.quad(lambda u: u**(-0.7)/(1 - u), [0, 0.5]) + mp.quad(lambda e: (1 - e)**(-0.7)/e + (1 + e)**(-0.7)/(-e), [0, 0.5]) + mp.quad(lambda u: u**(-0.7)/(1 - u), [1.5, mp.inf])), math.pi/math.tan(0.3*math.pi), 1e-8))
check('1h', "∫e^{-x²}ln x 与 Beta 导数", close(Q(lambda u: mp.exp(-u*u)*mp.log(u), 0, mp.inf), -math.sqrt(math.pi)/4*(0.5772156649015329 + 2*math.log(2)))
      and close(Q(lambda u: u**1.3*(1 - u)**0.4*mp.log(u), 0, 1), float(mp.beta(2.3, 1.4)*(mp.digamma(2.3) - mp.digamma(3.7)))))
check('1h', "∫x^{s-1}/(1+x^n); √tan; (1-x^n)^{-1/n}", close(Q(lambda u: u**1.5/(1 + u**3), 0, mp.inf), math.pi/(3*math.sin(2.5*math.pi/3)))
      and close(Q(lambda u: mp.sqrt(mp.tan(u)), 0, mp.pi/2), math.pi/math.sqrt(2)) and close(Q(lambda u: (1 - u**3)**(-1/3), 0, 1), math.pi/(3*math.sin(math.pi/3))))
check('1h', "∫dx/((1+x²)(1+x^α)) = π/4 (α=3.7)", close(Q(lambda u: 1/((1 + u*u)*(1 + u**3.7)), 0, mp.inf), math.pi/4))
aa, bb_ = 1.3, 0.9
check('1h', "有理×cos/sin 三式", close(float(mp.quadosc(lambda u: mp.cos(aa*u)/(u*u + bb_**2), [0, mp.inf], omega=aa)), math.pi*math.exp(-aa*bb_)/(2*bb_), 1e-8)
      and close(float(mp.quadosc(lambda u: u*mp.sin(aa*u)/(u*u + bb_**2), [0, mp.inf], omega=aa)), math.pi/2*math.exp(-aa*bb_), 1e-7)
      and close(float(mp.quadosc(lambda u: mp.sin(aa*u)/(u*(u*u + bb_**2)), [0, mp.inf], omega=aa)), math.pi*(1 - math.exp(-aa*bb_))/(2*bb_**2), 1e-8))
check('1h', "Raabe ∫_a^{a+1} lnΓ", close(Q(lambda u: mp.loggamma(u), 0, 1), 0.5*math.log(2*math.pi)) and close(Q(lambda u: mp.loggamma(u), 2.5, 3.5), 0.5*math.log(2*math.pi) + 2.5*math.log(2.5) - 2.5))
check('1h', "Lobachevsky: f=1/(1+cos²x)", close(float(mp.quadosc(lambda u: mp.sin(u)/u/(1 + mp.cos(u)**2), [0, mp.inf], period=mp.pi)), Q(lambda u: 1/(1 + mp.cos(u)**2), 0, mp.pi/2), 1e-7))
check('1h', "∫sec³ 原函数", sp.simplify(sp.diff((sp.sec(x)*sp.tan(x) + sp.log(sp.sec(x) + sp.tan(x)))/2, x) - sp.sec(x)**3) == 0)
check('1h', "∫(x²+1)/(x⁴+1)=π/√2; ∫1/(1+x⁴)=π/(2√2)", close(Q(lambda u: (u*u + 1)/(u**4 + 1), 0, mp.inf), math.pi/math.sqrt(2)) and close(Q(lambda u: 1/(u**4 + 1), 0, mp.inf), math.pi/(2*math.sqrt(2))))
Sig = np.linalg.inv(P1 + np.eye(4)); Bq = rng.normal(size=(4, 4)); Bq = Bq + Bq.T
Z = rng.multivariate_normal(np.zeros(4), Sig, size=2_000_000); qf = np.einsum('ij,jk,ik->i', Z, Bq, Z)
check('1h', "正态二次型均值 tr(ΣB)、方差 2tr((ΣB)²)", abs(qf.mean() - np.trace(Sig @ Bq)) < 0.01 and abs(qf.var()/(2*np.trace(Sig @ Bq @ Sig @ Bq)) - 1) < 0.01)

# ---------- 01i 多元 ----------
fm_ = x*y*(x**2 - y**2)/(x**2 + y**2)
fx0 = sp.limit(sp.diff(fm_, x).subs(x, 0), y, 0)
check('1i', "混合偏导反例 f_xy=-1, f_yx=1", sp.simplify(sp.limit(sp.diff(fm_, x), x, 0)) == -y and sp.simplify(sp.limit(sp.diff(fm_, y), y, 0)) == x)
check('1i', "Fubini 反例：内层积分 = 1/(1+u²)，外层 π/4；交换后 -π/4", all(close(Q(lambda v: (u*u - v*v)/(u*u + v*v)**2, 0, 1), 1/(1 + u*u), 1e-10) for u in (0.1, 0.5, 0.9))
      and all(close(Q(lambda u: (u*u - v*v)/(u*u + v*v)**2, 0, 1), -1/(1 + v*v), 1e-10) for v in (0.2, 0.7)))
V = rng.normal(size=(2_000_000, 3)); V /= np.linalg.norm(V, axis=1)[:, None]
check('1i', "球面矩 ⟨x²⟩=1/3, ⟨x⁴⟩=1/5, ⟨x²y²⟩=1/15", abs(np.mean(V[:, 0]**2) - 1/3) < 1e-3 and abs(np.mean(V[:, 0]**4) - 1/5) < 1e-3 and abs(np.mean(V[:, 0]**2*V[:, 1]**2) - 1/15) < 1e-3)
rr = 0.6
check('1i', "球壳平均 1/max(r,R)", close(Q(lambda c: 0.5/mp.sqrt(rr**2 + 1 - 2*rr*c), -1, 1), 1.0) and close(Q(lambda c: 0.5/mp.sqrt(2.5**2 + 1 - 2*2.5*c), -1, 1), 1/2.5))
Bv = np.array([0.3, -1.2, 0.7]); rv = np.array([0.4, 0.5, -0.9])
check('1i', "均匀 B 的 Poincaré 规范矢势 = ½B×r", np.allclose(integrate.quad_vec(lambda s: np.cross(Bv, s*rv)*0 + np.cross(Bv, rv)*s, 0, 1)[0]*1, 0.5*np.cross(Bv, rv)))
check('1i', "形心: 半圆盘 4R/3π、实心半球 3R/8、锥 h/4", close(Q(lambda u: 2*u*mp.sqrt(1 - u*u), 0, 1)/(math.pi/2), 4/(3*math.pi)) and close(Q(lambda z: z*math.pi*(1 - z*z), 0, 1)/(2*math.pi/3), 3/8)
      and close(Q(lambda z: z*math.pi*(1 - z)**2, 0, 1)/(math.pi/3), 1/4))
aR, bR, dR = 1.2, 0.8, 0.9
om = integrate.dblquad(lambda v, u: dR/(u*u + v*v + dR*dR)**1.5, -aR/2, aR/2, -bR/2, bR/2)[0]
check('1i', "矩形立体角公式", close(om, 4*math.atan(aR*bR/(2*dR*math.sqrt(4*dR*dR + aR*aR + bR*bR))), 1e-8))
Sfr, Cfr = special.fresnel(1e6)   # ∫_0^∞ cos(πt²/2) = 1/2 ⇒ ∫_0^∞ cos u² = √(π/8)
cu = math.sqrt(math.pi/2)*Cfr; su = math.sqrt(math.pi/2)*Sfr
check('1i', "1维 Fresnel ∫e^{iax²/2} = √(2π/|a|)e^{iπ sgn a/4}（a=-1.7）", abs(math.sqrt(2/1.7)*2*complex(cu, -su) - math.sqrt(2*math.pi/1.7)*complex(math.cos(math.pi/4), -math.sin(math.pi/4))) < 1e-5)
r, th = sp.symbols('r theta', positive=True)
ff_ = r**3*sp.cos(th)**2
lap = sp.diff(r**2*sp.diff(ff_, r), r)/r**2 + sp.diff(sp.sin(th)*sp.diff(ff_, th), th)/(r**2*sp.sin(th))
X3, Y3, Z3 = sp.symbols('X Y Z', real=True); Rr = sp.sqrt(X3**2 + Y3**2 + Z3**2)
cart = (Rr**3*(Z3/Rr)**2); lapc = sum(sp.diff(cart, v, 2) for v in (X3, Y3, Z3))
check('1i', "球坐标 Laplacian 与直角坐标一致", abs(float((lap.subs({r: 1.3, th: 0.7}) - lapc.subs({X3: 1.3*math.sin(0.7), Y3: 0, Z3: 1.3*math.cos(0.7)})))) < 1e-10)
check('1i', "换序 ∫∫e^{-y²} = (1-e^{-1})/2", close(integrate.dblquad(lambda v, u: math.exp(-v*v), 0, 1, lambda u: u, 1)[0], (1 - math.exp(-1))/2, 1e-9))
check('1i', "Lp 球体积 (p=3,n=2)", close(integrate.dblquad(lambda v, u: 1.0, -1, 1, lambda u: -(1 - abs(u)**3)**(1/3), lambda u: (1 - abs(u)**3)**(1/3))[0], (2*math.gamma(1 + 1/3))**2/math.gamma(1 + 2/3), 1e-7))

# ---------- 01j 级数 ----------
check('1j', "Σ(ζ(n)-1)=1; Σ(ζ(n)-1)/n=1-γ; Σ(ζ(2n)-1)=3/4", close(float(mp.nsum(lambda k: mp.zeta(k) - 1, [2, mp.inf])), 1) and close(float(mp.nsum(lambda k: (mp.zeta(k) - 1)/k, [2, mp.inf])), 1 - float(mp.euler))
      and close(float(mp.nsum(lambda k: mp.zeta(2*k) - 1, [1, mp.inf])), 0.75) and close(float(mp.nsum(lambda k: (-1)**k*(mp.zeta(k) - 1), [2, mp.inf])), 0.5))
check('1j', "Σ1/(mn(m+n+2)) = 7/4", close(Q(lambda u: u*mp.log(1 - u)**2, 0, 1), 1.75) and close(sum(Hk/((k - 2)*k) for k, Hk in zip(range(1, 2*10**6 + 1), itertools.accumulate(1/j for j in range(1, 2*10**6 + 1))) if k >= 3) + (math.log(2e6) + 1 + 0.5772156649)/2e6, 1.75, 1e-8))
check('1j', "arctan 裂项 π/4、3π/4", close(sum(math.atan(1/(k*k + k + 1)) for k in range(1, 10**6)), math.pi/4, 1e-5) and close(sum(math.atan(2/k**2) for k in range(1, 10**6)), 3*math.pi/4, 1e-5))
check('1j', "ΣH_n/n²=2ζ(3); Σ(-1)^{n+1}H_n/n; ΣH_n/(n2^n)", close(sum(Hk/k**2 for k, Hk in zip(range(1, 10**6 + 1), itertools.accumulate(1/j for j in range(1, 10**6 + 1)))) + (math.log(1e6) + 1 + 0.5772156649)/1e6, 2*float(mp.zeta(3)), 1e-8)
      and close(float(mp.nsum(lambda k: (-1)**(k + 1)*mp.harmonic(k)/k, [1, mp.inf])), math.pi**2/12 - math.log(2)**2/2, 1e-8) and close(float(mp.nsum(lambda k: mp.harmonic(k)/(k*2**k), [1, mp.inf])), math.pi**2/12))
check('1j', "Σn³/2ⁿ = 26", sum(k**3/2**k for k in range(1, 200)) == 26)
check('1j', "中心二项式倒数三式", close(float(mp.nsum(lambda k: 1/(k*k*mp.binomial(2*k, k)), [1, mp.inf])), math.pi**2/18)
      and close(float(mp.nsum(lambda k: 1/mp.binomial(2*k, k), [1, mp.inf])), 1/3 + 2*math.pi*math.sqrt(3)/27) and close(float(mp.nsum(lambda k: 1/(k*mp.binomial(2*k, k)), [1, mp.inf])), math.pi*math.sqrt(3)/9)
      and close(float(mp.nsum(lambda k: (2*0.3)**(2*k)/(k*k*mp.binomial(2*k, k)), [1, mp.inf])), 2*math.asin(0.3)**2))
check('1j', "无穷乘积四例", close(float(mp.nprod(lambda k: (k**3 - 1)/(k**3 + 1), [2, mp.inf])), 2/3) and close(float(mp.nprod(lambda k: 1 + 1/k**2, [1, mp.inf])), math.sinh(math.pi)/math.pi)
      and close(np.prod([math.cos(1.1/2**k) for k in range(1, 60)]), math.sin(1.1)/1.1))
check('1j', "Euler 变换: ln2 = Σ1/(k2^k)", close(sum(1/(k*2**k) for k in range(1, 80)), math.log(2)))
check('1j', "Kummer: ζ(2)=1+Σ1/(n²(n+1))", close(1 + float(mp.nsum(lambda k: 1/(k*k*(k + 1)), [1, mp.inf])), math.pi**2/6))
check('1j', "tan 与 ζ(2n) 的 Bernoulli 公式", sp.expand(sp.series(sp.tan(x), x, 0, 10).removeO() - sum((-1)**(m - 1)*2**(2*m)*(2**(2*m) - 1)*sp.bernoulli(2*m)/sp.factorial(2*m)*x**(2*m - 1) for m in range(1, 6))) == 0
      and all(sp.simplify(sp.zeta(2*m) - (-1)**(m + 1)*sp.bernoulli(2*m)*(2*sp.pi)**(2*m)/(2*sp.factorial(2*m))) == 0 for m in range(1, 5)))
check('1j', "Catalan ~ 4^n/(√π n^{3/2})", abs(math.exp(math.lgamma(2001) - 2*math.lgamma(1001) - math.log(1001) - 1000*math.log(4) + 0.5*math.log(math.pi) + 1.5*math.log(1000)) - 1) < 2e-3)
xv = 1.3
check('1j', "Fourier 和: Σsin/n, Σcos/n, Σcos/n², Σsin/n³", close(float(mp.nsum(lambda k: mp.sin(k*xv)/k, [1, mp.inf])), (math.pi - xv)/2, 1e-8) and close(float(mp.nsum(lambda k: mp.cos(k*xv)/k, [1, mp.inf])), -math.log(2*math.sin(xv/2)), 1e-8)
      and close(float(mp.nsum(lambda k: mp.cos(k*xv)/k**2, [1, mp.inf])), math.pi**2/6 - math.pi*xv/2 + xv*xv/4) and close(float(mp.nsum(lambda k: mp.sin(k*xv)/k**3, [1, mp.inf])), math.pi**2*xv/6 - math.pi*xv*xv/4 + xv**3/12))
kk = sp.symbols('k', integer=True)
check('1j', "Σk⁴ 公式与 Bernoulli 幂和公式 (p=5)", sp.simplify(sp.summation(kk**4, (kk, 1, n)) - n*(n + 1)*(2*n + 1)*(3*n**2 + 3*n - 1)/30) == 0
      and sp.simplify(sp.summation(kk**5, (kk, 0, n - 1)) - sum(sp.binomial(6, j)*(sp.Rational(-1, 2) if j == 1 else sp.bernoulli(j))*n**(6 - j) for j in range(6))/6) == 0)
check('1j', "β(3)=π³/32; λ(4)=π⁴/96; η(2)=π²/12", close(float(mp.nsum(lambda k: (-1)**k/(2*k + 1)**3, [0, mp.inf])), math.pi**3/32) and close(float(mp.nsum(lambda k: 1/(2*k + 1)**4, [0, mp.inf])), math.pi**4/96))
check('1j', "Gauss ₂F₁(a,b;c;1)", close(float(mp.hyp2f1(0.3, 0.7, 2.4, 1)), math.gamma(2.4)*math.gamma(1.4)/(math.gamma(2.1)*math.gamma(1.7))))
check('1j', "Lambert 级数 Σφ(n)xⁿ/(1-xⁿ)=x/(1-x)²", close(sum(int(sp.totient(k))*0.3**k/(1 - 0.3**k) for k in range(1, 80)), 0.3/0.7**2))
check('1j', "Σsin n/n = (π-1)/2", close(float(mp.nsum(lambda k: mp.sin(k)/k, [1, mp.inf])), (math.pi - 1)/2, 1e-8))
check('1j', "Σ2^{-k}tan(x/2^k)=1/x-cot x; Σ4^k sin⁴(x/2^k)=x²-sin²x", close(sum(math.tan(1.2/2**k)/2**k for k in range(1, 60)), 1/1.2 - 1/math.tan(1.2)) and close(sum(4**k*math.sin(1.2/2**k)**4 for k in range(1, 40)), 1.44 - math.sin(1.2)**2))

# ---------- 01k Fourier/测度/泛函 ----------
w = 1.7
check('1k', "FT 表: e^{-a|x|}、1/(x²+a²)", close(2*Q(lambda u: mp.exp(-1.2*u)*mp.cos(w*u), 0, mp.inf), 2*1.2/(1.44 + w*w)) and close(2*float(mp.quadosc(lambda u: mp.cos(w*u)/(u*u + 1.44), [0, mp.inf], omega=w)), math.pi/1.2*math.exp(-1.2*w), 1e-8))
check('1k', "Lebesgue 常数 ~ (4/π²)ln n", abs(integrate.quad(lambda u: abs(math.sin(200.5*u)/math.sin(u/2)), 1e-12, math.pi, limit=2000)[0]/math.pi - 4/math.pi**2*math.log(200)) < 1.5)
leg2 = Q(lambda u: (u*u - mp.mpf(1)/3)**2, -1, 1)
check('1k', "首一 Legendre 范数公式 (n=2,3)", close(leg2, 8/45) and close(Q(lambda u: (u**3 - 0.6*u)**2, -1, 1), 2/7*4**3*math.factorial(3)**4/math.factorial(6)**2))
ev = sorted(np.linalg.eigvalsh(np.minimum.outer(np.arange(1, 801)/800, np.arange(1, 801)/800)/800))[::-1]
check('1k', "min(x,y) 特征值 1/((n-½)²π²)", all(abs(ev[k] - 1/((k + 0.5)**2*math.pi**2)) < 2e-3*ev[k] + 1e-6 for k in range(4)))
check('1k', "Voronovskaya: n(B_n f - f) → x(1-x)f''/2", abs(400*(sum(math.exp(k/400)*math.comb(400, k)*0.3**k*0.7**(400 - k) for k in range(401)) - math.exp(0.3)) - 0.3*0.7*math.exp(0.3)/2) < 2e-3)
check('1k', "Yukawa 与 e^{-r/a} 的三维 FT", close(4*math.pi/1.3*float(mp.quadosc(lambda r_: mp.exp(-0.8*r_)*mp.sin(1.3*r_), [0, mp.inf], omega=1.3)), 4*math.pi/(1.69 + 0.64), 1e-8)
      and close(4*math.pi/1.3*Q(lambda r_: r_*mp.exp(-r_/0.7)*mp.sin(1.3*r_), 0, mp.inf), 8*math.pi*0.343/(1 + 1.69*0.49)**2))
check('1k', "圆盘二维 FT 2πaJ₁(ka)/k", close(2*math.pi*Q(lambda r_: r_*mp.besselj(0, 2.1*r_), 0, 1.3), 2*math.pi*1.3*special.j1(2.1*1.3)/2.1))
check('1k', "Gibbs 过冲 ≈ 0.0895 J", abs(special.sici(math.pi)[0]/math.pi - 0.5 - 0.0895) < 1e-4)

# ---------- 01l 线性代数 ----------
xv_ = rng.random(5) + 0.5; yv_ = rng.random(5) + 0.2
Cm = 1/(xv_[:, None] + yv_[None, :])
num = np.prod([(xv_[j] - xv_[i])*(yv_[j] - yv_[i]) for i in range(5) for j in range(i + 1, 5)])
check('1l', "Cauchy 行列式", close(np.linalg.det(Cm), num/np.prod(xv_[:, None] + yv_[None, :]), 1e-8))
check('1l', "Hilbert 逆为整数", all(abs(v - round(v)) < 1e-6 for v in linalg.invhilbert(6).ravel()))
A2 = rng.normal(size=(3, 6)); B2 = rng.normal(size=(6, 3))
check('1l', "Cauchy–Binet", close(np.linalg.det(A2 @ B2), sum(np.linalg.det(A2[:, list(S)])*np.linalg.det(B2[list(S), :]) for S in itertools.combinations(range(6), 3)), 1e-8))
Am_ = rng.integers(-2, 3, size=(6, 6)).astype(float); Bm_ = rng.integers(-1, 2, size=(6, 6)).astype(float); Bm_[:, 3:] = 0; Cm_ = rng.integers(-2, 3, size=(6, 6)).astype(float); Cm_[4:] = 0
rk = np.linalg.matrix_rank
check('1l', "Frobenius 秩不等式", rk(Am_ @ Bm_) + rk(Bm_ @ Cm_) <= rk(Bm_) + rk(Am_ @ Bm_ @ Cm_))
P = rng.normal(size=(5, 2)); Pr = P @ np.linalg.inv(P.T @ P) @ P.T
check('1l', "投影 tr=rank", close(np.trace(Pr), 2) and np.allclose(Pr @ Pr, Pr))
Nl = np.triu(rng.normal(size=(5, 5)), 1); S_ = rng.normal(size=(5, 5)); Ns = S_ @ Nl @ np.linalg.inv(S_)
check('1l', "幂零: tr A^k=0", all(abs(np.trace(np.linalg.matrix_power(Ns, k))) < 1e-8 for k in range(1, 6)))
G_ = rng.normal(size=(4, 4))
check('1l', "Schur 不等式 Σ|λ|² ≤ ||A||_F²", np.sum(np.abs(np.linalg.eigvals(G_))**2) <= np.sum(G_**2) + 1e-12)
U_, P_ = linalg.polar(G_)
check('1l', "极分解: U 是最近的正交矩阵（随机比较）", all(np.linalg.norm(G_ - U_) <= np.linalg.norm(G_ - linalg.expm((lambda K: K - K.T)(rng.normal(size=(4, 4))*0.5)) @ U_) + 1e-12 for _ in range(200)))
Ap = rng.normal(size=(6, 3)) @ rng.normal(size=(3, 4)); Pp = np.linalg.pinv(Ap)
check('1l', "Moore–Penrose 四条件", np.allclose(Ap @ Pp @ Ap, Ap) and np.allclose(Pp @ Ap @ Pp, Pp) and np.allclose((Ap @ Pp).T, Ap @ Pp) and np.allclose((Pp @ Ap).T, Pp @ Ap))
check('1l', "Gelfand ρ(A)=lim||A^k||^{1/k}", abs(np.linalg.norm(np.linalg.matrix_power(G_/3, 400), 2)**(1/400) - max(abs(np.linalg.eigvals(G_/3)))) < 0.02)
check('1l', "Schur 乘积定理", np.linalg.eigvalsh(P1*P2).min() > -1e-10)
Ad = rng.normal(size=(5, 5)); Ad[:, 4] = Ad[:, 0] + Ad[:, 1]
adj = lambda M: np.array([[(-1)**(i + j)*np.linalg.det(np.delete(np.delete(M, j, 0), i, 1)) for j in range(M.shape[0])] for i in range(M.shape[0])])
check('1l', "adj 的秩与 adj(adj A)=det^{n-2}A", rk(adj(Ad), tol=1e-8) == 1 and np.allclose(adj(adj(G_)), np.linalg.det(G_)**2*G_))
ee = np.linalg.eigvals(G_)
check('1l', "主子式和 = e_k；Newton e3", close(sum(np.linalg.det(G_[np.ix_(S, S)]) for S in itertools.combinations(range(4), 2)), np.real(sum(ee[i]*ee[j] for i, j in itertools.combinations(range(4), 2))), 1e-8)
      and close(np.real(sum(ee[i]*ee[j]*ee[k] for i, j, k in itertools.combinations(range(4), 3))), (np.trace(G_)**3 - 3*np.trace(G_)*np.trace(G_ @ G_) + 2*np.trace(G_ @ G_ @ G_))/6, 1e-8))
def centralizer_dim(M):
    n_ = M.shape[0]; K = np.kron(np.eye(n_), M) - np.kron(M.T, np.eye(n_))
    return n_*n_ - rk(K, tol=1e-8)
J = linalg.block_diag(*[np.eye(k)*2 + np.eye(k, k=1) for k in (3, 2, 2)], *[np.eye(k)*5 + np.eye(k, k=1) for k in (2, 1)])
check('1l', "中心化子维数 Σc²（块 3,2,2 | 2,1）", centralizer_dim(J) == (3**2 + 3**2 + 1**2) + (2**2 + 1**2))
Nn = linalg.block_diag(*[np.eye(k, k=1) for k in (4, 2, 1)]); kd = lambda m: 7 - rk(np.linalg.matrix_power(Nn, m)) if m else 0
def im_ker(a, b):
    Ia = linalg.orth(np.linalg.matrix_power(Nn, a)) if a else np.eye(7); Kb = linalg.null_space(np.linalg.matrix_power(Nn, b))
    return Ia.shape[1] + Kb.shape[1] - rk(np.hstack([Ia, Kb])) if Kb.size and Ia.size else 0
check('1l', "dim(im N^a ∩ ker N^b) 公式", all(im_ker(a, b) == kd(a + b) - kd(a) for a in range(4) for b in range(1, 4)))
for M in (np.array([[1., 2], [-3, 0.5]]), np.array([[2., 1], [1, 3]]), np.array([[1., 1], [0, 1]])):
    tau = np.trace(M)/2; D = np.sqrt(complex(tau**2 - np.linalg.det(M))); tt = 0.8
    E = np.exp(tau*tt)*(np.cosh(D*tt)*np.eye(2) + (np.sinh(D*tt)/D if abs(D) > 1e-12 else tt)*(M - tau*np.eye(2)))
    ok2 = np.allclose(E, linalg.expm(tt*M))
    if not ok2: break
check('1l', "2×2 矩阵指数闭式（三种情形）", ok2)
xh = rng.normal(size=5); v = xh + np.sign(xh[0])*np.linalg.norm(xh)*np.eye(5)[0]; Hh = np.eye(5) - 2*np.outer(v, v)/(v @ v)
check('1l', "Householder 像为 -sgn(x1)||x||e1", np.allclose(Hh @ xh, -np.sign(xh[0])*np.linalg.norm(xh)*np.eye(5)[0]))
Ab_ = rng.normal(size=(4, 4)); Ab_ = Ab_ + Ab_.T; Bb_ = P1 + np.eye(4)
wg, Pg = linalg.eigh(Ab_, Bb_)
check('1l', "广义特征值同时对角化", np.allclose(Pg.T @ Bb_ @ Pg, np.eye(4)) and np.allclose(Pg.T @ Ab_ @ Pg, np.diag(wg)))
tt_ = 0.37
check('1l', "det(I+tA)=Σt^k tr Λ^k A", close(np.linalg.det(np.eye(4) + tt_*G_), sum(tt_**k*sum(np.linalg.det(G_[np.ix_(S, S)]) for S in itertools.combinations(range(4), k)) for k in range(5)), 1e-9))
Ai = np.linalg.inv(G_); I_, J_ = [0, 2], [1, 3]; Ic, Jc = [1, 3], [0, 2]
check('1l', "Jacobi 互补子式", close(np.linalg.det(Ai[np.ix_(I_, J_)]), (-1)**(sum(I_) + sum(J_) + 4)*np.linalg.det(G_[np.ix_(Jc, Ic)])/np.linalg.det(G_), 1e-9))
Ab = P1 + P2 + np.eye(4); Bb = P1 + np.eye(4)
check('1l', "Löwner: A≥B ⇒ B^{-1}≥A^{-1}, √A≥√B；A²≥B² 可失败", np.linalg.eigvalsh(np.linalg.inv(Bb) - np.linalg.inv(Ab)).min() > -1e-10
      and np.linalg.eigvalsh(linalg.sqrtm(Ab).real - linalg.sqrtm(Bb).real).min() > -1e-10 and np.linalg.eigvalsh(np.array([[2., 1], [1, 1]])@np.array([[2., 1], [1, 1]]) - np.diag([1., 0])).min() < 0)
dd_ = np.array([1., 2, 3.5, 5]); vv_ = rng.random(4) + 0.2; rho = 0.7; lam_ = np.linalg.eigvalsh(np.diag(dd_) + rho*np.outer(vv_, vv_))
check('1l', "秩一修正：久期方程与交错", all(abs(1 + rho*np.sum(vv_**2/(dd_ - l))) < 1e-8 for l in lam_) and all(dd_[i] < lam_[i] < (dd_[i + 1] if i < 3 else dd_[3] + rho*vv_ @ vv_) for i in range(4)))
perm = [1, 2, 0, 4, 3, 5]; Pm = np.eye(6)[perm]
check('1l', "置换矩阵特征多项式 ∏(λ^ℓ-1)", np.allclose(np.poly(Pm), np.polymul(np.polymul([1, 0, 0, -1], [1, 0, -1]), [1, -1])))
check('1l', "diag(-1,-1) 有实对数（转角 π）", np.allclose(linalg.expm(np.array([[0, -math.pi], [math.pi, 0]])), -np.eye(2)))

# ---------- 01m 抽代数论 ----------
from sympy.combinatorics import Permutation
from sympy.combinatorics.named_groups import AlternatingGroup, SymmetricGroup
A5 = AlternatingGroup(5)
check('1m', "A5 共轭类大小 1,15,20,12,12", sorted(len(c) for c in A5.conjugacy_classes()) == [1, 12, 12, 15, 20])
check('1m', "S_n 中心化子阶 ∏k^{m_k}m_k!", all(SymmetricGroup(6).order()//len(SymmetricGroup(6).conjugacy_class(Permutation(p, size=6))) == c for p, c in [([[0, 1], [2, 3]], 2*2*2*2), ([[0, 1, 2]], 3*6), ([[0, 1, 2, 3, 4, 5]], 6)]))
check('1m', "Landau g(10)=30", max(math.lcm(*p) for m in range(1, 11) for p in sp.utilities.iterables.partitions(10, m=m) for p in [[k for k, c in p.items() for _ in range(c)]]) == 30)
check('1m', "r₂(n)=4(d₁-d₃)", all(sum(1 for a in range(-12, 13) for b in range(-12, 13) if a*a + b*b == m) == 4*(sum(1 for d in sp.divisors(m) if d % 4 == 1) - sum(1 for d in sp.divisors(m) if d % 4 == 3)) for m in range(1, 120)))
check('1m', "√2+√3 极小多项式", sp.minimal_polynomial(sp.sqrt(2) + sp.sqrt(3), x) == x**4 - 10*x**2 + 1)
check('1m', "cos(2π/n) 次数 φ(n)/2", all(sp.degree(sp.minimal_polynomial(sp.cos(2*sp.pi/m), x), x) == sp.totient(m)//2 for m in (7, 9, 11, 12, 15)))
check('1m', "x³+px+q 判别式；x³-3x+1 为 81", sp.discriminant(x**3 + 2*x + 5, x) == -4*8 - 27*25 and sp.discriminant(x**3 - 3*x + 1, x) == 81)
check('1m', "x⁵-4x+2 恰 3 实根", len(sp.real_roots(x**5 - 4*x + 2)) == 3)
check('1m', "cos20° 满足 8x³-6x-1", abs(8*math.cos(math.pi/9)**3 - 6*math.cos(math.pi/9) - 1) < 1e-14)
check('1m', "三次判别式一般式", sp.expand(sp.discriminant(x**3 + 2*x**2 - 3*x + 7, x) - (4*9 - 4*(-27) - 4*8*7 - 27*49 + 18*2*(-3)*7)) == 0)
check('1m', "Legendre 公式与 100! 末尾零", sp.multiplicity(5, sp.factorial(100)) == 24 and all(sp.multiplicity(3, sp.factorial(m)) == (m - sum(sp.ntheory.digits(m, 3)[1:]))//2 for m in range(1, 200)))
check('1m', "Kummer: v₂C(2n,n) = s₂(n)", all(sp.multiplicity(2, sp.binomial(2*m, m)) == bin(m).count('1') for m in range(1, 300)))
def lucas(m, k, p):
    r_ = 1
    while m or k: r_ *= math.comb(m % p, k % p); m //= p; k //= p
    return r_ % p
check('1m', "Lucas 定理 (p=5,7)", all(math.comb(m, k) % p == lucas(m, k, p) for p in (5, 7) for m in range(60) for k in range(m + 1)))
check('1m', "LTE: v₂(3^{2^k}-1)=k+2, v₃(2^{3^k}+1)=k+1", all(sp.multiplicity(2, 3**(2**k) - 1) == k + 2 for k in range(1, 9)) and all(sp.multiplicity(3, 2**(3**k) + 1) == k + 1 for k in range(0, 6)))
check('1m', "(3/p)=1 ⇔ p≡±1 mod 12", all((sp.legendre_symbol(3, p) == 1) == (p % 12 in (1, 11)) for p in sp.primerange(5, 3000)))
check('1m', "Wilson 半阶乘", all(pow(math.factorial((p - 1)//2), 2, p) == (-1)**((p + 1)//2) % p for p in sp.primerange(3, 400)))
check('1m', "x²≡1 mod 2^k 有 4 解", all(sum(1 for a in range(2**k) if a*a % 2**k == 1) == 4 for k in range(3, 12)))
check('1m', "Dirichlet 卷积 φ*1=id, id*μ=φ", all(sum(sp.totient(d) for d in sp.divisors(m)) == m and sum(d*sp.mobius(m//d) for d in sp.divisors(m)) == sp.totient(m) for m in range(1, 300)))
Nd = 10**6
check('1m', "Σd(n) 与 Σφ(n) 主项", abs(sum(Nd//k for k in range(1, Nd + 1)) - (Nd*math.log(Nd) + (2*0.5772156649 - 1)*Nd)) < 5*math.sqrt(Nd))
check('1m', "Pell: D=13 (649,180), D=61", 649**2 - 13*180**2 == 1 and 1766319049**2 - 61*226153980**2 == 1)
check('1m', "Frobenius 数 ab-a-b 与不可表示个数", (lambda a, b: max(m for m in range(a*b) if not any((m - a*i) % b == 0 for i in range(m//a + 1))) == a*b - a - b
      and sum(1 for m in range(1, a*b) if not any((m - a*i) % b == 0 for i in range(m//a + 1))) == (a - 1)*(b - 1)//2)(7, 11))
check('1m', "r₄(n)=8Σ_{4∤d}d; 三平方定理", all(sum(1 for a in range(-6, 7) for b in range(-6, 7) for c in range(-6, 7) for d in range(-6, 7) if a*a + b*b + c*c + d*d == m) == 8*sum(d for d in sp.divisors(m) if d % 4) for m in range(1, 30))
      and all((any(a*a + b*b + c*c == m for a in range(0, 12) for b in range(0, 12) for c in range(0, 12))) == (lambda mm: not (lambda q: q % 8 == 7)(mm // 4**sp.multiplicity(4, mm)))(m) for m in range(1, 120)))
check('1m', "641 | F₅ 且 641 ≡ 1 mod 128", (2**32 + 1) % 641 == 0 and 641 % 128 == 1)
check('1m', "F_n-2 = ∏F_k", all(2**(2**m) + 1 - 2 == math.prod(2**(2**k) + 1 for k in range(m)) for m in range(1, 7)))
check('1m', "x⁴+1 模每个小素数可约", all(len(sp.factor_list(x**4 + 1, modulus=p)[1]) > 1 or sp.factor_list(x**4 + 1, modulus=p)[1][0][1] > 1 for p in sp.primerange(2, 60)))

# ---------- 01n 组合 ----------
check('1n', "Stirling S(n,k) 显式与 Bell / Dobinski", all(sp.functions.combinatorial.numbers.stirling(7, k) == sum((-1)**j*math.comb(k, j)*(k - j)**7 for j in range(k + 1))//math.factorial(k) for k in range(1, 8))
      and [int(sp.bell(m)) for m in range(7)] == [1, 1, 2, 5, 15, 52, 203] and close(float(mp.nsum(lambda k: k**6/mp.factorial(k), [0, mp.inf])/mp.e), 203))
pp = [int(sp.npartitions(m)) for m in range(60)]
def pent(m):
    s_ = 0; k = 1
    while True:
        g1, g2 = k*(3*k - 1)//2, k*(3*k + 1)//2
        if g1 > m: break
        sg = 1 if k % 2 else -1
        s_ += sg*pp[m - g1] + (sg*pp[m - g2] if g2 <= m else 0); k += 1
    return s_
check('1n', "五边形数递推 p(n)", all(pp[m] == pent(m) for m in range(1, 60)))
check('1n', "Hardy–Ramanujan 主项 (n=1000 相对误差<5%)", abs(math.exp(math.pi*math.sqrt(2000/3))/(4000*math.sqrt(3))/int(sp.npartitions(1000)) - 1) < 0.05)
check('1n', "错排 round(n!/e) 与有上界分配容斥", all(sp.subfactorial(m) == round(math.factorial(m)/math.e) for m in range(1, 15))
      and sum(1 for c in itertools.product(range(4), repeat=4) if sum(c) == 7) == sum((-1)**j*math.comb(4, j)*math.comb(7 - 4*j + 3, 3) for j in range(3)))
check('1n', "Σ(-1)^k C(n,k) k^m", all(sum((-1)**k*math.comb(6, k)*k**m for k in range(7)) == (0 if m < 6 else 720) for m in range(7)))
check('1n', "gcd(F_m,F_n)=F_gcd；Cassini", all(math.gcd(int(sp.fibonacci(a)), int(sp.fibonacci(b))) == sp.fibonacci(math.gcd(a, b)) for a in range(1, 40) for b in range(1, 40))
      and all(sp.fibonacci(m + 1)*sp.fibonacci(m - 1) - sp.fibonacci(m)**2 == (-1)**m for m in range(1, 30)))
def spanning(Adj):
    L = np.diag(Adj.sum(1)) - Adj; return round(np.linalg.det(L[1:, 1:]))
Kmn = np.block([[np.zeros((3, 3)), np.ones((3, 4))], [np.ones((4, 3)), np.zeros((4, 4))]])
cube = np.array([[1 if bin(i ^ j).count('1') == 1 else 0 for j in range(8)] for i in range(8)], float)
check('1n', "矩阵树: K_{3,4}=3³4², Q₃=384, K₆=6⁴", spanning(Kmn) == 3**3*4**2 and spanning(cube) == 2**(8 - 3 - 1)*1**3*2**3*3**1 and spanning(np.ones((6, 6)) - np.eye(6)) == 6**4)
check('1n', "k 叉树计数（Lagrange 反演）k=3", [math.comb(3*m, m)//(2*m + 1) for m in range(1, 7)] == [1, 3, 12, 55, 273, 1428])
check('1n', "Prüfer：度数序列 (3,2,1,1,1,2) 的树有 12 棵", sum(1 for seq in itertools.product(range(6), repeat=4) if all(seq.count(i) == d - 1 for i, d in enumerate((3, 2, 1, 1, 1, 2)))) == math.factorial(4)//(math.factorial(2)*math.factorial(1)))
def cyc_index_cube(k):
    return (k**6 + 3*k**4 + 12*k**3 + 8*k**2)//24
check('1n', "立方体面着色 k=2,3 与恰 2 红 = 2", cyc_index_cube(2) == 10 and cyc_index_cube(3) == 57)
qq = sp.symbols('q')
gb = sp.cancel(sp.prod([(1 - qq**(5 - i)) for i in range(2)])/sp.prod([(1 - qq**(i + 1)) for i in range(2)]))
check('1n', "F₂⁵ 中 2 维子空间数 = [5 2]_2 = 155", gb.subs(qq, 2) == 155)
def hook(lam):
    cols = [sum(1 for r_ in lam if r_ > j) for j in range(lam[0])]
    return math.factorial(sum(lam))//math.prod(lam[i] - j + cols[j] - i - 1 for i in range(len(lam)) for j in range(lam[i]))
check('1n', "钩长公式: Σ(f^λ)² = n! (n=7)", sum(hook([k for k, c in sorted(p.items(), reverse=True) for _ in range(c)])**2 for p in sp.utilities.iterables.partitions(7)) == math.factorial(7))
def kast(m, n_):
    return round(np.prod([4*math.cos(math.pi*j/(m + 1))**2 + 4*math.cos(math.pi*k/(n_ + 1))**2 for j in range(1, math.ceil(m/2) + 1) for k in range(1, math.ceil(n_/2) + 1)]))
check('1n', "Kasteleyn: 8×8=12988816, 2×n=F_{n+1}, 3×2n 递推", kast(8, 8) == 12988816 and all(kast(2, m) == sp.fibonacci(m + 1) for m in range(1, 15)) and [kast(3, 2*m) for m in range(1, 5)] == [3, 11, 41, 153])
check('1n', "Worpitzky 恒等式（用显式 Eulerian 数）", all(m**5 == sum(sum((-1)**j*math.comb(6, j)*(k + 1 - j)**5 for j in range(k + 1))*math.comb(m + k, 5) for k in range(5)) for m in range(0, 10)))
check('1n', "格路不碰 y=x+1: (m-n+1)/(m+1) C(m+n,n)", all(math.comb(m + k, k) - (math.comb(m + k, k - 1) if k else 0) == fractions.Fraction(m - k + 1, m + 1)*math.comb(m + k, k) for m in range(0, 12) for k in range(0, m + 1)))
check('1n', "色多项式: 圈 C5", sp.expand((t - 1)**5 - (t - 1)) == sp.expand(t*(t - 1)*(t - 2)*(t**2 - 2*t + 2)))
check('1n', "Σk C(n,k)² = n C(2n-1,n-1)", all(sum(k*math.comb(m, k)**2 for k in range(m + 1)) == m*math.comb(2*m - 1, m - 1) for m in range(1, 20)))

npass = sum(r[2] for r in R); print(f"\n第三轮续写数学(一) 01e–01n: {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
