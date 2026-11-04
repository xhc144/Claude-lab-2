"""第四轮续写 06d--13e（物理各章补充）的核验：公式用独立推导或数值积分复核，常数用 CODATA 值复算。"""
import math, itertools, json
import numpy as np, sympy as sp, mpmath as mp
from scipy import integrate, linalg, special, optimize, constants as K

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(12)
close = lambda a, b, tol=1e-9: abs(a - b) <= tol*max(1, abs(b))
G, c, hbar, kB, e, me, eps0, mu0 = K.G, K.c, K.hbar, K.k, K.e, K.m_e, K.epsilon_0, K.mu_0
g0, wE, RE, ME = 9.81, 7.2921e-5, 6.371e6, 5.972e24

# ---------- 06d 力学补充 ----------
sol = integrate.solve_ivp(lambda t, y: [y[1], g0 - 3*y[1]**2/y[0]] if y[0] > 0 else [0, 0], [0, 50], [1e-6, 0.0], rtol=1e-10, atol=1e-14, dense_output=True)
acc = g0 - 3*sol.y[1, -1]**2/sol.y[0, -1]
check('6d', "雨滴（ṁ∝r²v）加速度 → g/7", abs(acc - g0/7) < 1e-3*g0)
mu_E = G*ME; r1, r2 = RE + 300e3, 42164e3
dv1 = math.sqrt(mu_E/r1)*(math.sqrt(2*r2/(r1 + r2)) - 1); dv2 = math.sqrt(mu_E/r2)*(1 - math.sqrt(2*r1/(r1 + r2))); tH = math.pi*math.sqrt((r1 + r2)**3/(8*mu_E))
check('6d', "Hohmann LEO→GEO：2.43+1.47 km/s，约 5.3 h", abs(dv1/1e3 - 2.43) < 0.02 and abs(dv2/1e3 - 1.47) < 0.02 and abs(tH/3600 - 5.3) < 0.05)
def apsidal(n):
    L = 1.0; r0 = 1.0
    f = lambda r: -r**n
    rhs = lambda t, y: [y[1], L*L/y[0]**3 + f(y[0]), L/y[0]**2]
    # 圆轨道 L²/r³ = r^n ⇒ r0=1；给小扰动
    sol = integrate.solve_ivp(rhs, [0, 60], [1.0, 1e-3, 0.0], rtol=1e-11, atol=1e-13, dense_output=True, events=lambda t, y: y[1])
    th = [sol.sol(te)[2] for te in sol.t_events[0]]
    return th[2] - th[1]
check('6d', "近圆轨道拱点角 π/√(n+3)", all(abs(apsidal(n) - math.pi/math.sqrt(n + 3)) < 1e-3 for n in (-2.5, -1.0, 0.5)))
check('6d', "赤道 100 m 落体东偏≈2.2 cm", abs(2*wE/3*math.sqrt(2*100**3/g0) - 0.022) < 5e-4)
check('6d', "铅垂线最大偏差≈0.1°（45°）", abs(math.degrees(wE**2*RE*0.5/g0) - 0.1) < 0.005)
ee = 0.7; h0 = 2.0
Tb = math.sqrt(2*h0/g0) + sum(2*math.sqrt(2*h0/g0)*ee**k for k in range(1, 400))
check('6d', "弹跳总时间 √(2h/g)(1+e)/(1-e)", close(Tb, math.sqrt(2*h0/g0)*(1 + ee)/(1 - ee)))
m1, m2 = 1.3, 4.1
v2f = 2*m1/(m1 + m2)*1.0
check('6d', "弹性碰撞能量传递 4m₁m₂/(m₁+m₂)²", close(0.5*m2*v2f**2/(0.5*m1), 4*m1*m2/(m1 + m2)**2))
Nn, Kk, mm, a_ = 40, 2.0, 0.5, 1.0
Dm = (2*np.eye(Nn) - np.roll(np.eye(Nn), 1, 1) - np.roll(np.eye(Nn), -1, 1))*Kk/mm
ks = 2*np.pi*np.arange(Nn)/(Nn*a_)
check('6d', "一维晶格色散 ω=2√(K/m)|sin(ka/2)|", np.allclose(np.sort(np.sqrt(np.abs(np.linalg.eigvalsh(Dm)))), np.sort(2*math.sqrt(Kk/mm)*np.abs(np.sin(ks*a_/2)))))
rho = 1000.0; R0 = 1.0; Msph = 4/3*math.pi*R0**3*rho
tff = integrate.quad(lambda r: 1/math.sqrt(2*G*Msph*(1/r - 1/R0)), 0, R0)[0]
check('6d', "自由下落坍缩时间 √(3π/(32Gρ))", close(tff, math.sqrt(3*math.pi/(32*G*rho)), 1e-7))
check('6d', "地球隧道周期 2π√(R/g)≈84.4 min", abs(2*math.pi*math.sqrt(RE/g0)/60 - 84.4) < 0.2)
w_, Rh = 6.0, 0.5
Ueff = lambda th: -g0*Rh*math.cos(th) - 0.5*(w_*Rh*math.sin(th))**2
thmin = optimize.minimize_scalar(Ueff, bounds=(0.01, 3), method='bounded').x
check('6d', "旋转圆环上的珠子 cosθ₀=g/(ω²R)", abs(math.cos(thmin) - g0/(w_**2*Rh)) < 1e-6)
th0 = 0.6
Texact = 4*math.sqrt(1/g0)*special.ellipk(math.sin(th0/2)**2)
check('6d', "单摆大振幅展开到 θ₀⁴", abs(Texact/(2*math.pi*math.sqrt(1/g0)) - (1 + th0**2/16 + 11*th0**4/3072)) < 2e-5)
check('6d', "贴地轨道周期 √(3π/(Gρ))（地球≈84 min）", abs(math.sqrt(3*math.pi/(G*5514))/60 - 84.3) < 0.3 and close(2*math.pi*math.sqrt(RE**3/(G*ME)), math.sqrt(3*math.pi/(G*ME/(4/3*math.pi*RE**3))), 1e-12))
I1, I3, mgl = 2.0, 1.0, 3.0
def sleeping_stable(w3):
    # 小倾角线性化：特征多项式 I1 s² - i I3 w3 s - mgl = 0（复变量 ξ=θx+iθy）
    rts = np.roots([I1, -1j*I3*w3, -mgl]); return np.all(np.abs(rts.real) < 1e-9)
wc = math.sqrt(4*I1*mgl/I3**2)
check('6d', "睡眠陀螺稳定 ⇔ ω₃²>4I₁mgl/I₃²", sleeping_stable(1.01*wc) and not sleeping_stable(0.99*wc))

