"""续写部分（10b--13c）的符号/数值核验。"""
import math, json
import numpy as np, sympy as sp
from scipy import integrate, special, optimize, signal, stats, constants as C

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(5)
close = lambda a, b, tol=1e-3: abs(a - b) <= tol*abs(b)
eV = C.e

# ---------- 10b ----------
check('10b', "玻璃透镜入水焦距约 4 倍", abs((1.5 - 1)/(1.5/1.333 - 1) - 4) < 0.05)
f1, f2 = sp.symbols('f1 f2', positive=True)
check('10b', "d=f1+f2 时为无焦系统", sp.simplify(1/f1 + 1/f2 - (f1 + f2)/(f1*f2)) == 0)
n = 1.333
def dev(k):   # k 次内反射
    ti = math.acos(math.sqrt((n*n - 1)/((k + 1)**2 - 1))); tr = math.asin(math.sin(ti)/n)
    return math.degrees(k*math.pi + 2*ti - 2*(k + 1)*tr)
check('10b', "主虹 42°、副虹 51°", abs(180 - dev(1) - 42.0) < 0.5 and abs(dev(2) - 180 - 51.0) < 0.5, f"{180-dev(1):.2f}, {dev(2)-180:.2f}")
check('10b', "聚光比上限 ≈ 46000", abs(1/math.sin(math.radians(0.2667))**2 - 46000) < 1500)
nr = 1/1.51; th = math.radians(54.6)
ds = 2*math.atan(math.sqrt(math.sin(th)**2 - nr**2)/math.cos(th)); dp = 2*math.atan(math.sqrt(math.sin(th)**2 - nr**2)/(nr**2*math.cos(th)))
check('10b', "Fresnel 菱体: 54.6° 处 s,p 相移差 45°", abs(math.degrees(dp - ds) - 45) < 0.2, f"{math.degrees(dp-ds):.2f}°")
V1, V2, f = 60, 36, 100.0; fa = f*(V1 - V2)/V1; fb = -f*(V1 - V2)/V2
check('10b', "消色差双合透镜方程", abs(1/fa + 1/fb - 1/f) < 1e-12 and abs(1/(fa*V1) + 1/(fb*V2)) < 1e-12)
check('10b', "模式色散 34 ns/km", abs(1000*1.5/C.c*0.01/1.49*1e9 - 33.6) < 0.2)

# ---------- 10c ----------
Z1, Z2 = 415.0, 1.48e6
check('10c', "空气-水声强透射 ≈ 0.1%", abs(4*Z1*Z2/(Z1 + Z2)**2 - 1.12e-3) < 0.02e-3)
check('10c', "点源距离加倍 -6 dB", abs(10*math.log10(1/4) + 6.02) < 0.01)
check('10c', "Na D 双线拍周期 0.58 mm", abs(589.3e-9**2/0.597e-9*1e3 - 0.582) < 0.005)
nb = sp.symbols('nbar', positive=True); k = sp.symbols('k', integer=True, nonnegative=True)
pk = nb**k/(1 + nb)**(k + 1)
m1 = sp.summation(k*pk, (k, 0, sp.oo)); m2 = sp.summation(k*(k - 1)*pk, (k, 0, sp.oo))
check('10c', "热光 g2(0)=2, 方差 n̄+n̄²", sp.simplify(m2.subs(nb, sp.Rational(3, 2))/m1.subs(nb, sp.Rational(3, 2))**2) == 2)
I = rng.exponential(size=200000)
check('10c', "全展散斑对比度 1；N 张叠加 1/√N", abs(I.std()/I.mean() - 1) < 0.01 and abs(I.reshape(-1, 16).mean(1).std()/I.mean() - 0.25) < 0.01)
check('10c', "石英零级 λ/4 片 ≈ 17 μm", abs(633e-9/(4*0.0091)*1e6 - 17.4) < 0.1)
hbar, kB = C.hbar, C.k; mNa = 22.99*C.atomic_mass; kNa = 2*math.pi/589.0e-9
TD = hbar*2*math.pi*9.795e6/(2*kB); TDRb = hbar*2*math.pi*6.0666e6/(2*kB); Tr = (hbar*kNa)**2/(mNa*kB)
amax = hbar*kNa*2*math.pi*9.795e6/2/mNa
check('10c', "Doppler 极限 Na 240 μK、Rb 146 μK；反冲 2.4 μK；加速度 ~1e5 g", abs(TD*1e6 - 235) < 6 and abs(TDRb*1e6 - 146) < 1 and abs(Tr*1e6 - 2.4) < 0.1 and 5e4 < amax/9.81 < 2e5, f"{TD*1e6:.0f} μK, a={amax/9.81:.1e} g")

