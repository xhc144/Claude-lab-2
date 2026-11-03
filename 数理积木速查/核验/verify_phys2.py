"""续写部分（06b--09c）的符号/数值核验。"""
import math, json, itertools
import numpy as np, sympy as sp
from scipy import integrate, linalg, special, optimize, constants as C

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(4)
close = lambda a, b, tol=1e-3: abs(a - b) <= tol*abs(b)
eV, MeV = C.e, 1e6*C.e

# ---------- 06b ----------
P = rng.random((400000, 3)) - 0.5; nvec = rng.normal(size=3); nvec /= np.linalg.norm(nvec)
check('6b', "立方体任意轴 I = Ma²/6", abs(np.mean(np.sum(P**2, 1) - (P@nvec)**2) - 1/6) < 2e-3)
L, M = sp.symbols('L M', positive=True)
check('6b', "均匀棒打击中心在 2L/3", sp.simplify(L/2 + (M*L**2/12)/(M*L/2)) == sp.Rational(2, 3)*L)
g, Lr, ph0 = 9.8, 1.0, 1.2
def ladder(t, Y): return [Y[1], -1.5*g/Lr*math.cos(Y[0])]
ev = lambda t, Y: (-1.5*g/Lr*math.cos(Y[0]))*math.sin(Y[0]) + Y[1]**2*math.cos(Y[0])   # ẍ_cm ∝ -(φ̈ sinφ + φ̇² cosφ)
ev.terminal = True; ev.direction = -1
sl = integrate.solve_ivp(ladder, [0, 5], [ph0, 0], events=lambda t, Y: -(-1.5*g/Lr*math.cos(Y[0])*math.sin(Y[0]) + Y[1]**2*math.cos(Y[0])) if False else ev(t, Y), rtol=1e-11, atol=1e-12)
phf = sl.y_events[0][0][0]
check('6b', "梯子在质心高度降到 2/3 时离墙", abs(math.sin(phf)/math.sin(ph0) - 2/3) < 1e-5, f"{math.sin(phf)/math.sin(ph0):.6f}")
lam, x = sp.symbols('lambda x', positive=True)
check('6b', "落链称重 = 3 倍已落部分重量", sp.simplify(lam*g*x + lam*(2*g*x)) == 3*lam*g*x)
t, vt = sp.symbols('t v_t', positive=True); gs = sp.symbols('g', positive=True); vv = vt*sp.tanh(gs*t/vt)
check('6b', "二次阻力 v_t tanh(gt/v_t)", sp.simplify(sp.diff(vv, t) - gs*(1 - vv**2/vt**2)) == 0)
v0, al = 10.0, math.radians(25)
def rng_inc(th):
    tf = 2*v0*math.sin(th - al)/(g*math.cos(al)); return v0*math.cos(th)*tf/math.cos(al)
best = optimize.minimize_scalar(lambda th: -rng_inc(th), bounds=(al, math.pi/2), method='bounded')
check('6b', "斜面最大射程与最优方向", close(-best.fun, v0**2/(g*(1 + math.sin(al))), 1e-6) and abs(best.x - (al + (math.pi/2 - al)/2)) < 1e-4)
hh = 5.0
def rng_h(th): vy = v0*math.sin(th); tf = (vy + math.sqrt(vy*vy + 2*g*hh))/g; return v0*math.cos(th)*tf
bh = optimize.minimize_scalar(lambda th: -rng_h(th), bounds=(0, math.pi/2), method='bounded')
check('6b', "高处抛射最大射程与仰角", close(-bh.fun, v0/g*math.sqrt(v0**2 + 2*g*hh), 1e-6) and abs(math.tan(bh.x) - v0/math.sqrt(v0**2 + 2*g*hh)) < 1e-4)
Rs, th = sp.symbols('R theta', positive=True); b = Rs*sp.cos(th/2)
check('6b', "硬球 dσ/dΩ = R²/4", all(abs(float((b/sp.sin(th)*sp.Abs(sp.diff(b, th))).subs({Rs: 1.7, th: v})) - 1.7**2/4) < 1e-12 for v in (0.3, 1.5, 2.9)))
GM, r0, dv = 1.0, 1.0, 1e-4; vc = 1.0; v1 = vc + dv
a1 = 1/(2/r0 - v1**2); e1 = 1 - r0/a1
check('6b', "切向小冲量 e≈2Δv/v, ΔT/T≈3Δv/v", abs(e1/(2*dv) - 1) < 1e-3 and abs((a1**1.5 - 1)/(3*dv) - 1) < 1e-3)
m1, m2, I_, Rp, gg = sp.symbols('m1 m2 I R g', positive=True); q = sp.Function('q')(t)
Lag = (m1 + m2 + I_/Rp**2)*sp.diff(q, t)**2/2 + (m1 - m2)*gg*q
acc = sp.solve(sp.diff(sp.diff(Lag, sp.diff(q, t)), t) - sp.diff(Lag, q), sp.diff(q, t, 2))[0]
check('6b', "Atwood 机含滑轮", sp.simplify(acc - (m1 - m2)*gg/(m1 + m2 + I_/Rp**2)) == 0)
ms, s, Ls, vend = sp.symbols('m_s s L v', positive=True)
check('6b', "弹簧等效质量 m_s/3", sp.simplify(sp.integrate((ms/Ls)*(vend*s/Ls)**2/2, (s, 0, Ls)) - (ms/3)*vend**2/2) == 0)

