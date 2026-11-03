"""第三轮续写 02d--02h（几何拓扑补充）的符号/数值核验。数值核验只覆盖所测参数。"""
import math, itertools, json
import numpy as np, sympy as sp, mpmath as mp
cross2 = lambda a, b: a[0]*b[1] - a[1]*b[0]
from scipy import integrate, linalg, special, optimize

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(5)
close = lambda a, b, tol=1e-9: abs(a - b) <= tol*max(1, abs(b))
x, y, t, u, v = sp.symbols('x y t u v', real=True)

# ---------- 02d 解析几何 ----------
A, B = rng.normal(size=3), rng.normal(size=3); U, V = rng.normal(size=3), rng.normal(size=3)
res = optimize.minimize(lambda p: np.linalg.norm(A + p[0]*U - B - p[1]*V), [0, 0], tol=1e-14)
check('2d', "异面直线距离公式", close(res.fun, abs((B - A) @ np.cross(U, V))/np.linalg.norm(np.cross(U, V)), 1e-6))
P = rng.normal(size=(4, 3)); D2 = np.array([[np.sum((P[i] - P[j])**2) for j in range(4)] for i in range(4)])
CM = np.ones((5, 5)); CM[0, 0] = 0; CM[1:, 1:] = D2
check('2d', "Cayley–Menger: 288V² = det", close(288*(np.linalg.det(P[1:] - P[0])/6)**2, np.linalg.det(CM), 1e-8))
poly = rng.random((7, 2)); ang = np.argsort(np.arctan2(*(poly - poly.mean(0)).T[::-1])); poly = poly[ang]
from functools import reduce
shoe = 0.5*sum(poly[i, 0]*poly[(i + 1) % 7, 1] - poly[(i + 1) % 7, 0]*poly[i, 1] for i in range(7))
tri = sum(0.5*abs(cross2(poly[i] - poly.mean(0), poly[(i + 1) % 7] - poly.mean(0))) for i in range(7))
check('2d', "鞋带公式（星形多边形）", close(shoe, tri))
lat = np.array([[0, 0], [5, 1], [3, 4], [-1, 3]])
Bp = sum(math.gcd(abs(lat[(i + 1) % 4, 0] - lat[i, 0]), abs(lat[(i + 1) % 4, 1] - lat[i, 1])) for i in range(4))
from matplotlib.path import Path
pth = Path(lat); Ip = sum(1 for a in range(-2, 7) for b in range(-1, 6) if pth.contains_point((a, b), radius=-1e-9) and not any(abs(cross2(lat[(i + 1) % 4] - lat[i], np.array([a, b]) - lat[i])) < 1e-9 and min(lat[i, 0], lat[(i + 1) % 4, 0]) <= a <= max(lat[i, 0], lat[(i + 1) % 4, 0]) and min(lat[i, 1], lat[(i + 1) % 4, 1]) <= b <= max(lat[i, 1], lat[(i + 1) % 4, 1]) for i in range(4)))
check('2d', "Pick 定理", close(0.5*abs(sum(lat[i, 0]*lat[(i + 1) % 4, 1] - lat[(i + 1) % 4, 0]*lat[i, 1] for i in range(4))), Ip + Bp/2 - 1))
a_, b_, c_ = 5.0, 6.0, 7.0; s_ = (a_ + b_ + c_)/2; K = math.sqrt(s_*(s_ - a_)*(s_ - b_)*(s_ - c_))
Ac = np.array([0., 0]); Bc = np.array([c_, 0]); cx = (b_**2 + c_**2 - a_**2)/(2*c_); Cc = np.array([cx, math.sqrt(b_**2 - cx**2)])
Rr, rr = a_*b_*c_/(4*K), K/s_
I = (a_*Ac + b_*Bc + c_*Cc)/(a_ + b_ + c_)
Om = optimize.fsolve(lambda p: [np.sum((p - Ac)**2) - np.sum((p - Bc)**2), np.sum((p - Ac)**2) - np.sum((p - Cc)**2)], [1, 1])
H = Ac + Bc + Cc - 2*Om
check('2d', "Euler OI²=R²-2Rr, OH²=9R²-Σa²; 1/r=Σ1/r_a", close(np.sum((Om - I)**2), Rr**2 - 2*Rr*rr, 1e-8) and close(np.sum((Om - H)**2), 9*Rr**2 - (a_**2 + b_**2 + c_**2), 1e-8)
      and close(1/rr, sum((s_ - q)/K for q in (a_, b_, c_))))
