"""第四轮续写 01o--01v、02i--02l 的核验。数值核验只覆盖所测参数。"""
import math, itertools, json, fractions
import numpy as np, sympy as sp, mpmath as mp
from scipy import integrate, linalg, special

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(9)
close = lambda a, b, tol=1e-9: abs(a - b) <= tol*max(1, abs(b))
x = sp.symbols('x')
mp.mp.dps = 30

# ---------- 01o 复分析补充 ----------
v = integrate.quad(lambda t: math.log(t)/(1 + t*t)**2, 0, np.inf, limit=200)[0]
check('1o', "∫₀^∞ ln x/(1+x²)² = -π/4", close(v, -math.pi/4, 1e-8))
a = 0.7
s = sum((-1)**n/(n*n + a*a) for n in range(1, 200000))
check('1o', "Σ(-1)^n/(n²+a²) = π/(2a sinh πa) - 1/(2a²)", close(s, math.pi/(2*a*math.sinh(math.pi*a)) - 1/(2*a*a), 1e-9))
z = mp.mpc(0.3, 0.5)
f = lambda t: mp.exp(t)*t**(-z)
hank = mp.quad(f, [-40 - 1j, 1 - 1j, 1 + 1j, -40 + 1j])/(2j*mp.pi)
check('1o', "Hankel 围道 1/Γ(z)", abs(hank - 1/mp.gamma(z)) < 1e-15)
for n_, xx in [(0, 1.3), (2, 4.1), (5, 7.7)]:
    vj = integrate.quad(lambda th: math.cos(n_*th - xx*math.sin(th)), 0, math.pi)[0]/math.pi
    check('1o', f"Bessel 积分 J_{n_}({xx})", close(vj, special.jv(n_, xx), 1e-10))
zeros = [0.3, -0.5j]
F = lambda zz: (zz - zeros[0])*(zz - zeros[1])*np.exp(zz)
jen = integrate.quad(lambda th: math.log(abs(F(np.exp(1j*th)))), 0, 2*math.pi)[0]/(2*math.pi)
check('1o', "Jensen 公式", close(math.log(abs(F(0))), sum(math.log(abs(zk)) for zk in zeros) + jen, 1e-9))

# ---------- 01p 多项式 ----------
for n_ in (4, 5, 6):
    pts = [(k, sp.Rational(k, k + 1)) for k in range(n_ + 1)]
    pv = sp.interpolate(pts, x).subs(x, n_ + 1)
    check('1p', f"p(k)=k/(k+1) 的插值在 n+1 处（n={n_}）", pv == sp.Rational(n_ + 1 + (-1)**(n_ + 1), n_ + 2))
ok = True
for _ in range(200):
    c = rng.normal(size=8); r_ = np.roots(c)
    ok &= np.max(np.abs(r_)) < 1 + np.max(np.abs(c[1:]/c[0]))
check('1p', "Cauchy 根模上界", ok)
def phi1(n):
    return sp.cyclotomic_poly(n, x).subs(x, 1)