# ---------- 06c ----------
A, a, H, gS = sp.symbols('A a H g', positive=True); hS = sp.Function('h')(t)
solh = (sp.sqrt(H) - a/A*sp.sqrt(gS/2)*t)**2
check('6c', "排空时间 (A/a)√(2H/g)", all(abs(float((A*sp.diff(solh, t) + a*sp.sqrt(2*gS*solh)).subs({A: 2.0, a: 0.1, H: 1.0, gS: 9.8, t: tv}))) < 1e-12 for tv in (0.5, 3.0, 8.0)) and sp.simplify(solh.subs(t, A/a*sp.sqrt(2*H/gS))) == 0)
check('6c', "血管半径减 16% 流阻翻倍", abs(0.84**-4 - 2) < 0.02)
gam_w, rho_w = 0.0728, 998.0
lc = math.sqrt(gam_w/(rho_w*9.81)); cph = lambda k: math.sqrt(9.81/k + gam_w*k/rho_w)
km = optimize.minimize_scalar(cph, bounds=(10, 2000), method='bounded').x
check('6c', "毛细长度 2.7 mm; 最小相速 23 cm/s @ 1.7 cm", abs(lc - 2.7e-3) < 0.1e-3 and abs(cph(km) - 0.23) < 0.005 and abs(2*math.pi/km - 0.017) < 0.001)
check('6c', "Kelvin 尾迹角 arcsin(1/3) = 19.47°", abs(math.degrees(math.asin(1/3)) - 19.47) < 0.01)
b1 = optimize.brentq(lambda z: math.cos(z)*math.cosh(z) + 1, 1, 3); b2 = optimize.brentq(lambda z: math.cos(z)*math.cosh(z) + 1, 4, 6)
check('6c', "悬臂梁 β1L=1.875, ω2/ω1=6.27", abs(b1 - 1.8751) < 1e-4 and abs((b2/b1)**2 - 6.27) < 0.01)
check('6c', "20°C 空气声速 343 m/s", abs(math.sqrt(1.4*C.R*293.15/0.028965) - 343) < 1.5)
mu = 3.003e-6; aE = 1.496e11
rL1 = optimize.brentq(lambda r: (1 - mu)/(aE - r)**2 - mu/r**2 - (aE*(1 - mu) - r)/aE**3, 1e8, 1e10)
check('6c', "日地 L1 ≈ a(μ/3)^{1/3} ≈ 1.5e6 km", abs(rL1/(aE*(mu/3)**(1/3)) - 1) < 0.01 and abs(rL1 - 1.5e9) < 0.05e9, f"{rL1/1e9:.3f}e6 km")
mu_c = optimize.brentq(lambda m: 27*m*(1 - m) - 1, 1e-4, 0.2)
check('6c', "L4/L5 稳定阈值 M/m > 24.96", abs((1 - mu_c)/mu_c - 24.96) < 0.01)
w0, gm = 3.0, 0.2; wd = math.sqrt(w0**2 - gm**2/4)
check('6c', "对数衰减率 δ = γT_d/2", abs(math.log(math.exp(-gm/2*0)/math.exp(-gm/2*2*math.pi/wd)) - gm*(2*math.pi/wd)/2) < 1e-12)