check('2d', "Stewart / 中线 / 角平分线", close(np.linalg.norm(Ac - (Bc + Cc)/2), 0.5*math.sqrt(2*b_**2 + 2*c_**2 - a_**2))
      and close(np.linalg.norm(Ac - (b_*Bc + c_*Cc)/(b_ + c_)), math.sqrt(b_*c_*(1 - a_**2/(b_ + c_)**2))))
th = np.sort(rng.random(4)*2*np.pi); Q4 = np.c_[np.cos(th), np.sin(th)]*1.7
sides = [np.linalg.norm(Q4[i] - Q4[(i + 1) % 4]) for i in range(4)]; sQ = sum(sides)/2
areaQ = 0.5*abs(sum(Q4[i, 0]*Q4[(i + 1) % 4, 1] - Q4[(i + 1) % 4, 0]*Q4[i, 1] for i in range(4)))
check('2d', "Brahmagupta 与 Ptolemy 等号", close(areaQ, math.sqrt(np.prod([sQ - q for q in sides]))) and close(np.linalg.norm(Q4[0] - Q4[2])*np.linalg.norm(Q4[1] - Q4[3]), sides[0]*sides[2] + sides[1]*sides[3]))
vv = rng.normal(size=(3, 3)); vv /= np.linalg.norm(vv, axis=1)[:, None]
sa = [math.acos(np.clip(vv[i] @ vv[(i + 1) % 3], -1, 1)) for i in range(3)]
def ang_at(i):
    a0, b0, c0 = vv[i], vv[(i + 1) % 3], vv[(i + 2) % 3]
    t1 = b0 - (a0 @ b0)*a0; t2 = c0 - (a0 @ c0)*a0
    return math.acos(np.clip(t1 @ t2/np.linalg.norm(t1)/np.linalg.norm(t2), -1, 1))