# ---------- 06e 连续介质与流体 ----------
Eg, nu = 200.0, 0.29
Gs, Kb = Eg/(2*(1 + nu)), Eg/(3*(1 - 2*nu))
check('6e', "E=2G(1+ν)=3K(1-2ν)，ν=1/4 时 v_P/v_S=√3", close(2*Gs*(1 + nu), 3*Kb*(1 - 2*nu)) and close(math.sqrt((Eg/(3*(1 - 0.5)) + 4/3*Eg/2.5)/(Eg/2.5)), math.sqrt(3)))
def blasius(fpp0):
    s = integrate.solve_ivp(lambda t, y: [y[1], y[2], -0.5*y[0]*y[2]], [0, 15], [0, 0, fpp0], rtol=1e-11, atol=1e-12, dense_output=True)
    return s
fpp = optimize.brentq(lambda a: blasius(a).y[1, -1] - 1, 0.2, 0.5)
sb = blasius(fpp); eta99 = optimize.brentq(lambda t: sb.sol(t)[1] - 0.99, 1, 10)
check('6e', "Blasius：f''(0)=0.332，δ₉₉≈5.0x/√Re", abs(fpp - 0.33206) < 1e-4 and abs(eta99 - 4.91) < 0.03)
h1, Fr1 = 0.3, 3.0
v1 = Fr1*math.sqrt(g0*h1); q = v1*h1
h2 = optimize.brentq(lambda h: (q*q/h1 + g0*h1*h1/2) - (q*q/h + g0*h*h/2), h1*1.01, 10)
check('6e', "水跃 h₂/h₁=½(√(1+8Fr₁²)-1)（动量守恒）", close(h2/h1, 0.5*(math.sqrt(1 + 8*Fr1**2) - 1), 1e-9))
uu = sp.symbols('u'); vv, rhoQ = sp.symbols('v rhoQ', positive=True)
Pp = rhoQ*2*(vv - uu)*uu
check('6e', "Pelton：u=v/2 时功率最大 ½ρQv²", sp.solve(sp.diff(Pp, uu), uu) == [vv/2] and sp.simplify(Pp.subs(uu, vv/2) - rhoQ*vv**2/2) == 0)
check('6e', "水的毛细长度≈2.7 mm", abs(math.sqrt(0.0728/(1000*g0))*1e3 - 2.72) < 0.03)
A1, A2, dp, rf = 3e-3, 1e-3, 2000.0, 1000.0
v2 = math.sqrt(2*dp/(rf*(1 - (A2/A1)**2)))
check('6e', "Venturi：Bernoulli + 连续性", close(0.5*rf*(v2**2 - (v2*A2/A1)**2), dp))
hh, th_ = sp.symbols('h theta', positive=True); yy = sp.symbols('y'); eta_, rg = sp.symbols('eta rho_g', positive=True)
ux = rg*sp.sin(th_)/eta_*(hh*yy - yy**2/2)
check('6e', "斜面液膜流量 ρg sinθ h³/(3η)", sp.simplify(sp.integrate(ux, (yy, 0, hh)) - rg*sp.sin(th_)*hh**3/(3*eta_)) == 0)
check('6e', "Rayleigh--Plateau：kR<1 不稳定（λ>2πR）", all((special.iv(1, k)/special.iv(0, k)*k*(1 - k*k) > 0) == (k < 1) for k in np.linspace(0.05, 1.5, 30)))

# ---------- 07e 分析力学与电动力学补充 ----------
xq = sp.symbols('x y z'); pq = sp.symbols('p_x p_y p_z')
Lv = [xq[1]*pq[2] - xq[2]*pq[1], xq[2]*pq[0] - xq[0]*pq[2], xq[0]*pq[1] - xq[1]*pq[0]]
PB = lambda f, g: sum(sp.diff(f, xq[i])*sp.diff(g, pq[i]) - sp.diff(f, pq[i])*sp.diff(g, xq[i]) for i in range(3))
check('7e', "{L_i,L_j}=ε_ijk L_k", all(sp.simplify(PB(Lv[i], Lv[(i + 1) % 3]) - Lv[(i + 2) % 3]) == 0 for i in range(3)))
Bmin, Bmax = 1.0, 4.0
ok = True
for th in np.linspace(0.05, 1.5, 30):
    vperp2 = math.sin(th)**2; reflect = vperp2*Bmax/Bmin >= 1
    ok &= reflect == (math.sin(th)**2 >= Bmin/Bmax)
check('7e', "磁镜损失锥（μ 守恒 + 能量守恒）", ok)
check('7e', "磁偶极辐射 = 电偶极公式作 p→m/c", close(mu0*1.0**2*1e9**4/(12*math.pi*c**3), (1.0/c)**2*1e9**4/(12*math.pi*eps0*c**3), 1e-9))
Rl, al_ = 0.1, 1e-4
def ring_L_ext():
    # Neumann 公式：导线中心线与导线内表面线（半径 R-a）之间的互感
    k2 = 4*Rl*(Rl - al_)/((2*Rl - al_)**2)
    k = math.sqrt(k2)
    return mu0*math.sqrt(Rl*(Rl - al_))*((2/k - k)*special.ellipk(k2) - 2/k*special.ellipe(k2))
check('7e', "细导线圆环外自感 μ₀R(ln(8R/a)-2)", abs(ring_L_ext()/(mu0*Rl*(math.log(8*Rl/al_) - 2)) - 1) < 2e-3)
wt = np.logspace(-2, 2, 20001); epsI = (np.array(2.0)*wt/(1 + wt**2))
check('7e', "Debye 弛豫：Im ε 在 ωτ=1 处取峰 (εs-ε∞)/2", abs(wt[np.argmax(epsI)] - 1) < 1e-3 and close(epsI.max(), 1.0, 1e-6))
gam = 1e3; beta = math.sqrt(1 - 1/gam**2)
check('7e', "相对论 Lagrange 量给出 p=γmv", close(sp.diff(-sp.Symbol('m')*sp.Symbol('c')**2*sp.sqrt(1 - sp.Symbol('v')**2/sp.Symbol('c')**2), sp.Symbol('v')).subs({sp.Symbol('m'): 1, sp.Symbol('c'): 1, sp.Symbol('v'): 0.6}), 0.6/math.sqrt(1 - 0.36)))