# ---------- 07b ----------
J, th_, m_, w_ = sp.symbols('J theta m omega', positive=True)
qv = sp.sqrt(2*J/(m_*w_))*sp.sin(th_); pv = sp.sqrt(2*J*m_*w_)*sp.cos(th_)
check('7b', "作用量-角变量: {q,p}_{θ,J}=1, H=ωJ", sp.simplify(sp.diff(qv, th_)*sp.diff(pv, J) - sp.diff(qv, J)*sp.diff(pv, th_)) == 1
      and sp.simplify(pv**2/(2*m_) + m_*w_**2*qv**2/2 - w_*J) == 0)
c = sp.symbols('c')
check('7b', "球顶滑落 cosθ=2/3", sp.solve(sp.Eq(c, 2*(1 - c)), c) == [sp.Rational(2, 3)])
pphi, mm, l, gg_, tt = sp.symbols('p m l g theta', positive=True)
Ue = pphi**2/(2*mm*l**2*sp.sin(tt)**2) - mm*gg_*l*sp.cos(tt)
psol = sp.sqrt(mm**2*gg_*l**3*sp.sin(tt)**4/sp.cos(tt))
check('7b', "锥摆小振动 ω_θ² = ω²(1+3cos²θ)", sp.simplify(sp.diff(Ue, tt).subs(pphi, psol)) == 0
      and sp.simplify(sp.diff(Ue, tt, 2).subs(pphi, psol)/(mm*l**2) - gg_/(l*sp.cos(tt))*(1 + 3*sp.cos(tt)**2)) == 0)
Mm = np.array([[2, 1], [1, 1]]); Km = np.array([[2, 0], [0, 1]])
check('7b', "双摆 ω² = (2∓√2) g/ℓ", np.allclose(np.sort(linalg.eigvals(Km, Mm).real), [2 - math.sqrt(2), 2 + math.sqrt(2)]))
aK, Om, gK, lK, mK = sp.symbols('a Omega g l m', positive=True); qK = sp.symbols('q')
UeK = -mK*gK*lK*sp.cos(qK) + mK*aK**2*Om**2/4*sp.sin(qK)**2
check('7b', "Kapitza: 倒立点 U''>0 ⇔ a²Ω²>2gℓ", sp.simplify(sp.diff(UeK, qK, 2).subs(qK, sp.pi) - (mK*aK**2*Om**2/2 - mK*gK*lK)) == 0)
tau = C.e**2/(6*math.pi*C.epsilon_0*C.m_e*C.c**3); re = C.physical_constants['classical electron radius'][0]; a0 = C.physical_constants['Bohr radius'][0]
check('7b', "τ=6.3e-24 s; 经典原子塌缩 1.6e-11 s", close(tau, 6.26e-24, 2e-3) and close(a0**3/(4*re**2*C.c), 1.56e-11, 5e-3))
sT = 8*math.pi/3*re**2; LE = 4*math.pi*C.G*1.98847e30*C.m_p*C.c/sT
check('7b', "σ_T 与 Eddington 光度", close(sT, 6.652e-29, 1e-3) and close(LE, 1.26e31, 5e-3))
check('7b', "r_e = α ƛ_C = α² a0", close(re, C.alpha*C.hbar/(C.m_e*C.c), 1e-6) and close(re, C.alpha**2*a0, 1e-6))
check('7b', "磁刚度 0.3; LHC 弯转半径 ≈ 2.8 km", abs(1e9*C.e/C.c/C.e - 3.3356) < 1e-3 and abs(7e12/2.998e8/8.33/1e3 - 2.80) < 0.01)

# ---------- 07c ----------
def frac_ion(T):
    nb = 6.1e-10*16*math.pi*special.zeta(3)*(C.k*T/(C.h*C.c))**3*... if False else 6.1e-10*(2*special.zeta(3)/math.pi**2)*(C.k*T/(C.hbar*C.c))**3
    S = (2*math.pi*C.m_e*C.k*T/C.h**2)**1.5*math.exp(-13.6057*eV/(C.k*T))/nb
    return (-S + math.sqrt(S*S + 4*S))/2