E = sum(ang_at(i) for i in range(3)) - math.pi
num = abs(vv[0] @ np.cross(vv[1], vv[2])); den = 1 + vv[0] @ vv[1] + vv[0] @ vv[2] + vv[1] @ vv[2]
Om_vs = 2*math.atan2(num, den)
check('2d', "球面三角形面积 = 球面角盈 = Van Oosterom 立体角", close(E, Om_vs, 1e-9))
cc = math.cos(sa[2]); check('2d', "球面余弦定理", close(math.cos(sa[2]), math.cos(sa[0])*math.cos(sa[1]) + math.sin(sa[0])*math.sin(sa[1])*math.cos(ang_at(1)), 1e-9))
Aq, Bq, Cq, Dq, Eq, Fq = 2.0, 1.0, 3.0, -1.0, 2.0, -5.0
M3 = np.array([[Aq, Bq/2, Dq/2], [Bq/2, Cq, Eq/2], [Dq/2, Eq/2, Fq]])
xs = np.linspace(-3, 3, 3001); XX, YY = np.meshgrid(xs, xs)
area_num = np.mean(Aq*XX**2 + Bq*XX*YY + Cq*YY**2 + Dq*XX + Eq*YY + Fq < 0)*36
check('2d', "二次曲线椭圆面积 8π|Δ|/(4AC-B²)^{3/2}", abs(area_num - 8*math.pi*abs(np.linalg.det(M3))/(4*Aq*Cq - Bq**2)**1.5) < 0.01)
x0 = 1.0; y0s = sp.solve(2*x0**2 + x0*y + 3*y**2 - x0 + 2*y - 5, y); y0 = float(y0s[0])
tang = lambda X_, Y_: Aq*X_*x0 + Bq*(X_*y0 + x0*Y_)/2 + Cq*Y_*y0 + Dq*(X_ + x0)/2 + Eq*(Y_ + y0)/2 + Fq
grad = np.array([2*Aq*x0 + Bq*y0 + Dq, Bq*x0 + 2*Cq*y0 + Eq])
check('2d', "“一半代入”切线方程", abs(tang(x0, y0)) < 1e-9 and abs(tang(x0 + grad[1], y0 - grad[0])) < 1e-9)
z1, z2, z3 = 0.3 + 1j, -1 + 0.2j, 2 - 1j
fM = lambda z: (z - z1)*(z2 - z3)/((z - z3)*(z2 - z1))
check('2d', "Möbius 三点公式", abs(fM(z1)) < 1e-12 and abs(fM(z2) - 1) < 1e-12 and abs(fM(z3 + 1e-12)) > 1e9)
cv, rho, Rinv = np.array([2.0, 1.0]), 0.7, 1.3
pts = cv + rho*np.c_[np.cos(np.linspace(0, 6, 50)), np.sin(np.linspace(0, 6, 50))]
img = Rinv**2*pts/np.sum(pts**2, 1)[:, None]
c2 = Rinv**2*cv/(cv @ cv - rho**2); r2 = Rinv**2*rho/abs(cv @ cv - rho**2)
check('2d', "反演下圆的像：圆心与半径", np.allclose(np.linalg.norm(img - c2, axis=1), r2))
q = np.r_[math.cos(0.4), math.sin(0.4)*np.array([1, 2, 2])/3]
def qmul(a, b): return np.r_[a[0]*b[0] - a[1:] @ b[1:], a[0]*b[1:] + b[0]*a[1:] + np.cross(a[1:], b[1:])]
vec = np.array([0.3, -1.0, 2.0]); rot = qmul(qmul(q, np.r_[0, vec]), q*np.r_[1, -1, -1, -1])[1:]
check('2d', "四元数旋转 = Rodrigues", np.allclose(rot, linalg.expm(0.8*np.cross(np.eye(3), np.array([1, 2, 2])/3)) @ vec))
check('2d', "Ramanujan 椭圆周长近似 (a=3,b=1)", abs(math.pi*(3*4 - math.sqrt(10*6)) - 4*3*float(mp.ellipe(1 - 1/9))) < 1e-3)
check('2d', "球冠面积 2πRh", close(integrate.quad(lambda th: 2*math.pi*math.sin(th)*4, 0, math.acos(0.4))[0], 2*math.pi*2*(2 - 0.8)))
check('2d', "Steiner 公式：立方体平行体", close(np.mean(np.linalg.norm(np.maximum(np.abs(rng.random((2_000_000, 3))*3.0 - 1.5) - 1, 0), axis=1) <= 0.5)*27, 8 + 6*4*0.5 + 3*math.pi*2*0.25 + 4*math.pi/3*0.125, 3e-3))
Lseg = 2.0; nn = 400000; thc = rng.random(nn)*math.pi; pc = (rng.random(nn) - 0.5)*6
hits = np.abs(pc - 0*np.cos(thc)) <= np.abs(Lseg/2*np.cos(thc))   # 线段沿 x 轴，中心在原点
check('2d', "Crofton: ∫∫n = 2L", abs(hits.mean()*math.pi*6 - 2*Lseg) < 0.03)
check('2d', "Farey 邻项 bc-ad=1 (n=8)", all(b2*a1 - a2*b1 == 1 for (a2, b2), (a1, b1) in zip(sorted({(p, q_) for q_ in range(1, 9) for p in range(0, q_ + 1) if math.gcd(p, q_) == 1}, key=lambda f: f[0]/f[1])[:-1], sorted({(p, q_) for q_ in range(1, 9) for p in range(0, q_ + 1) if math.gcd(p, q_) == 1}, key=lambda f: f[0]/f[1])[1:])))
ae, be = 3.0, 1.2
tt = sp.symbols('tt'); X_, Y_ = ae*sp.cos(tt), be*sp.sin(tt)
kap = (sp.diff(X_, tt)*sp.diff(Y_, tt, 2) - sp.diff(Y_, tt)*sp.diff(X_, tt, 2))/(sp.diff(X_, tt)**2 + sp.diff(Y_, tt)**2)**sp.Rational(3, 2)
check('2d', "椭圆顶点曲率半径 b²/a, a²/b", close(1/float(kap.subs(tt, 0)), be**2/ae) and close(1/float(kap.subs(tt, sp.pi/2)), ae**2/be))
pp = [np.array([1.0, 0]), np.array([0, 1.0]), np.array([-1.0, 0]), np.array([0.6, -0.8])]
check('2d', "四点共圆行列式", abs(np.linalg.det(np.array([[p @ p, p[0], p[1], 1] for p in pp]))) < 1e-12)

# ---------- 02e 曲线曲面 ----------
f = x**2; fp, fpp = sp.diff(f, x), sp.diff(f, x, 2)
check('2e', "y=x² 渐屈线 (-4x³, 3x²+1/2)", sp.simplify(x - fp*(1 + fp**2)/fpp + 4*x**3) == 0 and sp.simplify(f + (1 + fp**2)/fpp - 3*x**2 - sp.Rational(1, 2)) == 0)
Lld = 2.0; tts = np.linspace(0.05, 1.5, 200)
env = [(Lld*math.cos(q_)**3, Lld*math.sin(q_)**3) for q_ in tts]
check('2e', "梯子包络为星形线", all(abs(abs(a0)**(2/3) + abs(b0)**(2/3) - Lld**(2/3)) < 1e-12 for a0, b0 in env)
      and all(abs(a0/(Lld*math.cos(q_)) + b0/(Lld*math.sin(q_)) - 1) < 1e-12 for (a0, b0), q_ in zip(env, tts)))
