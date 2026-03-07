import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
from datetime import datetime, timedelta
from scipy.stats import lognorm, pareto, poisson
import matplotlib
import matplotlib.font_manager as fm

# ---------- Vantage Alpin palette (from HTML) ----------
BG      = '#F0EFF0'
CARD    = '#DCDBDC'
PRIMARY = '#334C65'
ACCENT  = '#D4723C'
TEXT    = '#000000'
MUTED   = '#555555'
WHITE   = '#FFFFFF'
BORDER  = '#B8B7B8'

# Extended palette derived from the base
GREEN   = '#4A7A5B'
PURPLE  = '#6B5B8A'
BLUE_LT = '#5B8FAF'
RED_SM  = '#B84A3C'

plt.rcParams.update({
    'figure.facecolor': BG,
    'axes.facecolor': WHITE,
    'axes.edgecolor': BORDER,
    'axes.labelcolor': MUTED,
    'text.color': TEXT,
    'xtick.color': MUTED,
    'ytick.color': MUTED,
    'grid.color': BORDER,
    'grid.alpha': 0.45,
    'grid.linewidth': 0.5,
    'font.size': 10,
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'axes.titlecolor': PRIMARY,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Inter', 'DejaVu Sans'],
})

np.random.seed(42)

fig = plt.figure(figsize=(19.20, 10.80), dpi=100)
gs = GridSpec(3, 4, figure=fig, hspace=0.38, wspace=0.32,
             left=0.05, right=0.97, top=0.91, bottom=0.06)

# ===== 1) Customer Activity – Zipf =====
ax1 = fig.add_subplot(gs[0, 0])
activities = np.random.zipf(2.0, 5000)
activities_clipped = np.clip(activities, 1, 60)
bins = np.arange(1, 62) - 0.5
ax1.hist(activities_clipped, bins=bins, color=PRIMARY, alpha=0.82, edgecolor=WHITE, linewidth=0.3, density=True)
ax1.set_title('I.  Customer Activity  ·  Zipf(a = 2.0)')
ax1.set_xlabel('Activity score')
ax1.set_ylabel('Density')
ax1.set_xlim(0, 40)
ax1.grid(True, axis='y')

# ===== 2) Product Prices – Lognormal =====
ax2 = fig.add_subplot(gs[0, 1])
x_price = np.linspace(10, 800, 500)
configs = [
    (4.4, 0.6, 'Clothing (μ=4.4)',   ACCENT),
    (4.8, 0.5, 'Footwear (μ=4.8)',   PRIMARY),
    (5.0, 0.7, 'Equipment (μ=5.0)',  GREEN),
]
for mu, sigma, label, color in configs:
    pdf = lognorm.pdf(x_price, s=sigma, scale=np.exp(mu))
    ax2.fill_between(x_price, pdf, alpha=0.18, color=color)
    ax2.plot(x_price, pdf, color=color, lw=2.2, label=label)
ax2.axvline(80, color=MUTED, ls='--', lw=0.8, alpha=0.5)
ax2.axvline(180, color=MUTED, ls='--', lw=0.8, alpha=0.5)
ymax2 = ax2.get_ylim()[1]
ax2.text(45,  ymax2*0.88, 'Budget',  fontsize=7, color=MUTED, ha='center')
ax2.text(130, ymax2*0.88, 'Mid',     fontsize=7, color=MUTED, ha='center')
ax2.text(350, ymax2*0.88, 'Premium', fontsize=7, color=MUTED, ha='center')
ax2.set_title('II.  Base Prices  ·  Lognormal by Category')
ax2.set_xlabel('Price (€)')
ax2.set_ylabel('Density')
ax2.legend(fontsize=7.5, loc='upper right', framealpha=0.6, edgecolor=BORDER)
ax2.grid(True, axis='y')

# ===== 3) Product Popularity – Pareto =====
ax3 = fig.add_subplot(gs[0, 2])
pop_scores = pareto.rvs(2.5, size=500)
pop_sorted = np.sort(pop_scores)[::-1]
rank = np.arange(1, 501)
ax3.scatter(rank, pop_sorted, s=10, color=ACCENT, alpha=0.7, edgecolors='none', zorder=3)
ax3.set_title('III.  Product Popularity  ·  Pareto(a = 2.5)')
ax3.set_xlabel('Product rank')
ax3.set_ylabel('Popularity score')
ax3.set_yscale('log')
ax3.grid(True)