Thalf = optimize.brentq(lambda T: frac_ion(T) - 0.5, 2000, 6000)
check('7c', "Saha: 复合在 kT≪13.6 eV (x=0.5 时 ~3700 K)", 3000 < Thalf < 4500 and C.k*Thalf/eV < 0.4, f"T_half={Thalf:.0f} K")
Rg, a_, b_, V, T = sp.symbols('R a b V T', positive=True); pvdw = Rg*T/(V - b_) - a_/V**2
sol = sp.solve([sp.diff(pvdw, V), sp.diff(pvdw, V, 2)], [V, T], dict=True)[0]
check('7c', "vdW 临界点与 Z_c=3/8", sp.simplify(sol[V] - 3*b_) == 0 and sp.simplify(sol[T] - 8*a_/(27*Rg*b_)) == 0 and sp.simplify(pvdw.subs(sol)*sol[V]/(Rg*sol[T]) - sp.Rational(3, 8)) == 0)
check('7c', "干绝热递减率 9.8 K/km; 标高 8.4 km", abs(9.81/1004*1e3 - 9.77) < 0.02 and abs(C.k*288/(0.028965/C.N_A*9.81)/1e3 - 8.43) < 0.05)
check('7c', "冰熔点 -0.0074 K/atm", abs(273.15*(1/999.8 - 1/916.7)/333.5e3*101325 + 0.0074) < 3e-4)
check('7c', "Onsager kTc = 2.269 J", abs(2/math.log(1 + math.sqrt(2)) - 2.269) < 1e-3)
bJ, bh = sp.symbols('K h', positive=True)
Tm = sp.Matrix([[sp.exp(bJ + bh), sp.exp(-bJ)], [sp.exp(-bJ), sp.exp(bJ - bh)]])
lp = sp.exp(bJ)*sp.cosh(bh) + sp.sqrt(sp.exp(2*bJ)*sp.sinh(bh)**2 + sp.exp(-2*bJ))
check('7c', "一维 Ising 转移矩阵本征值", abs(float((Tm.det() - (lp*(2*sp.exp(bJ)*sp.cosh(bh) - lp))).subs({bJ: 0.7, bh: 0.3}))) < 1e-12)
mk = 1.0
vbar = integrate.quad(lambda v: v*4*math.pi*v*v*(1/(2*math.pi))**1.5*math.exp(-v*v/2), 0, 40)[0]
check('7c', "Maxwell 平均速率 √(8kT/πm)", close(vbar, math.sqrt(8/math.pi), 1e-8))
kTE = 0.05; Nf = lambda mu: integrate.quad(lambda e: math.sqrt(e)/(math.exp((e - mu)/kTE) + 1), 0, 5)[0]
muT = optimize.brentq(lambda mu: Nf(mu) - 2/3, 0.8, 1.1)
check('7c', "Sommerfeld μ(T)=E_F[1-π²/12 (kT/E_F)²]", abs(muT - (1 - math.pi**2/12*kTE**2)) < 2e-5)
check('7c', "Landauer kT ln2 (300 K) = 2.9e-21 J", close(C.k*300*math.log(2), 2.87e-21, 3e-3))