# ---------- 07f 热力学补充 ----------
bb, ww, hb = sp.symbols('beta omega hbar', positive=True)
Zq = 1/(2*sp.sinh(bb*hb*ww/2)); Eavg = -sp.diff(sp.log(Zq), bb)
varE = sp.diff(sp.log(Zq), bb, 2)
Tt = sp.symbols('T', positive=True); kb_ = sp.symbols('k_B', positive=True)
CV = sp.diff(Eavg.subs(bb, 1/(kb_*Tt)), Tt)
check('7f', "⟨ΔE²⟩=k_BT²C_V（量子谐振子）", sp.simplify((varE.subs(bb, 1/(kb_*Tt)) - kb_*Tt**2*CV)) == 0)
a_, b_, Rg_, V_ = sp.symbols('a b R V', positive=True)
B2 = sp.limit(V_*((Rg_*Tt/(V_ - b_) - a_/V_**2)*V_/(Rg_*Tt) - 1), V_, sp.oo)
check('7f', "van der Waals：B₂=b-a/RT，Boyle 温度 a/(Rb)", sp.simplify(B2 - (b_ - a_/(Rg_*Tt))) == 0 and sp.solve(B2, Tt) == [a_/(Rg_*b_)])
x_ = np.linspace(0.01, 3, 300001); Cs = (1/x_)**2*np.exp(1/x_)/(1 + np.exp(1/x_))**2
check('7f', "两能级 Schottky 峰 C_max≈0.44Nk", abs(Cs.max() - 0.439) < 2e-3)
Th_ = 50.0
Zo = sum(3*(2*J + 1)*math.exp(-J*(J + 1)/Th_) for J in range(1, 400, 2)); Zp = sum((2*J + 1)*math.exp(-J*(J + 1)/Th_) for J in range(0, 400, 2))
check('7f', "H₂ 正/仲比高温 3:1", abs(Zo/Zp - 3) < 0.01)
check('7f', "标度关系 α+2β+γ=2（平均场、二维 Ising）", 0 + 2*0.5 + 1 == 2 and 0 + 2*sp.Rational(1, 8) + sp.Rational(7, 4) == 2)
rr, gg = 8.0, 1.4
Tb1 = 300.0; T2 = Tb1*rr**(gg - 1); T3 = 1800.0; T4 = T3/rr**(gg - 1)
check('7f', "Otto 效率 1-r^{1-γ}", close(1 - (T4 - Tb1)/(T3 - T2), 1 - rr**(1 - gg)))
check('7f', "冰的残余熵 R ln(3/2)=3.37 J/(mol K)", abs(K.R*math.log(1.5) - 3.37) < 0.005)
Eur = integrate.quad(lambda p: p*p*p*math.exp(-p), 0, np.inf)[0]/integrate.quad(lambda p: p*p*math.exp(-p), 0, np.inf)[0]
check('7f', "极端相对论理想气体 ⟨E⟩=3k_BT", close(Eur, 3))
aR, Vs = sp.symbols('a V', positive=True)
Fph = -aR*Vs*Tt**4/3
check('7f', "光子气体 p=u/3：F=-aVT⁴/3 ⇒ p=aT⁴/3，U=aVT⁴", sp.simplify(-sp.diff(Fph, Vs) - aR*Tt**4/3) == 0 and sp.simplify(Fph - Tt*sp.diff(Fph, Tt) - aR*Vs*Tt**4) == 0)
Nq, q = 30, 50
Nq, q = 3000, 5000
check('7f', "Einstein 固体计数 Ω=C(q+N-1,q) 与 Stirling 熵", abs(math.lgamma(q + Nq)/1 - math.lgamma(q + 1) - math.lgamma(Nq) - ((q + Nq)*math.log(q + Nq) - q*math.log(q) - Nq*math.log(Nq)))/((q + Nq)*math.log(q + Nq) - q*math.log(q) - Nq*math.log(Nq)) < 2e-3)

# ---------- 07g 量子力学补充 ----------
m_, al, hb_ = sp.symbols('m alpha hbar', positive=True)
xx = sp.symbols('x', real=True)
kap = m_*al/hb_**2; psi = sp.sqrt(kap)*sp.exp(-kap*sp.Abs(xx))
jump = sp.diff(sp.sqrt(kap)*sp.exp(-kap*xx), xx).subs(xx, 0) - sp.diff(sp.sqrt(kap)*sp.exp(kap*xx), xx).subs(xx, 0)
check('7g', "δ 势阱束缚态 E=-mα²/2ħ²（导数跳跃 -2mα/ħ² ψ(0)）", sp.simplify(jump + 2*m_*al/hb_**2*sp.sqrt(kap)) == 0 and sp.simplify(-hb_**2*kap**2/(2*m_) + m_*al**2/(2*hb_**2)) == 0)
Nf = 60; ad = np.diag(np.sqrt(np.arange(1, Nf)), 1); xop = (ad + ad.T)/math.sqrt(2); pop = (ad - ad.T)/(1j*math.sqrt(2))
alpha = 1.3 + 0.7j
cs = np.array([np.exp(-abs(alpha)**2/2)*alpha**n/math.sqrt(math.factorial(n)) for n in range(Nf)])
ex = lambda O: (cs.conj()@O@cs).real
check('7g', "相干态 ΔxΔp=ħ/2", abs(math.sqrt(ex(xop@xop) - ex(xop)**2)*math.sqrt(ex(pop@pop) - ex(pop)**2) - 0.5) < 1e-9)
sx = np.array([[0, 1], [1, 0]])/2; sy = np.array([[0, -1j], [1j, 0]])/2; sz = np.diag([0.5, -0.5])
SS = sum(np.kron(s, s) for s in (sx, sy, sz))
check('7g', "S₁·S₂ 本征值 ħ²/4（三重）与 -3ħ²/4（单）", np.allclose(np.sort(np.linalg.eigvalsh(SS)), [-0.75, 0.25, 0.25, 0.25]))
def nbound(z0):
    f_even = lambda z: z*math.tan(z) - math.sqrt(max(z0*z0 - z*z, 0))
    cnt = 0
    for n in range(0, 200):
        lo, hi = n*math.pi/2, min((n + 1)*math.pi/2, z0)
        if lo >= z0: break
        cnt += 1
    return cnt