# ===== 4) Basket Size Distribution =====
ax4 = fig.add_subplot(gs[0, 3])
sizes = [1, 2, 3, 4]
probs = [0.50, 0.30, 0.15, 0.05]
colors_basket = [PRIMARY, BLUE_LT, ACCENT, RED_SM]
bars = ax4.bar(sizes, probs, color=colors_basket, edgecolor=WHITE, width=0.55, alpha=0.88, linewidth=0.5)
for bar, p in zip(bars, probs):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.012,
             f'{p:.0%}', ha='center', fontsize=9.5, color=TEXT, fontweight='bold')
ax4.set_title('IV.  Basket Size Distribution')
ax4.set_xlabel('Items per order')
ax4.set_ylabel('Probability')
ax4.set_ylim(0, 0.60)
ax4.set_xticks(sizes)
ax4.grid(True, axis='y')

# ===== 5) Weekly Seasonality =====
ax5 = fig.add_subplot(gs[1, 0])
days_w = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
weekly = [0.90, 0.85, 0.90, 0.95, 1.00, 1.20, 1.30]
colors_w = [PRIMARY if w < 1.0 else (GREEN if w > 1.0 else BLUE_LT) for w in weekly]
ax5.bar(days_w, weekly, color=colors_w, edgecolor=WHITE, width=0.52, alpha=0.85, linewidth=0.5)
ax5.axhline(1.0, color=ACCENT, ls='--', lw=1.2, alpha=0.7)
ax5.set_title('V.  Weekly Seasonality  ·  M_week')
ax5.set_ylabel('Multiplier')
ax5.set_ylim(0.7, 1.45)
ax5.grid(True, axis='y')

# ===== 6) Composite Seasonality Timeline =====
ax6 = fig.add_subplot(gs[1, 1:3])
start = datetime(2023, 1, 1)
T = 731
dates = [start + timedelta(days=t) for t in range(T)]

m_trend = np.array([1.0 + (0.20 / T) * t for t in range(T)])
weekly_map = {0: 0.90, 1: 0.85, 2: 0.90, 3: 0.95, 4: 1.00, 5: 1.20, 6: 1.30}
m_week = np.array([weekly_map[d.weekday()] for d in dates])
m_month = np.array([1.15 if d.day > 25 else 1.0 for d in dates])

def event_mult(d):
    md = (d.month, d.day)
    if (7, 15) <= md <= (7, 30): return 1.5
    if (11, 20) <= md <= (11, 27): return 3.0
    if (12, 1) <= md <= (12, 15): return 1.8
    if (12, 24) <= md <= (12, 26): return 0.2
    return 1.0

m_event = np.array([event_mult(d) for d in dates])
m_total = m_trend * m_week * m_month * m_event
m_smooth = np.convolve(m_total, np.ones(7)/7, mode='same')

ax6.fill_between(dates, m_smooth, alpha=0.20, color=PRIMARY)
ax6.plot(dates, m_smooth, color=PRIMARY, lw=1.3, label='M_total (7d avg)')
for d in dates:
    ev = event_mult(d)
    if ev == 3.0:
        ax6.axvspan(d, d + timedelta(days=1), color=ACCENT, alpha=0.12)
    elif ev == 1.8:
        ax6.axvspan(d, d + timedelta(days=1), color=ACCENT, alpha=0.06)
    elif ev == 1.5:
        ax6.axvspan(d, d + timedelta(days=1), color=GREEN, alpha=0.06)

ax6.set_title('VI.  Composite Seasonality  ·  M_total(t) = M_trend × M_week × M_month × M_event')
ax6.set_ylabel('Multiplier')
ax6.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax6.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax6.xaxis.get_majorticklabels(), rotation=30, ha='right')
ax6.legend(fontsize=8, loc='upper left', framealpha=0.6, edgecolor=BORDER)
ax6.grid(True)