# ---------- 11b ----------
w, R1, R2, C1, C2 = sp.symbols('omega R1 R2 C1 C2', positive=True)
Zp = lambda Rr, Cc: Rr/(1 + sp.I*w*Rr*Cc)
H = Zp(R2, C2)/(Zp(R1, C1) + Zp(R2, C2))
check('11b', "探头补偿 R1C1=R2C2 时分压比与频率无关", sp.simplify(H.subs(C1, R2*C2/R1) - R2/(R1 + R2)) == 0)
check('11b', "一阶系统 t_r·BW = 0.35", abs(math.log(9)/(2*math.pi) - 0.35) < 0.001)
Nb = 12; tt = np.arange(200000); xs = (2**(Nb - 1) - 1)*np.sin(2*np.pi*tt*0.0123457)
qerr = np.round(xs) - xs; snr = 10*math.log10(np.mean(xs**2)/np.mean(qerr**2))
check('11b', "量化噪声 q/√12; SNR=6.02N+1.76 dB", abs(qerr.std() - 1/math.sqrt(12)) < 2e-3 and abs(snr - (6.02*Nb + 1.76)) < 0.3, f"{snr:.2f} dB")
check('11b', "50 MHz, ΔL=1 m ⇒ 60°", abs(math.degrees(2*math.pi*50e6*1/C.c) - 60.0) < 0.1)
check('11b', "Si 633 nm (η=0.8) 响应度 0.41 A/W", abs(0.8*C.e*633e-9/(C.h*C.c) - 0.408) < 0.002)

# ---------- 11c ----------
Bb, G = sp.symbols('B Gamma', positive=True)
Lz = 1/(Bb**2 + G**2); dL = sp.diff(Lz, Bb); pk_ = sp.solve(sp.diff(dL, Bb), Bb)
check('11c', "Lorentz 导数线峰峰间距 = (2/√3)·HWHM", any(sp.simplify(2*r - 2*G/sp.sqrt(3)) == 0 for r in pk_))
check('11c', "Mössbauer ⁵⁷Fe 线宽速度 ≈ 0.1 mm/s；Pound-Rebka 2.45e-15", abs(C.c*4.7e-9/14.4e3*1e3 - 0.098) < 0.003 and abs(9.81*22.5/C.c**2 - 2.46e-15) < 0.02e-15)
E = 661.657; me = 510.999
check('11c', "Cs-137 Compton 边 478 keV、背散射 184 keV", abs(2*E*E/(me + 2*E) - 477.3) < 0.5 and abs(E/(1 + 2*E/me) - 184.3) < 0.5)
muBh = C.physical_constants['Bohr magneton in Hz/T'][0]*1e-4/1e6   # MHz/G
check('11c', "Rb g_F: 0.700 / 0.467 MHz/G", abs(muBh/2 - 0.700) < 0.001 and abs(muBh/3 - 0.4665) < 0.001)
RinfH = C.Rydberg/(1 + C.m_e/C.m_p); RinfD = C.Rydberg/(1 + C.m_e/(2.01355*C.atomic_mass - C.m_e*0))
lamH = 1/(RinfH*(1/4 - 1/9)); lamD = 1/(C.Rydberg/(1 + C.m_e/C.physical_constants['deuteron mass'][0])*(1/4 - 1/9))
check('11c', "H_α 与 D_α 差 0.18 nm (真空波长)", abs((lamH - lamD)*1e9 - 0.179) < 0.003, f"{(lamH-lamD)*1e9:.4f} nm")
kk, mu = 20, 50.0; Ds = []
for _ in range(20000):
    xx = rng.poisson(mu, kk); Ds.append((kk - 1)*xx.var(ddof=1)/xx.mean())
check('11c', "离散指数 ~ χ²_{k-1}", abs(np.mean(Ds) - (kk - 1)) < 0.2 and abs(np.var(Ds) - 2*(kk - 1)) < 2)

# ---------- 12b ----------
check('12b', "零事件上限 2.30/3.00；n=1,2 的 90% 上限 3.89/5.32", abs(-math.log(0.1) - 2.303) < 1e-3 and abs(-math.log(0.05) - 2.996) < 1e-3
      and abs(optimize.brentq(lambda m: stats.poisson.cdf(1, m) - 0.1, 1, 10) - 3.890) < 1e-3 and abs(optimize.brentq(lambda m: stats.poisson.cdf(2, m) - 0.1, 1, 10) - 5.322) < 1e-3)