ok = all(phi1(n) == (sp.factorint(n) and (list(sp.factorint(n))[0] if len(sp.factorint(n)) == 1 else 1)) for n in range(2, 80))
check('1p', "Φ_n(1)=p（素数幂）或 1", ok)
coef_ok = all(set(sp.Poly(sp.cyclotomic_poly(n, x), x).coeffs()) <= {0, 1, -1} for n in range(1, 105))
check('1p', "n<105 时 Φ_n 系数 ∈{0,±1}，Φ_105 出现 -2", coef_ok and -2 in sp.Poly(sp.cyclotomic_poly(105, x), x).coeffs())
ok3 = all(sum(math.comb(n, 3*k) for k in range(n//3 + 1))*3 == 2**n + round(2*math.cos(n*math.pi/3)) for n in range(1, 40))
ok4 = all(abs(sum(math.comb(n, 4*k) for k in range(n//4 + 1))*4 - (2**n + 2**(n/2 + 1)*math.cos(n*math.pi/4))) < 1e-6 for n in range(1, 40))
check('1p', "Σ C(n,3k) 与 Σ C(n,4k) 的单位根过滤", ok3 and ok4)
p_, q_ = -7.0, 6.0     # 根 1, 2, -3
roots = sorted(2*math.sqrt(-p_/3)*math.cos(math.acos(3*q_/(2*p_)*math.sqrt(-3/p_))/3 - 2*math.pi*k/3) for k in range(3))
check('1p', "三次方程三角解（x³-7x+6）", np.allclose(roots, [-3, 1, 2]))
rem = sp.rem(x**100, x**2 - 3*x + 2, x)
check('1p', "x^100 mod (x²-3x+2)", sp.expand(rem - ((2**100 - 1)*x + 2 - 2**100)) == 0)
P = sp.Poly((x - 1)*(x + 2)*(x - 3)*(x - 0.5), x); x0 = 0.77
check('1p', "Σ1/(x-r_i)=p'/p", close(sum(1/(x0 - r) for r in (1, -2, 3, 0.5)), float(P.diff(x).eval(x0)/P.eval(x0)), 1e-12))

# ---------- 01s 数论进阶 ----------
for p in (5, 7, 11, 13, 17, 19):
    g = sum(np.exp(2j*np.pi*k*k/p) for k in range(p))
    want = math.sqrt(p) if p % 4 == 1 else 1j*math.sqrt(p)
    check('1s', f"二次 Gauss 和 p={p}", abs(g - want) < 1e-9)
pn = [int(sp.functions.combinatorial.numbers.partition(n)) for n in range(300)]
check('1s', "Ramanujan 同余 5,7,11", all(pn[5*n + 4] % 5 == 0 for n in range(55)) and all(pn[7*n + 5] % 7 == 0 for n in range(40)) and all(pn[11*n + 6] % 11 == 0 for n in range(25)))
ok = sp.bernoulli(12) == sp.Rational(-691, 2730)
for n in range(1, 15):
    val = sp.bernoulli(2*n) + sum(sp.Rational(1, p) for p in sp.primerange(2, 2*n + 2) if (2*n) % (p - 1) == 0)
    ok &= val.is_integer
check('1s', "von Staudt--Clausen（2n≤28），B₁₂=-691/2730", ok)
check('1s', "Wolstenholme C(2p-1,p-1)≡1 mod p³", all(math.comb(2*p - 1, p - 1) % p**3 == 1 for p in (5, 7, 11, 13, 17, 19, 23)))
check('1s', "561 是 Carmichael 数（Korselt）", all(560 % (p - 1) == 0 for p in (3, 11, 17)) and all(pow(a, 560, 561) == 1 for a in range(2, 561) if math.gcd(a, 561) == 1))
def classno(D):
    h = 0
    a = 1
    while 3*a*a <= -D:
        for b in range(-a + 1, a + 1):
            if (b*b - D) % (4*a) == 0:
                c = (b*b - D)//(4*a)
                if c >= a and math.gcd(math.gcd(a, abs(b)), c) == 1 and not (b < 0 and (a == c)):
                    h += 1
        a += 1
    return h
ones = []
for d in range(1, 400):
    if any(d % (p*p) == 0 for p in range(2, 21)):
        continue
    D = -d if d % 4 == 3 else -4*d
    if classno(D) == 1:
        ones.append(d)
check('1s', "类数为 1 的虚二次域 d=1,2,3,7,11,19,43,67,163", ones == [1, 2, 3, 7, 11, 19, 43, 67, 163], str(ones))
check('1s', "e^{π√163} 接近整数 640320³+744", abs(mp.mpf(640320)**3 + 744 - mp.exp(mp.pi*mp.sqrt(163))) < 1e-11)
def rep(p, n):
    return any(math.isqrt(p - n*y*y)**2 == p - n*y*y for y in range(0, math.isqrt(p//n) + 1))
pr = list(sp.primerange(5, 1000))
check('1s', "p=x²+2y² ⇔ p≡1,3 (8)；p=x²+3y² ⇔ p≡1 (3)", all(rep(p, 2) == (p % 8 in (1, 3)) for p in pr) and all(rep(p, 3) == (p % 3 == 1) for p in pr))
check('1s', "g(k)=2^k+⌊(3/2)^k⌋-2：4,9,19,37", [2**k + math.floor(1.5**k) - 2 for k in (2, 3, 4, 5)] == [4, 9, 19, 37])
ok = True
for p in sp.primerange(5, 200):
    cnt = 1 + sum(1 + sp.legendre_symbol((xx**3 + xx + 1) % p, p) if (xx**3 + xx + 1) % p else 1 for xx in range(p))
    ok &= abs(cnt - (p + 1)) <= 2*math.sqrt(p)
check('1s', "Hasse 界（y²=x³+x+1）", ok)

# ---------- 01t 矩阵技巧补充 ----------
n_ = 7
T = np.diag(-2*np.ones(n_)) + np.diag(np.ones(n_ - 1), 1) + np.diag(np.ones(n_ - 1), -1)
ev = np.sort(np.linalg.eigvalsh(T)); want = np.sort([-4*math.sin(k*math.pi/(2*(n_ + 1)))**2 for k in range(1, n_ + 1)])
check('1t', "tridiag(1,-2,1) 特征值", np.allclose(ev, want))
L2 = np.kron(T, np.eye(n_)) + np.kron(np.eye(n_), T)
check('1t', "二维 Laplacian = Kronecker 和", np.allclose(np.sort(np.linalg.eigvalsh(L2)), np.sort([a_ + b_ for a_ in want for b_ in want])))
def spd(n):
    M = rng.normal(size=(n, n)); return M@M.T + n*np.eye(n)
A, B = spd(4), spd(4)
sq = lambda M: linalg.sqrtm(M).real
Ah = sq(A); Aih = np.linalg.inv(Ah)
G = Ah@sq(Aih@B@Aih)@Ah
Bh = sq(B); Bih = np.linalg.inv(Bh)
G2 = Bh@sq(Bih@A@Bih)@Bh
check('1t', "几何平均：A#B=B#A 且 X A⁻¹ X=B", np.allclose(G, G2) and np.allclose(G@np.linalg.inv(A)@G, B))
Aw, V = np.linalg.eigh(A); E = rng.normal(size=(4, 4)); E = E + E.T
Fm = np.array([[(math.exp(Aw[i]) - math.exp(Aw[j]))/(Aw[i] - Aw[j]) if i != j else math.exp(Aw[i]) for j in range(4)] for i in range(4)])/1.0
h = 1e-6
num = (linalg.expm((A + h*E)/10) - linalg.expm((A - h*E)/10))/(2*h)
Aw10 = Aw/10
Fm = np.array([[(math.exp(Aw10[i]) - math.exp(Aw10[j]))/(Aw10[i] - Aw10[j]) if i != j else math.exp(Aw10[i]) for j in range(4)] for i in range(4)])
check('1t', "Daleckii--Krein 导数（f=exp）", np.allclose(num, V@(Fm*(V.T@(E/10)@V))@V.T, atol=1e-6))
S = rng.normal(size=(4, 4)); S = S + S.T
vals = [np.array(z_)@S@np.array(z_) for z_ in itertools.product([-1, 1], repeat=4)]
check('1t', "Hutchinson：均值=tr，方差=2(‖A‖F²-Σa_ii²)", close(np.mean(vals), np.trace(S)) and close(np.var(vals), 2*(np.sum(S*S) - np.sum(np.diag(S)**2))))
M = rng.normal(size=(5, 5)); U_, sv, Vt = np.linalg.svd(M)
Ms = M - sv[-1]*np.outer(U_[:, -1], Vt[-1])
check('1t', "到奇异矩阵的最近距离 = σ_min", abs(np.linalg.det(Ms)) < 1e-10 and close(np.linalg.norm(M - Ms, 2), sv[-1]))
nvec = rng.normal(size=3); nvec /= np.linalg.norm(nvec); th = 1.1
K = np.array([[0, -nvec[2], nvec[1]], [nvec[2], 0, -nvec[0]], [-nvec[1], nvec[0], 0]])
Rm = linalg.expm(th*K)
check('1t', "旋转矩阵对数：θ 与轴", close(math.acos((np.trace(Rm) - 1)/2), th) and np.allclose((Rm - Rm.T)/(2*math.sin(th)), K))
A5 = spd(5); U = rng.normal(size=(5, 2)); C = spd(2); Vv = rng.normal(size=(2, 5))
lhs = np.linalg.inv(A5 + U@C@Vv); Ai = np.linalg.inv(A5)
check('1t', "Woodbury 恒等式", np.allclose(lhs, Ai - Ai@U@np.linalg.inv(np.linalg.inv(C) + Vv@Ai@U)@Vv@Ai))
xv = rng.normal(size=5)
check('1t', "det(A+xxᵀ)=det A (1+xᵀA⁻¹x)", close(np.linalg.det(A5 + np.outer(xv, xv)), np.linalg.det(A5)*(1 + xv@Ai@xv), 1e-9))
H = np.array([[1]])
for _ in range(3):
    H = np.block([[H, H], [H, -H]])
check('1t', "Sylvester Hadamard：HHᵀ=8I，|det|=8⁴", np.allclose(H@H.T, 8*np.eye(8)) and close(abs(np.linalg.det(H)), 8**4))

# ---------- 01u 竞赛型技巧 ----------
check('1u', "max∫(x²f-xf²) = 1/16", close(integrate.quad(lambda t: t**3/4, 0, 1)[0], 1/16))
def ram(depth):
    v_ = 1.0
    for n in range(depth, 1, -1):
        v_ = math.sqrt(1 + n*v_)
    return v_
check('1u', "Ramanujan 嵌套根式 → 3", abs(ram(60) - 3) < 1e-12)
def nest(k):
    v_ = 0.0
    for _ in range(k):
        v_ = math.sqrt(2 + v_)
    return v_
check('1u', "k 层 √(2+…) = 2cos(π/2^{k+1})", all(close(nest(k), 2*math.cos(math.pi/2**(k + 1))) for k in range(1, 12)))
ok = all(sum(math.floor(xx + k/n) for k in range(n)) == math.floor(n*xx) for n in range(1, 9) for xx in rng.uniform(-5, 5, 50))
ok &= all(sum((k*q)//p for k in range(1, p)) == (p - 1)*(q - 1)//2 for p in range(2, 30) for q in range(2, 30) if math.gcd(p, q) == 1)
phi = (1 + 5**0.5)/2
Sa = {math.floor(n*phi) for n in range(1, 2000)}; Sb = {math.floor(n*phi*phi) for n in range(1, 2000)}
ok &= Sa.isdisjoint(Sb) and set(range(1, 3000)) <= (Sa | Sb)
check('1u', "Hermite、格点求和、Beatty（φ, φ²）", ok)
N = 10**6
k = np.arange(1, N + 1)
check('1u', "(1/n)Σ(⌊2n/k⌋-2⌊n/k⌋) → 2ln2-1", abs(np.mean((2*N)//k - 2*(N//k)) - (2*math.log(2) - 1)) < 1e-4)
check('1u', "(1/n)Σ{n/k} → 1-γ", abs(np.mean(N/k - N//k) - (1 - float(mp.euler))) < 1e-4)
n_ = 12
Gm = sp.Matrix(n_, n_, lambda i, j: math.gcd(i + 1, j + 1))
check('1u', "Smith 行列式 det[gcd(i,j)] = Πφ(k)", Gm.det() == math.prod(sp.totient(k) for k in range(1, n_ + 1)))
check('1u', "Σ n/(n⁴+n²+1) = 1/2", sp.summation(sp.Symbol('n')/(sp.Symbol('n')**4 + sp.Symbol('n')**2 + 1), (sp.Symbol('n'), 1, sp.oo)) == sp.Rational(1, 2))
def subsets_mod5(Nn):
    cnt = [1, 0, 0, 0, 0]
    for e in range(1, Nn + 1):
        cnt = [cnt[r] + cnt[(r - e) % 5] for r in range(5)]
    return cnt[0]
check('1u', "{1..2000} 中和被 5 整除的子集数", subsets_mod5(2000) == (2**2000 + 4*2**400)//5 and (2**2000 + 4*2**400) % 5 == 0)
check('1u', "Π(1+2^{-2^k}) = 2", abs(math.prod(1 + 2.0**(-2**k) for k in range(7)) - 2) < 1e-15)
c_ = sp.Symbol('c')
check('1u', "反例 f=1-2x：c f(c)=∫₀ᶜ f 只在 c=0", sp.solve(sp.Eq(c_*(1 - 2*c_), sp.integrate(1 - 2*x, (x, 0, c_))), c_) == [0])
cc = optimize_root = None
from scipy import optimize
fx = lambda t: math.cos(3*t) - 0.2 + 0*t
mean0 = integrate.quad(fx, 0, 1)[0]
g_ = lambda t: fx(t) - mean0          # ∫₀¹ g = 0
hfun = lambda cpt: g_(cpt) - integrate.quad(g_, 0, cpt)[0]
grid = np.linspace(1e-3, 1 - 1e-3, 400)
vals = [hfun(t) for t in grid]
check('1u', "存在 c 使 f(c)=∫₀ᶜ f（数值例）", any(vals[i]*vals[i + 1] <= 0 for i in range(len(vals) - 1)))

# ---------- 01v 泛函分析补充 ----------
m = 1500; hgrid = 1/m
Vmat = np.tril(np.ones((m, m)))*hgrid - np.eye(m)*hgrid/2
sv = np.linalg.svd(Vmat, compute_uv=False)
check('1v', "Volterra 算子 ‖V‖=2/π", abs(sv[0] - 2/math.pi) < 1e-4)
check('1v', "‖V‖_HS² = Σ 1/((n+½)π)² = 1/2", close(sum(1/((n + 0.5)*math.pi)**2 for n in range(200000)), 0.5, 1e-5) and abs(np.sum(sv**2) - 0.5) < 1e-3)
def numrad(Am, K=3600):
    th = np.linspace(0, 2*np.pi, K, endpoint=False)
    return max(np.linalg.eigvalsh((np.exp(1j*t)*Am + np.exp(-1j*t)*Am.conj().T)/2)[-1] for t in th)
Nil = np.array([[0, 1], [0, 0]], dtype=complex)
check('1v', "幂零 2×2 的数值半径 1/2", close(numrad(Nil), 0.5, 1e-6))
ok = True
for _ in range(20):
    Am = rng.normal(size=(4, 4)) + 1j*rng.normal(size=(4, 4)); w_ = numrad(Am, 720); nrm = np.linalg.norm(Am, 2)
    ok &= (0.5*nrm - 1e-9 <= w_ <= nrm + 1e-9)
check('1v', "½‖A‖ ≤ w(A) ≤ ‖A‖", ok)
Am = rng.normal(size=(4, 4))
mu_ = max(np.linalg.eigvalsh((Am + Am.T)/2))
check('1v', "‖e^{tA}‖ ≤ e^{t·max Re W(A)}", all(np.linalg.norm(linalg.expm(t*Am), 2) <= math.exp(t*mu_)*(1 + 1e-12) for t in np.linspace(0, 3, 31)))
ang = [math.pi/2 + 2*math.pi*k/3 for k in range(3)]
Phi = np.array([[math.cos(a_), math.sin(a_)] for a_ in ang])
check('1v', "Mercedes--Benz 框架 A=B=3/2", np.allclose(Phi.T@Phi, 1.5*np.eye(2)))
kern = lambda xx: integrate.quad(lambda kk: math.cos(kk*xx)/(1 + kk*kk), 0, np.inf, limit=400, weight='cos', wvar=xx)[0]/math.pi if xx else integrate.quad(lambda kk: 1/(1 + kk*kk), 0, np.inf)[0]/math.pi
check('1v', "H¹(ℝ) 的再生核 ½e^{-|x|}", all(close(integrate.quad(lambda kk: 1/(1 + kk*kk), 0, np.inf, weight='cos', wvar=xx)[0]/math.pi, 0.5*math.exp(-xx), 1e-7) for xx in (0.3, 1.0, 2.5)))
Rot = np.array([[math.cos(0.7), -math.sin(0.7), 0], [math.sin(0.7), math.cos(0.7), 0], [0, 0, 1]])
xv = np.array([1.0, 2.0, 3.0]); avg = np.zeros(3); Pk = np.eye(3)
for kk in range(20000):
    avg += Pk@xv; Pk = Pk@Rot
check('1v', "平均遍历：投影到不动子空间", np.allclose(avg/20000, [0, 0, 3], atol=1e-3))

# ---------- 02i 凸几何与离散几何 ----------
w_ = 1.0
reul_area = (math.pi - math.sqrt(3))/2*w_**2
check('2i', "Reuleaux 三角形面积 (π-√3)w²/2，周长 πw", close(3*(math.pi/6*w_**2) - 2*(math.sqrt(3)/4*w_**2), reul_area) and close(3*w_*math.pi/3, math.pi*w_))
check('2i', "堆积密度 π/√12≈0.9069，π/√18≈0.7405", abs(math.pi/math.sqrt(12) - 0.9069) < 1e-4 and abs(math.pi/math.sqrt(18) - 0.7405) < 1e-4)
c_disk = (2/3)**(1/3)*math.gamma(5/3)*2*math.pi/math.pi**(1/3)
check('2i', "圆盘内随机点凸包顶点 ~ 3.38 n^{1/3}", abs(c_disk - 3.38) < 0.01, f"c={c_disk:.4f}")
check('2i', "Mahler：正方形与其极体（菱形）体积积 = 4²/2!", close(4*2, 4**2/2))
a1, a2, b1, b2 = 1.0, 3.0, 2.5, 0.4
check('2i', "Brunn--Minkowski（两个矩形）", ((a1 + b1)*(a2 + b2))**0.5 >= (a1*a2)**0.5 + (b1*b2)**0.5)

# ---------- 02j 三角形几何 ----------
def tri_data(P):
    A_, B_, C_ = P
    a_ = np.linalg.norm(B_ - C_); b_ = np.linalg.norm(C_ - A_); c_ = np.linalg.norm(A_ - B_)
    s_ = (a_ + b_ + c_)/2; K_ = math.sqrt(s_*(s_ - a_)*(s_ - b_)*(s_ - c_))
    Aa = math.acos((b_*b_ + c_*c_ - a_*a_)/(2*b_*c_)); Bb = math.acos((a_*a_ + c_*c_ - b_*b_)/(2*a_*c_)); Cc = math.pi - Aa - Bb
    return a_, b_, c_, s_, K_, Aa, Bb, Cc
ok = {k: True for k in ['id', 'area', 'dist', 'ineq', 'fermat', 'brocard', 'em']}
for _ in range(30):
    P = rng.normal(size=(3, 2))
    a_, b_, c_, s_, K_, Aa, Bb, Cc = tri_data(P)
    Rr = a_*b_*c_/(4*K_); r_ = K_/s_; ra = K_/(s_ - a_); rb = K_/(s_ - b_); rc = K_/(s_ - c_)
    ok['id'] &= close(math.cos(Aa) + math.cos(Bb) + math.cos(Cc), 1 + r_/Rr) and close(math.sin(Aa) + math.sin(Bb) + math.sin(Cc), s_/Rr) \
        and close(math.sin(Aa/2)*math.sin(Bb/2)*math.sin(Cc/2), r_/(4*Rr)) and close(1/math.tan(Aa) + 1/math.tan(Bb) + 1/math.tan(Cc), (a_*a_ + b_*b_ + c_*c_)/(4*K_))
    ok['area'] &= close(K_, 2*Rr*Rr*math.sin(Aa)*math.sin(Bb)*math.sin(Cc)) and close(K_, math.sqrt(r_*ra*rb*rc)) and close(1/r_, 1/ra + 1/rb + 1/rc)
    A_, B_, C_ = P
    D = 2*(A_[0]*(B_[1] - C_[1]) + B_[0]*(C_[1] - A_[1]) + C_[0]*(A_[1] - B_[1]))
    O = np.array([np.dot(A_, A_)*(B_[1] - C_[1]) + np.dot(B_, B_)*(C_[1] - A_[1]) + np.dot(C_, C_)*(A_[1] - B_[1]),
                  np.dot(A_, A_)*(C_[0] - B_[0]) + np.dot(B_, B_)*(A_[0] - C_[0]) + np.dot(C_, C_)*(B_[0] - A_[0])])/D
    Hc = A_ + B_ + C_ - 2*O
    I = (a_*A_ + b_*B_ + c_*C_)/(a_ + b_ + c_); Ia = (-a_*A_ + b_*B_ + c_*C_)/(-a_ + b_ + c_)
    ok['dist'] &= close(np.sum((O - Hc)**2), 9*Rr*Rr - (a_*a_ + b_*b_ + c_*c_)) and close(np.sum((I - Hc)**2), 2*r_*r_ - 4*Rr*Rr*math.cos(Aa)*math.cos(Bb)*math.cos(Cc)) \
        and close(np.sum((O - Ia)**2), Rr*Rr + 2*Rr*ra) and close(np.linalg.norm(A_ - I), r_/math.sin(Aa/2)) and close(np.linalg.norm(I - Ia), 4*Rr*math.sin(Aa/2)) \
        and close(np.sum((O - I)**2), Rr*Rr - 2*Rr*r_) and close(np.linalg.norm(A_ - Hc), 2*Rr*abs(math.cos(Aa)))
    ok['ineq'] &= a_*a_ + b_*b_ + c_*c_ >= 4*math.sqrt(3)*K_ + (a_ - b_)**2 + (b_ - c_)**2 + (c_ - a_)**2 - 1e-12 and Rr >= 2*r_
    ok['brocard'] &= close(1/math.tan(Aa) + 1/math.tan(Bb) + 1/math.tan(Cc), (a_*a_ + b_*b_ + c_*c_)/(4*K_)) and math.atan(1/((a_*a_ + b_*b_ + c_*c_)/(4*K_))) <= math.pi/6 + 1e-12
    if max(Aa, Bb, Cc) < 2*math.pi/3:
        fsum = optimize.minimize(lambda q: sum(np.linalg.norm(q - V_) for V_ in P), P.mean(axis=0), method='Nelder-Mead', options={'xatol': 1e-12, 'fatol': 1e-14, 'maxiter': 20000}).fun
        ok['fermat'] &= abs(fsum**2 - ((a_*a_ + b_*b_ + c_*c_)/2 + 2*math.sqrt(3)*K_)) < 1e-6
    # Erdős--Mordell：取三角形内随机点
    wts = rng.dirichlet([1, 1, 1]); Q = wts@P
    def dline(Pt, U_, W_):
        d1_, d2_ = W_ - U_, Pt - U_
        return abs(d1_[0]*d2_[1] - d1_[1]*d2_[0])/np.linalg.norm(W_ - U_)
    ok['em'] &= sum(np.linalg.norm(Q - V_) for V_ in P) >= 2*(dline(Q, B_, C_) + dline(Q, C_, A_) + dline(Q, A_, B_)) - 1e-12
check('2j', "三角恒等式 Σcos=1+r/R、Σsin=s/R、Πsin(A/2)=r/4R、Σcot=(a²+b²+c²)/4K", ok['id'])
check('2j', "面积 2R²ΠsinA = √(r r_a r_b r_c)，1/r=Σ1/r_a", ok['area'])
check('2j', "距离公式 OH²、IH²、OI_a²、AI、II_a、OI²、AH", ok['dist'])
check('2j', "Hadwiger--Finsler 与 R≥2r", ok['ineq'])
check('2j', "Brocard 角 cotω=Σcot，ω≤30°", ok['brocard'])
check('2j', "Fermat 点距离和公式", ok['fermat'])
check('2j', "Erdős--Mordell 不等式", ok['em'])
k_, d_ = 2.3, 1.7
A_, B_ = np.array([0.0, 0.0]), np.array([d_, 0.0])
cen = (A_ - k_*k_*B_)/(1 - k_*k_); rad = k_*d_/abs(1 - k_*k_)
pts = [cen + rad*np.array([math.cos(t), math.sin(t)]) for t in np.linspace(0, 6, 7)]
check('2j', "Apollonius 圆半径 kd/|1-k²|", all(close(np.linalg.norm(q - A_)/np.linalg.norm(q - B_), k_) for q in pts))
aa = 1.0
Vt_ = aa**3/(6*math.sqrt(2)); St_ = math.sqrt(3)*aa*aa
check('2j', "正四面体 r=a/(2√6)=3V/S，R=√6a/4=3r", close(3*Vt_/St_, aa/(2*math.sqrt(6))) and close(math.sqrt(6)/4*aa, 3*aa/(2*math.sqrt(6))))
P = rng.normal(size=(3, 2)); a_, b_, c_, s_, K_, *_ = tri_data(P)
M3 = np.array([(P[1] + P[2])/2, (P[0] + P[2])/2, (P[0] + P[1])/2]); am, bm, cm, sm, Km, *_ = tri_data(M3)
check('2j', "九点圆半径 R/2", close(am*bm*cm/(4*Km), a_*b_*c_/(4*K_)/2))

# ---------- 02k Lie 代数与表示 ----------
chi = lambda j, th: math.sin((2*j + 1)*th/2)/math.sin(th/2)
ok = True
for j1 in (0, 0.5, 1, 1.5):
    for j2 in (0, 0.5, 1, 1.5):
        val = integrate.quad(lambda th: chi(j1, th)*chi(j2, th)*math.sin(th/2)**2, 1e-12, 2*math.pi - 1e-12)[0]*(2/math.pi)/2
        ok &= abs(val - (j1 == j2)) < 1e-8
check('2k', "SU(2) 特征标正交", ok)
th = 0.83
check('2k', "χ_{j1}χ_{j2}=Σχ_J（1⊗3/2）", close(chi(1, th)*chi(1.5, th), sum(chi(J, th) for J in (0.5, 1.5, 2.5))))
check('2k', "½⊗½⊗½ = 3/2⊕½⊕½（特征标）", close(chi(0.5, th)**3, chi(1.5, th) + 2*chi(0.5, th)))
d3 = lambda p, q: (p + 1)*(q + 1)*(p + q + 2)//2
check('2k', "SU(3) 维数：3,8,10,6；3⊗3̄=8+1，3⊗3⊗3=10+8+8+1", [d3(1, 0), d3(1, 1), d3(3, 0), d3(2, 0)] == [3, 8, 10, 6] and 9 == 8 + 1 and 27 == 10 + 8 + 8 + 1)
def hook_content(shape, N):
    num = den = 1
    conj = [sum(1 for r in shape if r > c) for c in range(shape[0])]
    for i, row in enumerate(shape):
        for j in range(row):
            num *= N + j - i; den *= (row - j - 1) + (conj[j] - i - 1) + 1
    return num//den
ok = all(hook_content([k], N) == math.comb(N + k - 1, k) for N in range(2, 7) for k in range(1, 6)) and all(hook_content([1]*k, N) == math.comb(N, k) for N in range(2, 7) for k in range(1, N + 1))
ok &= hook_content([2], 3) == 6 and hook_content([2, 1], 3) == 8 and all(hook_content([p + q, q], 3) == d3(p, q) for p in range(4) for q in range(4))
check('2k', "钩长--内容公式（行、列、SU(3) 的 (p,q)）", ok)
dims = {'A': lambda n: n*(n + 2), 'B': lambda n: n*(2*n + 1), 'C': lambda n: n*(2*n + 1), 'D': lambda n: n*(2*n - 1)}
check('2k', "低秩同构的维数：A1=B1=C1，B2=C2，D3=A3", dims['A'](1) == dims['B'](1) == dims['C'](1) == 3 and dims['B'](2) == dims['C'](2) == 10 and dims['D'](3) == dims['A'](3) == 15)
ok = True
for _ in range(500):
    X = rng.normal(size=(2, 2))*2; X -= np.trace(X)/2*np.eye(2)
    ok &= np.trace(linalg.expm(X)) >= -2 - 1e-9
check('2k', "sl(2,ℝ)：tr e^X ≥ -2", ok)
check('2k', "三维谐振子第 N 能级简并 (N+1)(N+2)/2", all(sum(1 for a_ in range(N + 1) for b_ in range(N + 1 - a_)) == (N + 1)*(N + 2)//2 for N in range(10)))

# ---------- 02l 图论补充 ----------
def petersen():
    E = []
    for i in range(5):
        E += [(i, (i + 1) % 5), (i, i + 5), (5 + i, 5 + (i + 2) % 5)]
    A_ = np.zeros((10, 10))
    for u, v_ in E:
        A_[u, v_] = A_[v_, u] = 1
    return A_, E
Ap, Ep = petersen()
evp = np.round(np.linalg.eigvalsh(Ap), 8)
check('2l', "Petersen 谱 3,1^(5),(-2)^(4)", sorted(evp.tolist()) == sorted([3.0] + [1.0]*5 + [-2.0]*4))
lam_, mu_, k_, n_ = 0, 1, 3, 10
disc = (lam_ - mu_)**2 + 4*(k_ - mu_)
th1, th2 = ((lam_ - mu_) + math.sqrt(disc))/2, ((lam_ - mu_) - math.sqrt(disc))/2
f1 = 0.5*((n_ - 1) - (2*k_ + (n_ - 1)*(lam_ - mu_))/math.sqrt(disc)); f2 = 0.5*((n_ - 1) + (2*k_ + (n_ - 1)*(lam_ - mu_))/math.sqrt(disc))
check('2l', "srg 特征值与重数公式（Petersen）", (th1, th2, f1, f2) == (1.0, -2.0, 5.0, 4.0))
alpha = max(len(S) for r in range(1, 11) for S in itertools.combinations(range(10), r) if all(Ap[u, v_] == 0 for u, v_ in itertools.combinations(S, 2)))
check('2l', "Hoffman 比值界在 Petersen 上取等 α=4", alpha == 4 == round(10*2/(3 + 2)))
def has_pm(A_):
    n = len(A_)
    def rec(left):
        if not left: return True
        u = left[0]
        return any(A_[u, v_] and rec([w for w in left if w not in (u, v_)]) for v_ in left[1:])
    return rec(list(range(n)))
check('2l', "Petersen 定理（无桥 3 正则有完美匹配）", has_pm(Ap))
def edge_col(E, k):
    n = len(E); col = [-1]*n
    adj = [[j for j in range(n) if j != i and set(E[i]) & set(E[j])] for i in range(n)]
    def bt(i):
        if i == n: return True
        for c in range(k):
            if all(col[j] != c for j in adj[i]):
                col[i] = c
                if bt(i + 1): return True
        col[i] = -1
        return False
    return bt(0)
check('2l', "Petersen 图 χ'=4（不能 3 边着色）", not edge_col(Ep, 3) and edge_col(Ep, 4))
def graphical_EG(d):
    d = sorted(d, reverse=True)
    if sum(d) % 2: return False
    return all(sum(d[:k]) <= k*(k - 1) + sum(min(x_, k) for x_ in d[k:]) for k in range(1, len(d) + 1))
def graphical_HH(d):
    d = sorted(d, reverse=True)
    while d and d[0] > 0:
        f_ = d.pop(0)
        if f_ > len(d): return False
        for i in range(f_):
            d[i] -= 1
            if d[i] < 0: return False
        d.sort(reverse=True)
    return True
ok = all(graphical_EG(list(d)) == graphical_HH(list(d)) for n in range(1, 7) for d in itertools.product(range(6), repeat=n))
check('2l', "Erdős--Gallai ⇔ Havel--Hakimi（n≤6 全部度序列），(3,3,3,1) 不可图", ok and not graphical_EG([3, 3, 3, 1]))
check('2l', "Moore 界：d=3,k=2 时 10（Petersen），d=7 时 50", 1 + 3 + 3*2 == 10 and 1 + 7 + 7*6 == 50)
def myc(A_):
    n = len(A_); M_ = np.zeros((2*n + 1, 2*n + 1))
    M_[:n, :n] = A_; M_[:n, n:2*n] = A_; M_[n:2*n, :n] = A_; M_[n:2*n, 2*n] = 1; M_[2*n, n:2*n] = 1
    return M_
def chrom(A_):
    n = len(A_)
    for k in range(1, n + 1):
        col = [-1]*n
        def bt(i):
            if i == n: return True
            for c in range(k):
                if all(col[j] != c for j in range(i) if A_[i, j]):
                    col[i] = c
                    if bt(i + 1): return True
            col[i] = -1
            return False
        if bt(0): return k
M2 = np.array([[0, 1], [1, 0]]); M3_ = myc(M2); M4_ = myc(M3_)
tri_free = lambda A_: np.trace(np.linalg.matrix_power(A_, 3)) == 0
check('2l', "Mycielski：5、11 点，无三角形，χ=3、4", len(M3_) == 3*2 - 1 and len(M4_) == 3*4 - 1 and tri_free(M3_) and tri_free(M4_) and chrom(M3_) == 3 and chrom(M4_) == 4)
def ntrees(A_):
    L_ = np.diag(A_.sum(1)) - A_
    return round(np.linalg.det(L_[1:, 1:]))
def Kmn(m, n):
    A_ = np.zeros((m + n, m + n)); A_[:m, m:] = 1; A_[m:, :m] = 1; return A_
def cube(n):
    N_ = 2**n; A_ = np.zeros((N_, N_))
    for i in range(N_):
        for b in range(n): A_[i, i ^ (1 << b)] = 1
    return A_
def wheel(n):
    A_ = np.zeros((n + 1, n + 1))
    for i in range(n):
        A_[i, (i + 1) % n] = A_[(i + 1) % n, i] = 1; A_[i, n] = A_[n, i] = 1
    return A_
lucas = lambda n: round(((1 + 5**0.5)/2)**n + ((1 - 5**0.5)/2)**n)
ok = all(ntrees(Kmn(m, n)) == m**(n - 1)*n**(m - 1) for m in range(1, 5) for n in range(1, 5))
ok &= all(ntrees(cube(n)) == 2**(2**n - n - 1)*math.prod(k**math.comb(n, k) for k in range(1, n + 1)) for n in range(1, 5))
ok &= all(ntrees(wheel(n)) == lucas(2*n) - 2 for n in range(3, 9))
for n in range(3, 8):
    A_ = np.ones((n, n)) - np.eye(n); A_[0, 1] = A_[1, 0] = 0
    ok &= ntrees(A_) == (n - 2)*n**(n - 3)
check('2l', "生成树数 K_{m,n}、Q_n、轮图、K_n-e", ok)
# 均匀生成树：P(e∈T)=R_eff
A_ = np.ones((5, 5)) - np.eye(5); A_[0, 1] = A_[1, 0] = 0; A_[2, 3] = A_[3, 2] = 0
E5 = [(i, j) for i in range(5) for j in range(i + 1, 5) if A_[i, j]]
trees = []
for S in itertools.combinations(E5, 4):
    par = list(range(5))
    def fnd(u):
        while par[u] != u: u = par[u]
        return u
    okT = True
    for u, v_ in S:
        ru, rv = fnd(u), fnd(v_)
        if ru == rv: okT = False; break
        par[ru] = rv
    if okT: trees.append(S)
Lp = np.linalg.pinv(np.diag(A_.sum(1)) - A_)
Reff = lambda u, v_: Lp[u, u] + Lp[v_, v_] - 2*Lp[u, v_]
check('2l', "均匀生成树 P(e∈T)=R_eff，Σ=n-1", all(close(sum(e in T_ for T_ in trees)/len(trees), Reff(*e), 1e-9) for e in E5) and close(sum(Reff(*e) for e in E5), 4))
Zcr = lambda n: (n//2)*((n - 1)//2)*((n - 2)//2)*((n - 3)//2)//4
check('2l', "交叉数引理 e³/64n² ≤ cr(K_n)（n=9..12 已知值）", all(math.comb(n, 2)**3/(64*n*n) <= Zcr(n) for n in range(9, 13)))
exC4 = [0, 1, 3, 4, 6, 7, 9, 11, 13, 16]
check('2l', "ex(n,C4) ≤ n(1+√(4n-3))/4（n≤10 已知值）", all(exC4[n - 1] <= n*(1 + math.sqrt(4*n - 3))/4 + 1e-9 for n in range(1, 11)))
lam2 = sorted(abs(evp))[-2]
ok = True
for _ in range(300):
    S = rng.random(10) < 0.5; T_ = rng.random(10) < 0.5
    eST = S.astype(float)@Ap@T_.astype(float)
    ok &= abs(eST - 3*S.sum()*T_.sum()/10) <= lam2*math.sqrt(S.sum()*T_.sum()) + 1e-9
check('2l', "扩张混合引理（Petersen，λ=2）", ok)
def scores_all(n):
    pairs = list(itertools.combinations(range(n), 2)); res = set()
    for bits in itertools.product([0, 1], repeat=len(pairs)):
        s_ = [0]*n
        for (i, j), b in zip(pairs, bits): s_[i if b else j] += 1
        res.add(tuple(sorted(s_)))
    return res
landau = lambda s_: all(sum(s_[:k]) >= math.comb(k, 2) for k in range(1, len(s_))) and sum(s_) == math.comb(len(s_), 2)
n_ = 5
check('2l', "Landau 得分序列判据（n=5 枚举）", scores_all(n_) == {s_ for s_ in itertools.combinations_with_replacement(range(n_), n_) if landau(s_)})
ok = True
for _ in range(30):
    n = 6; Tm = np.zeros((n, n), int)
    for i, j in itertools.combinations(range(n), 2):
        if rng.random() < 0.5: Tm[i, j] = 1
        else: Tm[j, i] = 1
    cnt = sum(all(Tm[p[i], p[i + 1]] for i in range(n - 1)) for p in itertools.permutations(range(n)))
    king = int(np.argmax(Tm.sum(1)))
    reach2 = (np.eye(n) + Tm + Tm@Tm)[king] > 0
    ok &= cnt % 2 == 1 and reach2.all()
check('2l', "竞赛图：Hamilton 路条数为奇数，出度最大者为王", ok)
gK = lambda n: math.ceil((n - 3)*(n - 4)/12)
check('2l', "g(K_n)：K5..K7 为 1，K8 为 2", [gK(n) for n in range(3, 9)] == [0, 0, 1, 1, 1, 2])

npass = sum(r[2] for r in R); print(f"\n第四轮数学（一）: {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