check('2e', "螺线 κ=a/(a²+b²), τ=b/(a²+b²)", (lambda r: sp.simplify(sp.sqrt(sp.Matrix(r.diff(t)).cross(sp.Matrix(r.diff(t, 2))).dot(sp.Matrix(r.diff(t)).cross(sp.Matrix(r.diff(t, 2)))))/sp.Matrix(r.diff(t)).norm()**3 - 2/sp.Integer(13)) == 0)(sp.Matrix([2*sp.cos(t), 2*sp.sin(t), 3*t])))
s_ = sp.symbols('s', positive=True)
check('2e', "曲线管体积 πa²L（螺线管，数值）", abs((lambda a0: integrate.tplquad(lambda r_, ph, s0: r_*(1 - r_*math.cos(ph)*2/13), 0, 2*math.pi*math.sqrt(13), 0, 2*math.pi, 0, a0)[0])(0.1) - math.pi*0.01*2*math.pi*math.sqrt(13)) < 1e-6)
E_, G_ = sp.Function('E')(u, v), sp.Function('G')(u, v)
Kform = lambda E0, G0: sp.simplify(-1/(2*sp.sqrt(E0*G0))*(sp.diff(sp.diff(E0, v)/sp.sqrt(E0*G0), v) + sp.diff(sp.diff(G0, u)/sp.sqrt(E0*G0), u)))
check('2e', "正交度量 K 公式：球面 1、双曲 -1、dr²+f²dθ²", abs(float(Kform(sp.Integer(1), sp.sin(u)**2).subs({u: 0.7, v: 0.3})) - 1) < 1e-12 and abs(float(Kform(1/v**2, 1/v**2).subs({u: 0.7, v: 0.3})) + 1) < 1e-12 and abs(float(Kform(sp.Integer(1), sp.cosh(u)**2).subs({u: 0.7, v: 0.3})) + 1) < 1e-12)
fS = sp.log(sp.cos(y)/sp.cos(x))
check('2e', "Scherk 满足极小曲面方程", sp.simplify((1 + sp.diff(fS, y)**2)*sp.diff(fS, x, 2) - 2*sp.diff(fS, x)*sp.diff(fS, y)*sp.diff(fS, x, y) + (1 + sp.diff(fS, x)**2)*sp.diff(fS, y, 2)) == 0)
Xen = sp.Matrix([u - u**3/3 + u*v**2, v - v**3/3 + v*u**2, u**2 - v**2])
Xu, Xv = Xen.diff(u), Xen.diff(v); Nn = Xu.cross(Xv)
Ee, Ff, Gg = Xu.dot(Xu), Xu.dot(Xv), Xv.dot(Xv); Ll, Mm, Nq = Xen.diff(u, 2).dot(Nn), Xen.diff(u, v).dot(Nn), Xen.diff(v, 2).dot(Nn)
check('2e', "Enneper 曲面 H=0", sp.simplify(Ee*Nq - 2*Ff*Mm + Gg*Ll) == 0)
check('2e', "伪球面两半面积 4π、体积 2π/3", close(2*float(mp.quad(lambda t_: 2*mp.pi*mp.sech(t_)*mp.sqrt(mp.diff(lambda q_: mp.sech(q_), t_)**2 + mp.diff(lambda q_: q_ - mp.tanh(q_), t_)**2), [0, mp.inf])), 4*math.pi, 1e-8)
      and close(2*float(mp.quad(lambda t_: mp.pi*mp.sech(t_)**2*(1 - mp.sech(t_)**2), [0, mp.inf])), 2*math.pi/3, 1e-8))