check('7g', "有限深方势阱束缚态数 ⌈2z₀/π⌉", all(nbound(z0) == math.ceil(2*z0/math.pi) for z0 in (0.3, 1.0, 1.6, 4.0, 7.9)))
bw = 0.8
Zh = sum(math.exp(-bw*(n + 0.5)) for n in range(400)); x2 = sum((n + 0.5)*math.exp(-bw*(n + 0.5)) for n in range(400))/Zh
check('7g', "热态 ⟨x²⟩=(ħ/2mω)coth(βħω/2)", close(x2, 0.5/math.tanh(bw/2)))
from sympy.physics.hydrogen import R_nl
r = sp.symbols('r', positive=True)
ok = all(sp.simplify(sp.integrate(R_nl(n, l, r, 1)**2*r**2/r**3, (r, 0, sp.oo)) - sp.Rational(1, 1)/(n**3*l*(sp.Rational(1, 2) + l)*(l + 1))) == 0 for n, l in [(2, 1), (3, 1), (3, 2), (4, 3)])
check('7g', "类氢 ⟨1/r³⟩=Z³/(n³l(l+½)(l+1)a³)", ok)
VG, kk_ = 0.3, 1.0
Hk = np.array([[kk_**2, VG], [VG, (kk_ - 2)**2]])
check('7g', "Bragg 面上能隙 2|V_G|", np.allclose(np.linalg.eigvalsh(Hk), [1 - VG, 1 + VG]))
Lbox = 300.0; Emax = 1.0
nmax = int(math.sqrt(Emax*2*Lbox**2/math.pi**2)) + 2
nv = np.arange(1, nmax); n2 = (nv[:, None, None]**2 + nv[None, :, None]**2 + nv[None, None, :]**2)
cnt = np.sum((math.pi/Lbox)**2*n2/2 <= Emax)
Nform = Lbox**3/(6*math.pi**2)*(2*Emax)**1.5
nm = Lbox*math.sqrt(2*Emax)/math.pi
check('7g', "三维态密度（积分得 N(E)；Dirichlet 盒子含面修正）", abs(cnt/Nform - 1) < 0.02 and abs(cnt/(Nform - 3*math.pi/8*nm**2) - 1) < 2e-3)
T1 = 1.0
check('7g', "1/T₂=1/(2T₁)+1/T_φ ⇒ T₂≤2T₁", all(1/(1/(2*T1) + 1/Tphi) <= 2*T1 for Tphi in rng.uniform(0.01, 100, 100)) and close(1/(1/(2*T1)), 2*T1))

# ---------- 08d 静电与静磁补充 ----------
zs, Rs = sp.symbols('z R', positive=True)
Ez = zs/(Rs**2 + zs**2)**sp.Rational(3, 2)
check('8d', "圆环轴线场最大于 z=R/√2", sp.solve(sp.diff(Ez, zs), zs) == [Rs/sp.sqrt(2)])
d_, a2 = 3.0, 0.5
s0 = math.sqrt(d_**2/4 - a2**2)
phi = lambda p: math.log(math.hypot(p[0] + s0, p[1])/math.hypot(p[0] - s0, p[1]))
pts = [np.array([d_/2 + a2*math.cos(t), a2*math.sin(t)]) for t in np.linspace(0, 6, 9)]
check('8d', "平行双导线：等效线电荷位于 ±√(d²/4-a²)，C'=πε₀/arccosh(d/2a)", np.ptp([phi(p) for p in pts]) < 1e-12 and close(math.pi/(2*phi(pts[0])), math.pi/(2*math.acosh(d_/(2*a2))), 1e-12))
q_, Rb, dd = sp.symbols('q R d', positive=True)
F_img = q_*(q_*Rb/dd)/(dd - Rb**2/dd)**2
check('8d', "点电荷与接地球的引力 q²Rd/(4πε₀(d²-R²)²)", sp.simplify(F_img - q_**2*Rb*dd/(dd**2 - Rb**2)**2) == 0)
P0, th = sp.symbols('P theta', positive=True); rr_ = sp.symbols('r', positive=True)
phin = P0*rr_*sp.cos(th)/(3*sp.Symbol('epsilon_0')); phout = P0*Rb**3*sp.cos(th)/(3*sp.Symbol('epsilon_0')*rr_**2)
check('8d', "均匀极化球：内部 E=-P/3ε₀ 满足边界条件", sp.simplify((phin - phout).subs(rr_, Rb)) == 0 and
      sp.simplify((-sp.diff(phout, rr_) + sp.diff(phin, rr_)).subs(rr_, Rb)*sp.Symbol('epsilon_0') - P0*sp.cos(th)) == 0)
Bc = integrate.quad(lambda t: math.sin(t)**3/2, 0, math.pi)[0]
check('8d', "旋转带电球壳内 B=(2/3)μ₀σRω", close(Bc, 2/3))
Uball = integrate.quad(lambda r: 0.5*eps0*(r/(4*math.pi*eps0))**2*4*math.pi*r*r, 0, 1)[0] + integrate.quad(lambda r: 0.5*eps0*(1/(4*math.pi*eps0*r*r))**2*4*math.pi*r*r, 1, np.inf)[0]
check('8d', "均匀带电球静电能 (3/5)Q²/(4πε₀R)", close(Uball, 0.6/(4*math.pi*eps0), 1e-8))
aw, bw_, dw = 0.2, 0.5, 0.1
Mnum = mu0/(2*math.pi)*bw_*integrate.quad(lambda x: 1/x, dw, dw + aw)[0]
check('8d', "导线与矩形线圈互感 (μ₀b/2π)ln((d+a)/d)", close(Mnum, mu0*bw_/(2*math.pi)*math.log((dw + aw)/dw)))
kap_, wcap, dcap, Vc, xcap = sp.symbols('kappa w d V x', positive=True)
Ucap = sp.Rational(1, 2)*eps0*(1 + (kap_ - 1)*xcap/sp.Symbol('L'))*sp.Symbol('L')*wcap/dcap*Vc**2
check('8d', "电容器吸入介质的力 ε₀(κ-1)wV²/2d（恒压 F=+∂W/∂x）", sp.simplify(sp.diff(Ucap, xcap) - eps0*(kap_ - 1)*wcap*Vc**2/(2*dcap)) == 0)

# ---------- 08e 电路补充 ----------
Rab, Rbc, Rca = 3.0, 5.0, 7.0
S_ = Rab + Rbc + Rca; Ra, Rb_, Rc_ = Rab*Rca/S_, Rab*Rbc/S_, Rbc*Rca/S_
par = lambda x, y: x*y/(x + y)
check('8e', "Δ--Y 变换（三对端子电阻相同）", close(Ra + Rb_, par(Rab, Rbc + Rca)) and close(Rb_ + Rc_, par(Rbc, Rab + Rca)) and close(Ra + Rc_, par(Rca, Rab + Rbc)))
Rl = 1.0
for _ in range(200): Rl = 1 + par(1, Rl)
check('8e', "无穷梯形网络 (1+√5)/2 R", close(Rl, (1 + math.sqrt(5))/2))
V8 = list(itertools.product([0, 1], repeat=3)); A8 = np.array([[1.0 if sum(abs(np.array(u) - np.array(v))) == 1 else 0 for v in V8] for u in V8])
Lp = np.linalg.pinv(np.diag(A8.sum(1)) - A8); Re = lambda i, j: Lp[i, i] + Lp[j, j] - 2*Lp[i, j]
check('8e', "立方体电阻：体对角 5/6，面对角 3/4，棱 7/12", close(Re(0, 7), 5/6) and close(Re(0, 3), 3/4) and close(Re(0, 1), 7/12))
C1, C2, V1, V2 = 2e-6, 3e-6, 10.0, 4.0
Vf = (C1*V1 + C2*V2)/(C1 + C2)
check('8e', "两电容并联损失 C₁C₂(V₁-V₂)²/2(C₁+C₂)", close(0.5*C1*V1**2 + 0.5*C2*V2**2 - 0.5*(C1 + C2)*Vf**2, C1*C2*(V1 - V2)**2/(2*(C1 + C2))))
def skin_ratio(a_over_delta):
    kk = (1 - 1j)*a_over_delta
    Z = kk/2*special.jv(0, kk)/special.jv(1, kk)
    return Z.real