Zas = lambda s, b: math.sqrt(2*((s + b)*math.log(1 + s/b) - s))
check('12b', "Asimov Z → s/√b (s≪b); 5σ p=2.87e-7", abs(Zas(1, 1e4)/(1/100) - 1) < 1e-3 and abs(stats.norm.sf(5) - 2.87e-7) < 0.01e-7 and abs(stats.norm.sf(3) - 1.35e-3) < 0.01e-3)
s1, s2, rho = 1.0, 2.0, 0.3; V = np.array([[s1**2, rho*s1*s2], [rho*s1*s2, s2**2]]); one = np.ones(2)
wg = np.linalg.solve(V, one)/(one@np.linalg.solve(V, one))
check('12b', "BLUE 权重与方差", abs(wg[0] - (s2**2 - rho*s1*s2)/(s1**2 + s2**2 - 2*rho*s1*s2)) < 1e-12 and abs(1/(one@np.linalg.solve(V, one)) - s1**2*s2**2*(1 - rho**2)/(s1**2 + s2**2 - 2*rho*s1*s2)) < 1e-12)
s1, s2, rho = 1.0, 2.0, 0.7; wv = (s2**2 - rho*s1*s2)/(s1**2 + s2**2 - 2*rho*s1*s2)
check('12b', "ρ > σ1/σ2 时出现负权重", (1 - wv) < 0)
check('12b', "MAD 因子 1.4826", abs(1/stats.norm.ppf(0.75) - 1.4826) < 1e-4)
y = rng.normal(size=2**16); taus = [2**j for j in range(1, 10)]
adev = [math.sqrt(0.5*np.mean(np.diff(y[:len(y)//tt*tt].reshape(-1, tt).mean(1))**2)) for tt in taus]
check('12b', "白噪声 Allan 偏差斜率 -1/2", abs(np.polyfit(np.log(taus), np.log(adev), 1)[0] + 0.5) < 0.05)
Nc, sg = 400, 1.0; cents = [rng.normal(0, sg, Nc).mean() for _ in range(5000)]
check('12b', "峰位精度 σ/√N", abs(np.std(cents) - sg/math.sqrt(Nc)) < 0.002)

# ---------- 12c ----------
fs, Nm = 1000.0, 20; ff = np.linspace(1, 499, 9981)
Hm = np.abs(np.sin(np.pi*ff*Nm/fs)/(Nm*np.sin(np.pi*ff/fs)))
check('12c', "滑动平均第一零点 f_s/N", abs(ff[np.argmin(Hm[ff < 60])] - fs/Nm) < 0.1)
Nw = 4096; win = signal.windows.hann(Nw, sym=False)
enbw = Nw*np.sum(win**2)/np.sum(win)**2
sc = lambda wv: -20*math.log10(abs(np.sum(wv*np.exp(-1j*np.pi*np.arange(Nw)/Nw)))/np.sum(wv))
check('12c', "Hann ENBW 1.5 格；扇贝损失 Hann 1.42 / 矩形 3.92 dB", abs(enbw - 1.5) < 1e-3 and abs(sc(win) - 1.42) < 0.01 and abs(sc(np.ones(Nw)) - 3.92) < 0.01)
x = rng.normal(0, 2.0, 8192); X = np.fft.rfft(x); Sk = 2*np.abs(X)**2/(fs*8192)
check('12c', "单边 PSD 归一化满足 Parseval", abs(np.sum(Sk[1:-1])*fs/8192/np.mean(x**2) - 1) < 0.01)
alpha, xmin = 2.5, 1.0; samp = xmin*(1 - rng.random(20000))**(-1/(alpha - 1))
ahat = 1 + len(samp)/np.sum(np.log(samp/xmin))
check('12c', "幂律指数 MLE", abs(ahat - alpha) < 3*(alpha - 1)/math.sqrt(len(samp)), f"{ahat:.4f}")
tv = np.linspace(0, 10, 401); tau, Bg = 2.0, 3.0; yv = 5*np.exp(-tv/tau) + Bg + rng.normal(0, 0.002, tv.size)
dt = 80; dif = yv[:-dt] - yv[dt:]; slope = np.polyfit(tv[:-dt][:200], np.log(dif[:200]), 1)[0]
check('12c', "Guggenheim 法求 τ（未知本底）", abs(-1/slope - tau) < 0.02, f"{-1/slope:.4f}")
check('12c', "FWHM 2.355σ；面积系数 1.064 / 1.571", abs(2*math.sqrt(2*math.log(2)) - 2.3548) < 1e-4 and abs(math.sqrt(math.pi/(4*math.log(2))) - 1.0645) < 1e-4 and abs(math.pi/2 - 1.5708) < 1e-4)
sG, gL = 1.0, 0.7; xx = np.linspace(-15, 15, 300001); vp = special.voigt_profile(xx, sG, gL)
above = xx[vp >= vp.max()/2]; fwhm = above[-1] - above[0]; fG, fL = 2.3548*sG, 2*gL
check('12c', "Voigt 宽度近似 (0.02%)", abs((0.5346*fL + math.sqrt(0.2166*fL**2 + fG**2))/fwhm - 1) < 3e-4)
check('12c', "Savitzky-Golay 5 点二次一阶导系数", np.allclose(signal.savgol_coeffs(5, 2, deriv=1, use='dot'), np.array([-2, -1, 0, 1, 2])/10))
z = rng.normal(3, 1, 50); xk, P = 0.0, 1e12
for zi in z: Kk = P/(P + 1.0); xk += Kk*(zi - xk); P = P*1.0/(P + 1.0)   # 稳定形式，避免 1-K 相消
check('12c', "Kalman (Q=0) = 逐次平均", abs(xk - z.mean()) < 1e-9)
a2, b2, c2 = -1.3, 0.37, 2.0; pts = np.array([-1, 0, 1]); yy = a2*(pts - b2)**2 + c2
delta = 0.5*(yy[0] - yy[2])/(yy[0] - 2*yy[1] + yy[2])
check('12c', "抛物线插值精确定峰", abs(delta - b2) < 1e-12 and abs(yy[1] - 0.25*(yy[0] - yy[2])*delta - c2) < 1e-12)
Ns, om = 400, 2*np.pi*5/400; tt = np.arange(Ns); As = []
for _ in range(3000):
    yy = 1.0*np.cos(om*tt) + rng.normal(0, 0.5, Ns); Xd = np.stack([np.cos(om*tt), np.sin(om*tt), np.ones(Ns)], 1)
    As.append(np.linalg.lstsq(Xd, yy, rcond=None)[0][0])
check('12c', "正弦振幅误差 σ√(2/N)", abs(np.std(As) - 0.5*math.sqrt(2/Ns)) < 0.002)

# ---------- 13b ----------
Tsun, Rsun, AU = 5772, 6.957e8, 1.496e11
check('13b', "地球平衡温度 255 K", abs(Tsun*math.sqrt(Rsun/(2*AU))*0.7**0.25 - 254.6) < 1)
check('13b', "K⁺ Nernst 电位 -89 mV (37°C)", abs(C.k*310.15/C.e*math.log(5/140)*1e3 + 89) < 1)
check('13b', "Arrhenius 每 10 K 翻倍 ⇔ E_a≈52 kJ/mol", abs(math.log(2)*C.R/(1/295 - 1/305)/1e3 - 51.9) < 1)
r_, K_, N0, t_ = sp.symbols('r K N0 t', positive=True); Nt = K_/(1 + (K_ - N0)/N0*sp.exp(-r_*t_))
check('13b', "Logistic 解", sp.simplify(sp.diff(Nt, t_) - r_*Nt*(1 - Nt/K_)) == 0)
x_, y_, a_, b_, g_, d_ = sp.symbols('x y alpha beta gamma delta', positive=True)
Vlv = d_*x_ - g_*sp.log(x_) + b_*y_ - a_*sp.log(y_)
check('13b', "Lotka-Volterra 守恒量", sp.simplify(sp.diff(Vlv, x_)*(a_*x_ - b_*x_*y_) + sp.diff(Vlv, y_)*(d_*x_*y_ - g_*y_)) == 0)
check('13b', "SIR R0=2 最终规模 0.797", abs(optimize.brentq(lambda z: z - 1 + math.exp(-2*z), 0.1, 1) - 0.7968) < 1e-3)
xv = 0.3; lyap = 0.0
for i in range(200000):
    xv = 4*xv*(1 - xv); lyap += math.log(abs(4 - 8*xv)) if i > 100 else 0
check('13b', "Logistic r=4 Lyapunov 指数 ln2", abs(lyap/(200000 - 101) - math.log(2)) < 0.01)
r3 = 1 + math.sqrt(8) + 0.001; xv = 0.5
for _ in range(5000): xv = r3*xv*(1 - xv)
orbit = []
for _ in range(9): xv = r3*xv*(1 - xv); orbit.append(xv)
check('13b', "r 略大于 1+√8 时稳定 3 周期", abs(orbit[0] - orbit[3]) < 1e-8 and abs(orbit[0] - orbit[1]) > 1e-3)
check('13b', "Shannon: 3 kHz/30 dB ≈ 30 kbit/s; 极限 -1.59 dB", abs(3000*math.log2(1001)/1e3 - 29.9) < 0.1 and abs(10*math.log10(math.log(2)) + 1.59) < 0.01)

# ---------- 13c ----------
t, m, g, w0 = sp.symbols('t m gamma omega0', positive=True); wd = sp.sqrt(w0**2 - g**2/4)
Gt = sp.exp(-g*t/2)*sp.sin(wd*t)/(m*wd)
check('13c', "阻尼振子 Green 函数满足方程与初条件", sp.simplify(m*(sp.diff(Gt, t, 2) + g*sp.diff(Gt, t) + w0**2*Gt)) == 0 and Gt.subs(t, 0) == 0 and sp.simplify(sp.diff(Gt, t).subs(t, 0) - 1/m) == 0)
x, al, Ts, T0 = sp.symbols('x alpha T_s T_0', positive=True)
Tsol = Ts + (T0 - Ts)*sp.erf(x/(2*sp.sqrt(al*t)))
check('13c', "erf 解满足热方程; 表面热流 ∝ t^{-1/2}", sp.simplify(sp.diff(Tsol, t) - al*sp.diff(Tsol, x, 2)) == 0 and sp.simplify(sp.diff(Tsol, x).subs(x, 0) - (T0 - Ts)/sp.sqrt(sp.pi*al*t)) == 0)
lam = 4000.0; mm = np.arange(1, 200)
Nev = np.sum((np.pi**2*(mm[:, None]**2 + mm[None, :]**2)) < lam)
check('13c', "Weyl 定律 (单位正方形, 含边界项)", abs(Nev - (lam/(4*math.pi) - 4*math.sqrt(lam)/(4*math.pi))) < 0.03*Nev, f"{Nev} vs {lam/(4*math.pi)-math.sqrt(lam)/math.pi:.1f}")
steps = rng.normal(size=(5000, 400, 3)); steps /= np.linalg.norm(steps, axis=2, keepdims=True)
r2 = np.mean(np.sum(steps.sum(1)**2, 1))
check('13c', "3D 随机游走 ⟨r²⟩ = 6Dt, D = ℓ²/(6τ)", abs(r2/(6*(1/6)*400) - 1) < 0.02)
kap = math.sqrt(2*C.m_e*4*eV)/C.hbar
check('13c', "STM: κ≈1 Å⁻¹, 每 Å 电流变 ~7 倍", abs(kap*1e-10 - 1.02) < 0.01 and 6 < math.exp(2*kap*1e-10) < 9)
check('13c', "Casimir 1 μm: 1.3 mPa; 10 nm ≈ 1 atm", abs(math.pi**2*C.hbar*C.c/(240*1e-24) - 1.3e-3) < 0.02e-3 and 0.8 < math.pi**2*C.hbar*C.c/(240*1e-32)/101325 < 1.5)
eps = 1e-3; mcw = optimize.brentq(lambda mm_: mm_ - math.tanh(mm_/(1 - eps)), 1e-3, 1)
check('13c', "Curie-Weiss: m ≈ √(3(1-T/Tc))", abs(mcw/math.sqrt(3*eps) - 1) < 2e-3)
wv, kp, gp, kT = sp.symbols('omega kappa gamma kT', positive=True); chi = 1/(kp - sp.I*gp*wv)
check('13c', "经典 FDT 与 Langevin 谱一致", sp.simplify(2*kT/wv*sp.im(chi) - 2*gp*kT/(kp**2 + gp**2*wv**2)) == 0)
check('13c', "kTC: 1 pF → 64 μV, 约 400 e", abs(math.sqrt(C.k*300/1e-12)*1e6 - 64.4) < 0.5 and abs(math.sqrt(C.k*300*1e-12)/C.e - 402) < 3)

npass = sum(r[2] for r in R); print(f"\n续写物理(二): {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