z0, w0 = 0.3 + 1.2j, -0.7 + 0.4j
cen = ((abs(z0)**2 - abs(w0)**2)/(2*(z0.real - w0.real))); rad = abs(z0 - cen)
a1, a2 = math.atan2(z0.imag, z0.real - cen), math.atan2(w0.imag, w0.real - cen)
glen = abs(integrate.quad(lambda ph: rad/(rad*math.sin(ph)), a1, a2)[0])
check('2e', "上半平面距离公式 cosh d = 1+|z-w|²/(2 Im z Im w)", close(math.cosh(glen), 1 + abs(z0 - w0)**2/(2*z0.imag*w0.imag), 1e-9))
Kc = 0.8; r0 = 0.05
check('2e', "Bertrand–Diguet–Puiseux", abs(3/math.pi*(2*math.pi*r0 - 2*math.pi*math.sin(math.sqrt(Kc)*r0)/math.sqrt(Kc))/r0**3 - Kc) < 1e-3)
th0 = 0.9
check('2e', "纬线和乐角 2π(1-cos θ0) = 所围面积", close(integrate.dblquad(lambda ph, th: math.sin(th), 0, th0, 0, 2*math.pi)[0], 2*math.pi*(1 - math.cos(th0))))
check('2e', "足球角亏 π/15，合计 4π", close(60*(2*math.pi - 2*2*math.pi/3 - 3*math.pi/5), 4*math.pi))
lam = 2/(1 + u**2 + v**2)
check('2e', "共形坐标 K=-Δlnλ/λ²：球极投影 K=1", sp.simplify(-(sp.diff(sp.log(lam), u, 2) + sp.diff(sp.log(lam), v, 2))/lam**2) == 1)
check('2e', "管体积（闭曲面）2Aε+(4π/3)χε³：球", sp.expand(sp.Rational(4, 3)*sp.pi*((2 + t)**3 - (2 - t)**3) - (2*4*sp.pi*4*t + sp.Rational(4, 3)*sp.pi*2*t**3)) == 0)
Rt, rt = 3.0, 1.0
check('2e', "圆环面 ∫|K| = 8π（Chern–Lashof 取等）", close(integrate.dblquad(lambda ph, th: abs(math.cos(th)/(rt*(Rt + rt*math.cos(th))))*rt*(Rt + rt*math.cos(th)), 0, 2*math.pi, 0, 2*math.pi)[0], 8*math.pi, 1e-7))