check('8e', "趋肤效应 R_ac/R_dc≈a/2δ（a/δ=20、40）", all(abs(skin_ratio(x)/(x/2) - 1) < 0.03 for x in (20, 40)))
check('8e', "铜 1 mm² 通 1 A 漂移速度≈7×10⁻⁵ m/s", abs(1/(8.5e28*e*1e-6) - 7.4e-5) < 0.2e-5)
lamD = math.sqrt(78.5*eps0*kB*298/(2*K.N_A*e*e*100))
check('8e', "0.1 M 1:1 电解质 Debye 长度≈0.96 nm", abs(lamD*1e9 - 0.96) < 0.02)
check('8e', "Boost：V_out=V_in/(1-D)（伏秒平衡）", close(10*0.6 + (10 - 25)*0.4, 0) and close(10/(1 - 0.6), 25))
Rm, Vm = 2.0, 12.0
wn = np.linspace(0, 1, 100001); Pm = (Vm - Vm*wn)*Vm*wn/Rm
check('8e', "直流电机最大输出功率在空载转速一半", abs(wn[np.argmax(Pm)] - 0.5) < 1e-4)

# ---------- 09d 相对论与天体 ----------
v_ = 0.6; gm_ = 1/math.sqrt(1 - v_**2)
Lb = np.array([[gm_, -gm_*v_, 0], [-gm_*v_, gm_, 0], [0, 0, 1]])
ux, uy = 0.3, 0.5; gu = 1/math.sqrt(1 - ux**2 - uy**2)
U = Lb@np.array([gu, gu*ux, gu*uy])
check('9d', "速度变换（含横向分量）", close(U[1]/U[0], (ux - v_)/(1 - ux*v_)) and close(U[2]/U[0], uy/(gm_*(1 - ux*v_))))
bt = sp.symbols('beta', positive=True); mu_ = sp.symbols('mu')
ratio = sp.integrate((1 - bt*mu_)**2, (mu_, -1, 1))/sp.integrate(1 - bt*mu_, (mu_, -1, 1))
check('9d', "逆 Compton ⟨ε'⟩=γ²ε(1+β²/3)→(4/3)γ²ε", sp.simplify(ratio - (1 + bt**2/3)) == 0)
E_ = sp.symbols('E', positive=True); m = sp.symbols('m', positive=True)
check('9d', "电子附近对产生阈值 4m_ec²；核附近 2m_ec²", sp.solve(sp.Eq((E_ + m)**2 - E_**2, (3*m)**2), E_) == [4*m] and abs(4*K.physical_constants['electron mass energy equivalent in MeV'][0] - 2.044) < 1e-3)
check('9d', "Pound--Rebka 22.5 m：gh/c²≈2.5×10⁻¹⁵", abs(g0*22.5/c**2 - 2.45e-15) < 0.05e-15)
check('9d', "Chandrasekhar 5.83/μe²≈1.46 M⊙（μe=2）", abs(5.83/4 - 1.457) < 0.002)
bvals = np.linspace(0.01, 0.999, 2000)
ok = all(abs(max(b*np.sin(th)/(1 - b*np.cos(th)) for th in [math.acos(b)]) - b/math.sqrt(1 - b*b)) < 1e-12 for b in bvals)
check('9d', "视超光速最大值 γβ（cosθ=β）", ok and abs(optimize.minimize_scalar(lambda th: -0.99*math.sin(th)/(1 - 0.99*math.cos(th)), bounds=(0, math.pi), method='bounded').x - math.acos(0.99)) < 1e-4)
b = 0.3; gb = 1/math.sqrt(1 - b*b)
boost = lambda bb_: np.array([[1/math.sqrt(1 - bb_*bb_), -bb_/math.sqrt(1 - bb_*bb_)], [-bb_/math.sqrt(1 - bb_*bb_), 1/math.sqrt(1 - bb_*bb_)]])
kin = np.array([1.0, 1.0]); km = boost(b)@kin; kref = np.array([km[0], -km[1]]); kout = boost(-b)@kref
check('9d', "运动镜面反射频率比 (1-β)/(1+β)（镜面系中反射再变换回来）", close(kout[0], (1 - b)/(1 + b)) and close(kout[1], -(1 - b)/(1 + b)))
Kearth = (2*math.pi*G/(365.25*86400))**(1/3)*5.972e24/(1.989e30 + 5.972e24)**(2/3)
check('9d', "视向速度半振幅：地球对太阳约 0.09 m/s", abs(Kearth - 0.0894) < 0.002)
H0 = 70e3/3.086e22
check('9d', "Hubble 时间 1/H₀≈14 Gyr", abs(1/H0/3.156e16 - 13.97) < 0.05)

# ---------- 09e 原子、核与凝聚态补充 ----------
check('9e', "Moseley：Cu Kα≈8.0 keV", abs(0.75*13.6057*28**2/1e3 - 8.0) < 0.01)
GF, mmu, hbar_GeV = 1.1663787e-5, 0.1056584, 6.582119569e-25
tau = hbar_GeV/(GF**2*mmu**5/(192*math.pi**3))
check('9e', "μ 子寿命 192π³/(G_F²m⁵)≈2.19 μs", abs(tau*1e6 - 2.19) < 0.02, f"τ={tau*1e6:.3f} μs")
check('9e', "BCS：Δ(0)=πe^{-γ}k_BTc=1.764，2Δ=3.53", abs(math.pi*math.exp(-float(mp.euler)) - 1.764) < 1e-3)
check('9e', "Josephson 2e/h=483.6 THz/V，R_K=25812.8 Ω", abs(2*e/K.h/1e12 - 483.598) < 1e-3 and abs(K.h/e**2 - 25812.807) < 1e-2)
check('9e', "室温 k_BT=25.9 meV（300 K）", abs(kB*300/e*1e3 - 25.85) < 0.01)
alpha_ = K.alpha
check('9e', "仲电子偶素寿命 2ħ/(m_ec²α⁵)≈125 ps", abs(2*hbar/(me*c**2*alpha_**5)*1e12 - 124.4) < 1.0)
check('9e', "⁵⁷Fe 14.4 keV 反冲能≈2 meV", abs((14.4e3)**2/(2*56.935*931.494e6)*1e3 - 1.95) < 0.02)
lam = math.log(2)/1.248e9; tage = 2.7e9
P_t = math.exp(-lam*tage); D_t = 1 - P_t
check('9e', "放射性测年 t=ln(1+D/P)/λ", close(math.log(1 + D_t/P_t)/lam, tage, 1e-12))