# ===== 7) Return Probability by Category =====
ax7 = fig.add_subplot(gs[1, 3])
cats = ['Equipment\n(r = 0.05)', 'Clothing\n(r = 0.15)', 'Footwear\n(r = 0.30)']
ret_probs = [0.05, 0.15, 0.30]
bars_r = ax7.barh(cats, ret_probs, color=[GREEN, ACCENT, RED_SM],
                  edgecolor=WHITE, height=0.45, alpha=0.85, linewidth=0.5)
for bar, p in zip(bars_r, ret_probs):
    ax7.text(bar.get_width() + 0.008, bar.get_y() + bar.get_height()/2,
             f'{p:.0%}', va='center', fontsize=10, color=TEXT, fontweight='bold')
ax7.set_title('VII.  Return Probability')
ax7.set_xlabel('Probability')
ax7.set_xlim(0, 0.40)
ax7.grid(True, axis='x')

# ===== 8) Simulated Daily Orders (Poisson) =====
ax8 = fig.add_subplot(gs[2, 0:2])
lam_de = 50 * m_total
lam_at = 15 * m_total
lam_ch = 10 * m_total
orders_de = np.random.poisson(lam_de)
orders_at = np.random.poisson(lam_at)
orders_ch = np.random.poisson(lam_ch)

ax8.fill_between(dates, orders_de, alpha=0.30, color=PRIMARY, label='DE (λ = 50)')
ax8.fill_between(dates, orders_at, alpha=0.35, color=ACCENT, label='AT (λ = 15)')
ax8.fill_between(dates, orders_ch, alpha=0.35, color=GREEN, label='CH (λ = 10)')
ax8.set_title('VIII.  Simulated Daily Orders  ·  Poisson(λ_k(t))')
ax8.set_xlabel('Date')
ax8.set_ylabel('Order count')
ax8.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax8.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax8.xaxis.get_majorticklabels(), rotation=30, ha='right')
ax8.legend(fontsize=8, loc='upper left', framealpha=0.6, edgecolor=BORDER)
ax8.grid(True)

# ===== 9) Poisson PMF examples =====
ax9 = fig.add_subplot(gs[2, 2])
for lam, label, color in [(10, 'CH base (λ = 10)', GREEN),
                           (50, 'DE base (λ = 50)', PRIMARY),
                           (150, 'DE Black Week (λ ≈ 150)', ACCENT)]:
    k_vals = np.arange(max(0, lam - 4*int(np.sqrt(lam))), lam + 4*int(np.sqrt(lam)) + 1)
    pmf = poisson.pmf(k_vals, lam)
    ax9.plot(k_vals, pmf, color=color, lw=2, label=label)
    ax9.fill_between(k_vals, pmf, alpha=0.12, color=color)
ax9.set_title('IX.  Poisson PMF at Key λ Values')
ax9.set_xlabel('Order count')
ax9.set_ylabel('P(X = n)')
ax9.legend(fontsize=7.5, loc='upper right', framealpha=0.6, edgecolor=BORDER)
ax9.grid(True)

# ===== 10) Operational Delays =====
ax10 = fig.add_subplot(gs[2, 3])
ship_days = np.arange(1, 6)
ship_pmf = np.ones(5) / 5
ret_days = np.arange(7, 31)
ret_pmf = np.ones(24) / 24

ax10.bar(ship_days, ship_pmf, color=PRIMARY, alpha=0.85, width=0.4,
         label='Shipping U{1,5}', edgecolor=WHITE, linewidth=0.5)
ax10.bar(ret_days, ret_pmf, color=ACCENT, alpha=0.7, width=0.8,
         label='Return U{7,30}', edgecolor=WHITE, linewidth=0.3)
ax10.set_title('X.  Operational Delay Distributions')
ax10.set_xlabel('Days post-event')
ax10.set_ylabel('Probability')
ax10.legend(fontsize=8, loc='upper right', framealpha=0.6, edgecolor=BORDER)
ax10.grid(True, axis='y')

# ===== Suptitle =====
fig.suptitle('Vantage Alpin  ·  Data Generating Process Overview',
             fontsize=20, fontweight='bold', color=PRIMARY, y=0.97,
             fontfamily='sans-serif')

out_path = '/home/claude/dgp_overview_1920x1080.png'
fig.savefig(out_path, dpi=600, facecolor=BG)
plt.close()
print(f'Saved to {out_path}')