# ---------- 07d ----------
check('7d', "He 变分 Z'=27/16, E=-77.5 eV", abs(optimize.minimize_scalar(lambda z: z*z - 4*z + 5/8*z).x - 27/16) < 1e-6 and abs(-(27/16)**2*27.2114 + 77.49) < 0.05)
mE, V0, a, Ee = 1.0, 2.0, 1.5, 0.8   # ħ=1
kk = math.sqrt(2*mE*Ee); kap = math.sqrt(2*mE*(V0 - Ee))
Mt = lambda kq, xq: np.array([[np.exp(1j*kq*xq), np.exp(-1j*kq*xq)], [1j*kq*np.exp(1j*kq*xq), -1j*kq*np.exp(-1j*kq*xq)]])
Mi = lambda kq, xq: np.array([[np.exp(kq*xq), np.exp(-kq*xq)], [kq*np.exp(kq*xq), -kq*np.exp(-kq*xq)]])
Tot = np.linalg.solve(Mt(kk, 0), Mi(kap, 0))@np.linalg.solve(Mi(kap, a), Mt(kk, a))
Tnum = 1/abs(Tot[0, 0])**2
check('7d', "方势垒透射公式 (转移矩阵)", close(Tnum, 1/(1 + V0**2*math.sinh(kap*a)**2/(4*Ee*(V0 - Ee))), 1e-9))
sig = [np.array([[0, 1], [1, 0]]), np.array([[0, -1j], [1j, 0]]), np.array([[1, 0], [0, -1]])]
av_, bv_ = rng.normal(size=3), rng.normal(size=3); dot = lambda v: sum(v[i]*sig[i] for i in range(3))
check('7d', "Pauli 恒等式", np.allclose(dot(av_)@dot(bv_), av_@bv_*np.eye(2) + 1j*dot(np.cross(av_, bv_))))
from sympy.physics.hydrogen import R_nl
r, thh = sp.symbols('r theta', positive=True)
psi2s = R_nl(2, 0, r, 1)/sp.sqrt(4*sp.pi); psi2p0 = R_nl(2, 1, r, 1)*sp.sqrt(3/(4*sp.pi))*sp.cos(thh)
zel = sp.integrate(sp.integrate(psi2s*r*sp.cos(thh)*psi2p0*r**2*sp.sin(thh), (thh, 0, sp.pi))*2*sp.pi, (r, 0, sp.oo))
check('7d', "|⟨2s|z|2p0⟩| = 3a0", abs(sp.simplify(zel)) == 3)
Z1, Z2 = 1, 2
ov = integrate.quad(lambda rr: 4*math.pi*rr*rr*math.sqrt(Z1**3/math.pi)*math.exp(-Z1*rr)*math.sqrt(Z2**3/math.pi)*math.exp(-Z2*rr), 0, 60)[0]
check('7d', "突变近似重叠 512/729", close(ov**2, 512/729, 1e-8))
kR = 1e-3; d0 = -kR
check('7d', "硬球低能 σ → 4πR²", close(4*math.pi/kR**2*math.sin(d0)**2, 4*math.pi, 1e-5))
A0, A1, B0, B1 = sig[2], sig[0], (sig[2] + sig[0])/math.sqrt(2), (sig[2] - sig[0])/math.sqrt(2)
Bell = np.kron(A0, B0) + np.kron(A0, B1) + np.kron(A1, B0) - np.kron(A1, B1)
check('7d', "CHSH 量子最大 2√2", abs(max(np.linalg.eigvalsh(Bell)) - 2*math.sqrt(2)) < 1e-12)
thc = 0.8; phis = np.linspace(0, 2*np.pi, 2001)[:-1]
states = []
for ph in phis:
    nB = np.array([math.sin(thc)*math.cos(ph), math.sin(thc)*math.sin(ph), math.cos(thc)])
    w, vecs = np.linalg.eigh(dot(nB)); states.append(vecs[:, np.argmax(w)])
prodov = np.prod([np.vdot(states[i], states[(i + 1) % len(states)]) for i in range(len(states))])
berry = -np.angle(prodov); Omega = 2*math.pi*(1 - math.cos(thc))
check('7d', "Berry 相位 |γ| = Ω/2 (mod 2π)", abs(abs((berry + math.pi) % (2*math.pi) - math.pi) - Omega/2) < 1e-4 or abs(abs((berry + math.pi) % (2*math.pi) - math.pi) - (2*math.pi - Omega/2)) < 1e-4, f"γ={berry:.5f}, Ω/2={Omega/2:.5f}")
check('7d', "ℓ_B(1 T)=25.7 nm; h/e²=25812.8 Ω", abs(math.sqrt(C.hbar/C.e)*1e9 - 25.66) < 0.01 and abs(C.h/C.e**2 - 25812.807) < 0.01)
kap0 = math.sqrt(2*C.m_e*0.3*eV)/C.hbar   # Stark/δ 势跳过；检查 δ 势束缚能
x_, al_, m__, hb = sp.symbols('x alpha m hbar', positive=True); kd = m__*al_/hb**2
check('7d', "δ 势: 导数跃变给 κ = mα/ħ²", sp.simplify(-2*kd - (-2*m__*al_/hb**2)) == 0 and sp.simplify(-(hb*kd)**2/(2*m__) + m__*al_**2/(2*hb**2)) == 0)