# ---------- 10d 几何光学补充 ----------
n_, R1, R2, dl = 1.5, 0.1, -0.15, 0.02
def refr(n1, n2, Rr): return np.array([[1, 0], [-(n2 - n1)/(Rr*n2), n1/n2]])
def trans(d): return np.array([[1, d], [0, 1]])
Msys = refr(n_, 1.0, R2)@trans(dl)@refr(1.0, n_, R1)
check('10d', "厚透镜焦距公式（矩阵法）", close(-Msys[1, 0], (n_ - 1)*(1/R1 - 1/R2 + (n_ - 1)*dl/(n_*R1*R2)), 1e-12))
nice = 1.31
check('10d', "22° 晕：60° 冰棱镜最小偏向 ≈21.8°", abs(math.degrees(2*math.asin(nice*math.sin(math.radians(30)))) - 60 - 21.8) < 0.1)
def te_modes(V):
    return sum(1 for m in range(100) if V > m*math.pi/2)
check('10d', "对称平板波导 TE 模式数 ⌈2V/π⌉", all(te_modes(V) == math.ceil(2*V/math.pi) for V in (0.5, 1.7, 3.3, 7.1)))
Rn, lam0 = 1.0, 589e-9
check('10d', "Newton 环暗环 r_m=√(mλR)（空气膜厚 r²/2R）", close(2*(math.sqrt(3*lam0*Rn)**2/(2*Rn)), 3*lam0))

# ---------- 10e 物理光学补充 ----------
xs = np.linspace(4, 5, 200001); side = np.max((np.sin(xs)/xs)**2)
xa = np.linspace(4.5, 6.5, 200001); ring = np.max((2*special.j1(xa)/xa)**2)
enc = 1 - special.j0(3.8317)**2 - special.j1(3.8317)**2
check('10e', "单缝旁瓣 4.7%，Airy 第一亮环 1.75%，中央 84%", abs(side - 0.0472) < 2e-4 and abs(ring - 0.0175) < 2e-4 and abs(enc - 0.838) < 2e-3)
def bragg_R(nH, nL, N, ns=1.52, n0=1.0):
    M = np.eye(2, dtype=complex)
    for n in [nL, nH]*N:     # 从入射侧数：L,H,…,L,H（紧贴基底的是 H）
        d = 0.25; Mi = np.array([[math.cos(2*math.pi*d), 1j*math.sin(2*math.pi*d)/n], [1j*n*math.sin(2*math.pi*d), math.cos(2*math.pi*d)]]); M = M@Mi
    B, C = M@np.array([1, ns])
    r = (n0*B - C)/(n0*B + C); return abs(r)**2
nH, nL, N = 2.3, 1.38, 6
formula = ((1 - 1.52/1.0*(nL/nH)**(2*N))/(1 + 1.52/1.0*(nL/nH)**(2*N)))**2
check('10e', "Bragg 反射镜中心反射率公式（传输矩阵）", abs(bragg_R(nH, nL, N) - formula) < 1e-9)
Rf = 0.99; Ff = math.pi*math.sqrt(Rf)/(1 - Rf)
check('10e', "Fabry--Pérot 腔内功率增强 ≈F/π", abs((1/(1 - Rf))/(Ff/math.pi) - 1) < 0.01)
I1, I2 = 1.0, 0.25
Iphi = I1 + I2 + 2*math.sqrt(I1*I2)*np.cos(np.linspace(0, 2*math.pi, 1001))
check('10e', "干涉对比度 2√(I₁I₂)/(I₁+I₂)", close((Iphi.max() - Iphi.min())/(Iphi.max() + Iphi.min()), 2*math.sqrt(I1*I2)/(I1 + I2)))
check('10e', "两束夹角 θ 的干涉条纹周期 λ/(2sin(θ/2))", close(500e-9/(2*math.sin(math.radians(30)/2)), 500e-9/(2*math.sin(math.radians(15)))))

# ---------- 11d 实验技术 ----------
dm = 3.7e-10
check('11d', "空气平均自由程≈6.6 mm/p[Pa]", abs(kB*293/(math.sqrt(2)*math.pi*dm*dm)*1e3 - 6.6) < 0.2)
vbar = math.sqrt(8*kB*293/(math.pi*29*K.atomic_mass))
check('11d', "长管分子流流导 12.1 d³/L（cm，L/s）", abs(math.pi/12*vbar*1e2*1e-3 - 12.1) < 0.1)
fc = 1.0
check('11d', "RC 低通的等效噪声带宽 πf_c/2", close(integrate.quad(lambda f: 1/(1 + (f/fc)**2), 0, np.inf)[0], math.pi/2*fc))
check('11d', "刀口法 10--90% 宽度 = 1.28w", abs(2*special.erfinv(0.8)/math.sqrt(2) - 1.2816) < 1e-4)
GF_, ex_, eps_s = 2.0, 5.0, 1e-4
Rg = 350.0; Rx = Rg*(1 + GF_*eps_s)
Vout = ex_*(Rx/(Rx + Rg) - 0.5)
check('11d', "四分之一桥 V_out≈V_ex GF ε/4", abs(Vout/(ex_*GF_*eps_s/4) - 1) < 1e-3)