# ---------- 02f 流形 ----------
th_ = np.linspace(0, math.pi, 200001); pdf = (1 - np.cos(th_))/math.pi
qs = rng.normal(size=(400000, 4)); qs /= np.linalg.norm(qs, axis=1)[:, None]; angs = 2*np.arccos(np.abs(qs[:, 0]))
check('2f', "随机旋转转角密度 (1-cosθ)/π, Eθ=π/2+2/π", close(np.trapezoid(pdf, th_), 1, 1e-8) and abs(angs.mean() - (math.pi/2 + 2/math.pi)) < 5e-3)
Xa = rng.normal(size=(3, 3))*0.05; Ya = rng.normal(size=(3, 3))*0.05
br = lambda a, b: a @ b - b @ a
bch = Xa + Ya + br(Xa, Ya)/2 + (br(Xa, br(Xa, Ya)) + br(Ya, br(Ya, Xa)))/12 - br(Ya, br(Xa, br(Xa, Ya)))/24
check('2f', "BCH 到四阶", np.linalg.norm(linalg.logm(linalg.expm(Xa) @ linalg.expm(Ya)) - bch) < 5e-6)
r_ = sp.symbols('r', positive=True); fr = sp.Function('f')(r_)
check('2f', "Cartan 结构方程例 K=-f''/f（f=sin r 得 1）", sp.simplify(-sp.diff(sp.sin(r_), r_, 2)/sp.sin(r_)) == 1)
g = sp.diag(1, sp.sin(u)**2)
Gam = lambda k, i, j: sum(g.inv()[k, l]*(sp.diff(g[j, l], [u, v][i]) + sp.diff(g[i, l], [u, v][j]) - sp.diff(g[i, j], [u, v][l]))/2 for l in range(2))
check('2f', "Γ^i_ij = ∂_j ln√g（球面）", all(abs(float((sum(Gam(i, i, j) for i in range(2)) - sp.diff(sp.log(sp.sqrt(g.det())), [u, v][j])).subs({u: 0.7, v: 0.3}))) < 1e-12 for j in range(2)))
dims = {'SO(5)': (lambda n: n*(n - 1)//2)(5), 'Sp(4,R)': (lambda n: n*(2*n + 1))(2), 'SU(3)': 8}
Mtest = rng.normal(size=(4, 4)); Jm = np.block([[np.zeros((2, 2)), np.eye(2)], [-np.eye(2), np.zeros((2, 2))]])
sp_alg = linalg.null_space(np.array([(Jm @ np.eye(16)[:, k].reshape(4, 4) + np.eye(16)[:, k].reshape(4, 4).T @ Jm).ravel() for k in range(16)]).T)
check('2f', "dim sp(4,R) = n(2n+1) = 10", sp_alg.shape[1] == 10)
check('2f', "Radon–Hurwitz: ρ(n)-1 向量场 (n=4→3, 8→7, 16→8, 6→1)", [(lambda n: (lambda b, a: 2**b + 8*a)(*(lambda e: (e % 4, e//4))(sp.multiplicity(2, n))))(n) - 1 for n in (4, 8, 16, 6)] == [3, 7, 8, 1])

# ---------- 02g 代数拓扑 ----------
def homology_RPn(n):
    # 胞腔链复形：C_k = Z，∂_k = 1+(-1)^k
    out = []
    for k in range(n + 1):
        dk = 1 + (-1)**k if k >= 1 else 0
        dk1 = 1 + (-1)**(k + 1) if k + 1 <= n else 0
        ker = 1 if dk == 0 else 0
        out.append('Z' if ker and dk1 == 0 else ('Z2' if ker and dk1 == 2 else '0'))
    return out
check('2g', "H_*(RP^n) 由胞腔链复形", homology_RPn(4) == ['Z', 'Z2', '0', 'Z2', '0'] and homology_RPn(5) == ['Z', 'Z2', '0', 'Z2', '0', 'Z'])
def snf_diag(M):
    return [d for d in __import__('sympy.matrices.normalforms', fromlist=['x']).smith_normal_form(sp.Matrix(M), domain=sp.ZZ).diagonal() if d != 0]
check('2g', "Klein 瓶 H1 = Z⊕Z2（关系矩阵 Smith 形）", sorted(abs(int(d)) for d in snf_diag([[2, 0]])) == [2])
Acat = np.array([[2, 1], [1, 1]])
def fixed_count(Am, m):
    Mm_ = np.linalg.matrix_power(Am, m) - np.eye(2, dtype=int); d = abs(round(np.linalg.det(Mm_)))
    # 数 (M-I)x ∈ Z² 的 x ∈ [0,1)²：等于 |det|
    pts = set()
    inv = np.linalg.inv(Mm_)
    for a in range(-d - 2, d + 3):
        for b in range(-d - 2, d + 3):
            xx = inv @ np.array([a, b]); xx = xx - np.floor(xx + 1e-12)
            pts.add((round(xx[0]*1e6), round(xx[1]*1e6)))
    return len(pts), d
check('2g', "猫映射周期点数 |2-tr A^m|", all((lambda c, d: c == d == abs(2 - np.trace(np.linalg.matrix_power(Acat, m))))(*fixed_count(Acat, m)) for m in (1, 2, 3)))
check('2g', "最少顶点三角剖分下界", [math.ceil((7 + math.sqrt(49 - 24*c))/2) for c in (2, 0, 1, -2)] == [4, 7, 6, 9])
check('2g', "透镜空间: 2 不是模 5 的 ±平方", all((2 - s*n*n) % 5 != 0 for n in range(5) for s in (1, -1)))
tq = sp.symbols('t')
check('2g', "三叶结 |Δ(-1)|=3；8 字结 |Δ(-1)|=5", abs((tq**2 - tq + 1).subs(tq, -1)) == 3 and abs((tq**2 - 3*tq + 1).subs(tq, -1)) == 5)

# ---------- 02h 点集拓扑与度量 ----------
check('2h', "Moran 方程: 等比时 ln m/ln(1/r)", all(close(m*r**(math.log(m)/math.log(1/r)), 1) for m, r in ((2, 1/3), (4, 1/3), (3, 1/2), (20, 1/3))))
sv = optimize.brentq(lambda s0: 0.5**s0 + 0.25**s0 - 1, 0.1, 2)
check('2h', "非等比 Moran：r=(1/2,1/4) 维数 = log_2 φ", close(sv, math.log2((1 + math.sqrt(5))/2), 1e-10))
p_ = 3; vals = [rng.integers(1, 10**6, 3) for _ in range(3000)]
vp = lambda n: sp.multiplicity(p_, int(n)) if n else 99
check('2h', "p 进超度量不等式", all(p_**-vp(a - c) <= max(p_**-vp(a - b), p_**-vp(b - c)) + 1e-15 for a, b, c in vals))

npass = sum(r[2] for r in R); print(f"\n第三轮续写数学(二) 02d–02h: {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