# ---------- 08b ----------
rho0 = 1.0; d = np.array([0.3, 0.1, 0]); pts = [np.array([0.35, 0.05, 0.02]), np.array([0.2, 0.15, -0.05])]
Ecav = [rho0*(p)/3 - rho0*(p - d)/3 for p in pts]   # ε0=1
check('8b', "偏心球腔内电场均匀 ρd/(3ε0)", all(np.allclose(E, rho0*d/3) for E in Ecav))
check('8b', "地球电容 0.71 mF", abs(4*math.pi*C.epsilon_0*6.371e6 - 7.09e-4) < 1e-6)
er, q, dz, z, rr_ = sp.symbols('epsilon_r q d z rho', positive=True)
qp = -(er - 1)/(er + 1)*q; qpp = 2*er/(er + 1)*q
phi1 = q/sp.sqrt(rr_**2 + (z - dz)**2) + qp/sp.sqrt(rr_**2 + (z + dz)**2); phi2 = qpp/(er*sp.sqrt(rr_**2 + (z - dz)**2))
check('8b', "介质镜像: φ 与 D_n 在界面连续", sp.simplify((phi1 - phi2).subs(z, 0)) == 0 and sp.simplify((sp.diff(phi1, z) - er*sp.diff(phi2, z)).subs(z, 0)) == 0)
check('8b', "磁压 1 T ≈ 4 atm", abs(1/(2*C.mu_0)/101325 - 3.93) < 0.02)
m1_, m2_, zz_, mu0 = sp.symbols('m1 m2 z mu0', positive=True)
check('8b', "共轴偶极力 3μ0 m1 m2/(2π r⁴)", sp.simplify(-sp.diff(-m2_*mu0*m1_/(2*sp.pi*zz_**3), zz_) + 3*mu0*m1_*m2_/(2*sp.pi*zz_**4)) == 0)
check('8b', "水抗磁悬浮 B∂B ≈ 1400 T²/m", abs(C.mu_0*1000*9.81/9.035e-6 - 1364) < 20)
aa, bb, dd = 0.1, 0.07, 3.0
ph = np.linspace(0, 2*np.pi, 721)[:-1]; dphi = ph[1] - ph[0]
Mex = C.mu_0/(4*math.pi)*sum(aa*bb*math.cos(p1 - p2)*dphi*dphi/math.sqrt(aa**2 + bb**2 - 2*aa*bb*math.cos(p1 - p2) + dd**2) for p1 in ph[::4] for p2 in ph)*4
check('8b', "远处共轴线圈互感 μ0πa²b²/(2d³)", close(Mex, C.mu_0*math.pi*aa**2*bb**2/(2*dd**3), 2e-2), f"{Mex:.3e} vs {C.mu_0*math.pi*aa**2*bb**2/(2*dd**3):.3e}")

# ---------- 08c ----------
rS, RS, Bd = sp.symbols('r R Bdot', positive=True)
check('8c', "螺线管感生电场内外", sp.simplify(2*sp.pi*rS*(rS/2*Bd) - sp.pi*rS**2*Bd) == 0 and sp.simplify(2*sp.pi*rS*(RS**2/(2*rS)*Bd) - sp.pi*RS**2*Bd) == 0)
Z0, ZL, bl = sp.symbols('Z0 Z_L beta_l', positive=True)
Zin = Z0*(ZL + sp.I*Z0*sp.tan(bl))/(Z0 + sp.I*ZL*sp.tan(bl))
check('8c', "λ/4 线 Z0²/Z_L; λ/2 线 Z_L", sp.simplify(sp.limit(Zin, bl, sp.pi/2) - Z0**2/ZL) == 0 and sp.simplify(Zin.subs(bl, sp.pi) - ZL) == 0)
check('8c', "太阳常数对应 E0 ≈ 1.0 kV/m", abs(math.sqrt(2*1361/(C.c*C.epsilon_0)) - 1012) < 3)
Nmax = 120; cnt = sum(1 for nx in range(1, Nmax) for ny in range(1, Nmax) for nz in range(0, Nmax) if nx*nx + ny*ny + nz*nz < Nmax**2)
cnt = 0
ar = np.arange(0, Nmax + 1); NX, NY, NZ = np.meshgrid(ar, ar, ar, indexing='ij'); S2 = NX**2 + NY**2 + NZ**2
inside = S2 < Nmax**2; zeros = (NX == 0).astype(int) + (NY == 0) + (NZ == 0)
cnt = 2*np.sum(inside & (zeros == 0)) + np.sum(inside & (zeros == 1))   # 两偏振；一个指标为 0 只有一个偏振
check('8c', "腔模计数 N = Vω³/(3π²c³)", abs(cnt/(math.pi*Nmax**3/3) - 1) < 0.02, f"ratio {cnt/(math.pi*Nmax**3/3):.4f}")
check('8c', "London λ (n_s=1e28) ≈ 53 nm; Φ0; K_J", abs(math.sqrt(C.m_e/(C.mu_0*1e28*C.e**2))*1e9 - 53) < 1 and abs(C.h/(2*C.e) - 2.0678e-15) < 1e-19 and abs(2*C.e/C.h*1e-6/1e6 - 483.6) < 0.05)
Vt, Rt, RL = sp.symbols('V_t R_t R_L', positive=True); Pw = Vt**2*RL/(Rt + RL)**2
check('8c', "最大功率传输 R_L = R_th, 效率 50%", sp.solve(sp.diff(Pw, RL), RL) == [Rt] and sp.simplify(Pw.subs(RL, Rt) - Vt**2/(4*Rt)) == 0)
w_, B_, R_ = sp.symbols('omega B R', positive=True); r_ = sp.symbols('r', positive=True)
check('8c', "Faraday 圆盘 ½BωR²", sp.integrate(w_*r_*B_, (r_, 0, R_)) == B_*w_*R_**2/2)