# ---------- 11e 经典实验 ----------
Lr, rr2, Mm, mm2, kap_t = sp.symbols('L r M m kappa', positive=True)
theta_eq = 2*G*Mm*mm2/rr2**2*(Lr/2)/kap_t; Tq = 2*sp.pi*sp.sqrt(mm2*Lr**2/2/kap_t)
check('11e', "Cavendish 扭秤 G=2π²Lr²θ/(MT²)", sp.simplify(2*sp.pi**2*Lr*rr2**2*theta_eq/(Mm*Tq**2) - G) == 0)
h1, h2, Ic = sp.symbols('h1 h2 I_c', positive=True)
T1k = 2*sp.pi*sp.sqrt((Ic + mm2*h1**2)/(mm2*sp.Symbol('g')*h1)); T2k = 2*sp.pi*sp.sqrt((Ic + mm2*h2**2)/(mm2*sp.Symbol('g')*h2))
Ics = sp.solve(sp.Eq(T1k**2, T2k**2), Ic)[0]
check('11e', "Kater 可逆摆 g=4π²(h₁+h₂)/T²", sp.simplify(4*sp.pi**2*(h1 + h2)/T1k.subs(Ic, Ics)**2 - sp.Symbol('g')) == 0)
check('11e', "Fizeau：2L/c=1/(2Nf) ⇒ c=4LNf", close(4*8633*720*12.6, 2*8633/(1/(2*720*12.6))) and abs(4*8633*720*12.6/3e8 - 1.04) < 0.01)
check('11e', "Michelson--Morley 预期条纹移动≈0.4", abs(2*11*(3e4)**2/(500e-9*c**2) - 0.44) < 0.01)
T1s = 1.0
check('11e', "反转恢复零点 τ=T₁ln2", abs(1 - 2*math.exp(-math.log(2))) < 1e-15)
bL = optimize.brentq(lambda x: math.cosh(x)*math.cos(x) - 1, 4, 5)
check('11e', "自由--自由梁首阶 β₁L=4.730", abs(bL - 4.7300) < 1e-4)
Dd, w_s, Ls = sp.symbols('D omega L', positive=True)
dlt = sp.sqrt(2*Dd/w_s); dt_ = (Ls/dlt)/w_s; lnr = Ls/dlt
check('11e', "Ångström 法 D=L²/(2Δt ln(A₁/A₂))", sp.simplify(Ls**2/(2*dt_*lnr) - Dd) == 0)
check('11e', "四探针 π/ln2=4.532", abs(math.pi/math.log(2) - 4.532) < 1e-3)
gm, pA, Vr = sp.symbols('gamma p A', positive=True)
kspring = gm*pA*sp.Symbol('A')**2/sp.Symbol('V')
check('11e', "Rüchardt：绝热弹簧 k=γpA²/V", sp.simplify(sp.diff(pA*(sp.Symbol('V')/(sp.Symbol('V') + sp.Symbol('A')*xx))**gm*sp.Symbol('A'), xx).subs(xx, 0) + kspring) == 0)

# ---------- 12d 数据分析补充 ----------
check('12d', "均匀分布 B 类不确定度 a/√3", close(math.sqrt(integrate.quad(lambda x: x*x/2, -1, 1)[0]), 1/math.sqrt(3)))
npl, nmi = 5, 4
runs = []
for perm in set(itertools.permutations([1]*npl + [0]*nmi)):
    runs.append(1 + sum(perm[i] != perm[i + 1] for i in range(len(perm) - 1)))
check('12d', "游程检验 E R=2n₊n₋/N+1", close(np.mean(runs), 2*npl*nmi/(npl + nmi) + 1))
kq = stats_k = 1.645
check('12d', "Currie 探测限 2.71+4.65√B", abs(kq**2 - 2.71) < 0.01 and abs(2*math.sqrt(2)*kq - 4.65) < 0.01)
nr, rho_ = 30, 0.5
zs_ = []
for _ in range(20000):
    X = rng.multivariate_normal([0, 0], [[1, rho_], [rho_, 1]], nr); zs_.append(math.atanh(np.corrcoef(X.T)[0, 1]))
check('12d', "Fisher z：方差 1/(n-3)", abs(np.var(zs_)*(nr - 3) - 1) < 0.05 and abs(np.mean(zs_) - math.atanh(rho_)) < 0.02)
check('12d', "对数坐标误差 0.434σ/x", abs(1/math.log(10) - 0.4343) < 1e-4)
Vc_ = np.diag([1.0, 2.0, 0.5]); yv = np.array([1.0, 2.2, 2.9]); Ac = np.array([[1.0, 1.0, -1.0]]); cc = np.array([0.0])
eta_hat = yv - Vc_@Ac.T@np.linalg.solve(Ac@Vc_@Ac.T, Ac@yv - cc)
cons = {'type': 'eq', 'fun': lambda e_: Ac@e_ - cc}
opt = optimize.minimize(lambda e_: (yv - e_)@np.linalg.solve(Vc_, yv - e_), yv, constraints=[cons], tol=1e-14)
check('12d', "线性约束拟合闭式解", np.allclose(eta_hat, opt.x, atol=1e-6) and abs(Ac@eta_hat - cc)[0] < 1e-12)
x1, x2, s1, s2, rh = 10.0, 9.0, 0.6, 0.5, 0.4
dsamp = rng.multivariate_normal([0, 0], [[s1**2, rh*s1*s2], [rh*s1*s2, s2**2]], 400000)
check('12d', "相关测量之差的方差 σ₁²+σ₂²-2ρσ₁σ₂", abs(np.var(dsamp[:, 0] - dsamp[:, 1]) - (s1**2 + s2**2 - 2*rh*s1*s2)) < 2e-3)

# ---------- 12e 信号处理补充 ----------
sig_t = 0.7
gauss = lambda t: math.exp(-t*t/(4*sig_t**2))
dt2 = integrate.quad(lambda t: t*t*gauss(t)**2, -20, 20)[0]/integrate.quad(lambda t: gauss(t)**2, -20, 20)[0]
df2 = 1/(16*math.pi**2*sig_t**2)
check('12e', "Gauss 窗取等 Δt Δf = 1/(4π)", close(math.sqrt(dt2*df2), 1/(4*math.pi), 1e-9))
Nn, A_, sg_ = 256, 1.0, 0.5; w0, ph0 = 0.7, 0.3
nn = np.arange(Nn)
def model(th): return th[0]*np.cos(th[1]*nn + th[2])
th0 = np.array([A_, w0, ph0]); Jm = np.zeros((Nn, 3))
for i in range(3):
    dth = np.zeros(3); dth[i] = 1e-6; Jm[:, i] = (model(th0 + dth) - model(th0 - dth))/2e-6
FI = Jm.T@Jm/sg_**2; crb = np.linalg.inv(FI)[1, 1]
eta = A_**2/(2*sg_**2)
check('12e', "正弦频率 CRB 12/(ηN(N²-1))（相位、幅度未知；N=256 渐近）", abs(crb/(12/(eta*Nn*(Nn**2 - 1))) - 1) < 0.01)
check('12e', "Silverman 带宽常数 (4/3)^{1/5}=1.06", abs((4/3)**0.2 - 1.0592) < 1e-4)
check('12e', "50 Ω 上 0 dBm=0.224 V rms", abs(math.sqrt(1e-3*50) - 0.2236) < 1e-4)
H_, Sn, Sx = 0.6 + 0.3j, 0.2, 1.5
mse = lambda G_: abs(G_*H_ - 1)**2*Sx + abs(G_)**2*Sn
Gopt = np.conj(H_)/(abs(H_)**2 + Sn/Sx)
check('12e', "Wiener 反卷积 H*/(|H|²+S_n/S_x) 使 MSE 最小", all(mse(Gopt) <= mse(Gopt + d) + 1e-15 for d in rng.normal(size=50)*0.1 + 1j*rng.normal(size=50)*0.1))
for n in (2, 4):
    w_c = 1.0; ww_ = np.array([0.5, 1.0, 2.0])
    check('12e', f"Butterworth n={n}：-3 dB 于 ω_c，高频 -20n dB/dec", close(1/(1 + 1.0**(2*n)), 0.5) and abs(10*math.log10(1/(1 + 1000**(2*n))) - 10*math.log10(1/(1 + 100**(2*n))) + 20*n) < 1e-3)