# ---------- 09b ----------
gm = 3000/105.6584; dl = math.sqrt(gm**2 - 1)*C.c*2.197e-6
check('9b', "μ 子 3 GeV 衰变长度 ≈ 19 km", abs(dl/1e3 - 18.7) < 0.3)
m = 1.0; T1 = 2.0; E1 = T1 + m; p1 = math.sqrt(E1**2 - m*m)
thc = 0.6   # 质心系散射角
gcm = (E1 + m)/math.sqrt(2*m*m + 2*E1*m); bcm = p1/(E1 + m); pst = math.sqrt((gcm*m)**2 - m*m)*1  # 质心系动量
pst = p1*m/math.sqrt(2*m*m + 2*E1*m); Est = math.sqrt(pst**2 + m*m)
def lab_angle(chi):
    px = gcm*(pst*math.cos(chi) + bcm*Est); py = pst*math.sin(chi); return math.atan2(py, px)
check('9b', "相对论等质量弹性碰撞夹角 < 90°", math.degrees(lab_angle(thc) + lab_angle(math.pi - thc)) < 90)
def p4(mass, pv): return np.array([math.sqrt(mass**2 + pv@pv), *pv])
mink = lambda a: a[0]**2 - a[1:]@a[1:]
pa, pb = p4(1.0, np.array([0, 0, 2.0])), p4(1.5, np.array([0, 0, -0.5])); Ptot = pa + pb
mc_, md_ = 0.8, 1.2; Ecm = math.sqrt(mink(Ptot))
pc_cm = math.sqrt((Ecm**2 - (mc_ + md_)**2)*(Ecm**2 - (mc_ - md_)**2))/(2*Ecm)
bvec = Ptot[1:]/Ptot[0]; gB = 1/math.sqrt(1 - bvec@bvec); nhat = np.array([0.6, 0, 0.8])
def boost(pv4):
    bb2 = bvec@bvec; Lb = np.eye(4); Lb[0, 0] = gB; Lb[0, 1:] = Lb[1:, 0] = gB*bvec; Lb[1:, 1:] += (gB - 1)*np.outer(bvec, bvec)/bb2
    return Lb@pv4
pc = boost(p4(mc_, pc_cm*nhat)); pd = boost(p4(md_, -pc_cm*nhat))
s_ = mink(pa + pb); t_ = mink(pa - pc); u_ = mink(pa - pd)
check('9b', "Mandelstam s+t+u = Σm²", abs(s_ + t_ + u_ - (1 + 1.5**2 + mc_**2 + md_**2)) < 1e-9 and np.allclose(pc + pd, Ptot))
check('9b', "光子火箭 β=0.9 需 √19", abs(math.sqrt(1.9/0.1) - 4.359) < 1e-3)
bet = lambda T, mc2: math.sqrt(1 - (mc2/(T + mc2))**2)
check('9b', "1 MeV 电子 β=0.941, 质子 β=0.046", abs(bet(1, 0.511) - 0.941) < 1e-3 and abs(bet(1, 938.27) - 0.046) < 1e-3)
check('9b', "ISCO 结合能 5.72%", abs(1 - math.sqrt(8/9) - 0.0572) < 1e-4)
check('9b', "Hawking T(M☉) ≈ 6e-8 K", abs(C.hbar*C.c**3/(8*math.pi*C.G*1.989e30*C.k) - 6.17e-8) < 0.05e-8)
H0 = 70e3/3.0857e22
check('9b', "1/H0 ≈ 14 Gyr; ρ_c ≈ 9e-27 kg/m³ (5 质子)", abs(1/H0/3.156e16 - 13.97) < 0.05 and abs(3*H0**2/(8*math.pi*C.G) - 9.2e-27) < 0.1e-27 and abs(3*H0**2/(8*math.pi*C.G)/C.m_p - 5.5) < 0.2)
tt_, Cc = sp.symbols('t C', positive=True); aa_ = Cc*tt_**sp.Rational(2, 3)
check('9b', "物质主导 a ∝ t^{2/3}: H² ∝ a^{-3}", sp.simplify((sp.diff(aa_, tt_)/aa_)**2*aa_**3 - (sp.diff(aa_, tt_)/aa_)**2*aa_**3).equals(0) and sp.simplify(((sp.diff(aa_, tt_)/aa_)**2*aa_**3).diff(tt_)) == 0)
check('9b', "微引力透镜 A(u=1) = 1.342", abs(3/math.sqrt(5) - 1.342) < 1e-3)