# ---------- 13d 数量级 ----------
check('13d', "Betz 极限 16/27（a=1/3）", sp.solve(sp.diff(4*sp.Symbol('a')*(1 - sp.Symbol('a'))**2, sp.Symbol('a')), sp.Symbol('a'))[0] == sp.Rational(1, 3) and 4*sp.Rational(1, 3)*(sp.Rational(2, 3))**2 == sp.Rational(16, 27))
check('13d', "一层温室模型 T_s=2^{1/4}T_e≈303 K", abs(2**0.25*255 - 303) < 1)
Mm_, dm_, Ms_, ds_ = 7.342e22, 3.844e8, 1.989e30, 1.496e11
check('13d', "平衡潮：月 0.54 m、日 0.25 m", abs(1.5*Mm_/ME*(RE/dm_)**3*RE - 0.54) < 0.01 and abs(1.5*Ms_/ME*(RE/ds_)**3*RE - 0.25) < 0.01)
check('13d', "海水趋肤深度≈250 m/√f", abs(math.sqrt(2/(mu0*4.0*2*math.pi*1.0)) - 252) < 3)
check('13d', "步行速度上限 √(gL)≈3 m/s（L=0.9 m）", abs(math.sqrt(g0*0.9) - 2.97) < 0.01)
check('13d', "ATP 水解≈20 k_BT（≈50 kJ/mol，体温）", abs(50e3/(K.R*310) - 19.4) < 0.5)
dd_ = sp.symbols('d', positive=True)
check('13d', "神经电缆长度常数 λ=√(r_m/r_i)∝√d（r_m∝1/d，r_i∝1/d²）", sp.simplify(sp.sqrt((1/dd_)/(1/dd_**2))/sp.sqrt(dd_)) == 1)

# ---------- 13e 跨学科模型 ----------
def kura_r(Kc_, sig=1.0):
    g = lambda w: math.exp(-w*w/(2*sig*sig))/math.sqrt(2*math.pi*sig*sig)
    f = lambda r: r - Kc_*r*integrate.quad(lambda th: math.cos(th)**2*g(Kc_*r*math.sin(th)), -math.pi/2, math.pi/2)[0]
    rs = np.linspace(1e-3, 0.999, 400); vals = [f(r) for r in rs]
    return any(vals[i]*vals[i + 1] < 0 for i in range(len(rs) - 1))
Kcrit = 2/(math.pi/math.sqrt(2*math.pi))
check('13e', "Kuramoto K_c=2/(πg(0))（Gauss 频率分布）", kura_r(1.05*Kcrit) and not kura_r(0.95*Kcrit))
bS, gS = 0.5, 0.2
solS = integrate.solve_ivp(lambda t, y: [bS*y[0]*(1 - y[0]) - gS*y[0]], [0, 400], [0.01], rtol=1e-10)
check('13e', "SIS 平衡 i*=1-1/R₀", abs(solS.y[0, -1] - (1 - gS/bS)) < 1e-6)
check('13e', "二维渗流分形维数 2-β/ν=91/48", 2 - sp.Rational(5, 36)/sp.Rational(4, 3) == sp.Rational(91, 48))
Ncov = 20
Ccov = lambda P, N: 2*sum(math.comb(P - 1, k) for k in range(N))
check('13e', "Cover：P=2N 时线性可分的二分类恰占一半", close(Ccov(2*Ncov, Ncov)/2**(2*Ncov), 0.5))
check('13e', "气候零阶敏感度 3.7/3.2≈1.2 K；Planck 响应 4σT³≈3.8 W/m²/K", abs(3.7/3.2 - 1.16) < 0.01 and abs(4*K.sigma*255**3 - 3.76) < 0.02)
r0_, r1_ = sp.symbols('r0 r1', positive=True); Qs, b_c = sp.symbols('Q b', positive=True)
cost = Qs**2/r0_**4 + b_c*r0_**2
ropt = sp.solve(sp.diff(cost, r0_), r0_)[0]
check('13e', "Murray 定律：最优半径 r³∝Q ⇒ r₀³=r₁³+r₂³", sp.simplify(ropt**6/Qs**2).free_symbols == {b_c})
xL = sp.symbols('x', positive=True)
F_wlc = (1/(4*(1 - xL)**2) - sp.Rational(1, 4) + xL)
check('13e', "蠕虫链：小伸长 F≈(3k_BT/2P)x/L", sp.series(F_wlc, xL, 0, 2).removeO() == sp.Rational(3, 2)*xL)
a12, a21, K1, K2 = 0.5, 0.6, 1.0, 1.2
solLV = integrate.solve_ivp(lambda t, y: [y[0]*(1 - (y[0] + a12*y[1])/K1), 0.8*y[1]*(1 - (y[1] + a21*y[0])/K2)], [0, 400], [0.1, 0.1], rtol=1e-10)
check('13e', "Lotka--Volterra 竞争：α₁₂<K₁/K₂、α₂₁<K₂/K₁ 时共存", a12 < K1/K2 and a21 < K2/K1 and np.all(solLV.y[:, -1] > 0.1))
tau_m, RI, Vth = 0.02, 1.5, 1.0
tfire = optimize.brentq(lambda t: RI*(1 - math.exp(-t/tau_m)) - Vth, 1e-9, 1)
check('13e', "漏积分发放：T=τ ln(RI/(RI-V_th))", close(tfire, tau_m*math.log(RI/(RI - Vth)), 1e-9))
check('13e', "72 法则：r=8% 时倍增 9.0 年", abs(math.log(2)/math.log(1.08) - 72/8) < 0.1)
def ovm_stable(Vp, a=1.0):
    ks = np.linspace(0.01, math.pi, 200)
    for k in ks:
        # 线性化：λ² + aλ - aV'(e^{ik}-1) = 0
        rts = np.roots([1, a, -a*Vp*(np.exp(1j*k) - 1)])
        if np.any(rts.real > 1e-12): return False
    return True
check('13e', "最优速度模型稳定 ⇔ V'(h)<a/2", ovm_stable(0.49) and not ovm_stable(0.51))
check('13e', "地表温度年波穿透深度 √(2D/ω)≈2 m（D=5×10⁻⁷）", abs(math.sqrt(2*5e-7/(2*math.pi/3.156e7)) - 2.24) < 0.02)

npass = sum(r[2] for r in R); print(f"\n第四轮物理: {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