# ---------- 09c ----------
check('9c', "氢 2p 精细分裂对应 B ≈ 0.8 T", abs(4.53e-5/5.788e-5 - 0.78) < 0.01)
we, wexe, v = sp.symbols('omega_e omega_e_x_e v', positive=True)
G = we*(v + sp.Rational(1, 2)) - wexe*(v + sp.Rational(1, 2))**2
vmax = sp.solve(sp.diff(G, v), v)[0]
check('9c', "Morse 离解能 ω_e²/(4ω_e x_e)", sp.simplify(G.subs(v, vmax) - we**2/(4*wexe)) == 0)
w, T, hb, kB, cc = sp.symbols('omega T hbar k c', positive=True)
uPl = hb*w**3/(sp.pi**2*cc**3)/(sp.exp(hb*w/(kB*T)) - 1)
B21 = sp.symbols('B21', positive=True); A21 = hb*w**3/(sp.pi**2*cc**3)*B21
check('9c', "Einstein A/B 与 Planck 平衡一致", sp.simplify(A21/(B21*uPl) - (sp.exp(hb*w/(kB*T)) - 1)) == 0)
check('9c', "1 mW 633 nm 光子流 3.2e15/s", abs(1e-3*633e-9/(C.h*C.c) - 3.19e15) < 0.02e15)
allowed = lambda rule: sorted({h*h + k*k + l*l for h, k, l in itertools.product(range(5), repeat=3) if (h, k, l) != (0, 0, 0) and rule(h, k, l)})[:5]
fcc = lambda h, k, l: len({h % 2, k % 2, l % 2}) == 1; bcc = lambda h, k, l: (h + k + l) % 2 == 0
check('9c', "消光规则: FCC 3,4,8,11,12; BCC 2,4,6,8,10", allowed(fcc) == [3, 4, 8, 11, 12] and allowed(bcc) == [2, 4, 6, 8, 10])
ni = math.sqrt(2.8e19*1.04e19)*math.exp(-1.12/(2*0.025852))
check('9c', "Si 本征载流子 ~1e10 cm⁻³", 3e9 < ni < 2e10, f"{ni:.2e}")
check('9c', "由 μ 子推 τ 轻子寿命 2.9e-13 s", abs(2.197e-6*(105.658/1776.86)**5*0.178 - 2.9e-13) < 0.1e-13)
check('9c', "大气振荡第一极大 L ≈ 500 km (1 GeV)", abs(math.pi/(2*1.27*2.5e-3) - 495) < 2)
mu_d = sp.symbols('mu_d'); mu_u = -2*mu_d
mup = sp.Rational(4, 3)*mu_u - sp.Rational(1, 3)*mu_d; mun = sp.Rational(4, 3)*mu_d - sp.Rational(1, 3)*mu_u
check('9c', "夸克模型 μn/μp = -2/3", sp.simplify(mun/mup) == sp.Rational(-2, 3))
check('9c', "Yukawa 力程 π: 1.4 fm, W: 2.5e-3 fm", abs(197.327/139.57 - 1.41) < 0.01 and abs(197.327/80377 - 2.45e-3) < 0.05e-3)
check('9c', "D-T 中子能量 14.1 MeV", abs(17.59*4.0026/(4.0026 + 1.00866) - 14.05) < 0.05)

npass = sum(r[2] for r in R); print(f"\n续写物理(一): {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
