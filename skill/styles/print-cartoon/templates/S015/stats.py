"""S015 你总排到慢的那队 — every number in the film comes from this simulation (seeded, reproducible) → data/stats_out.txt
Model: 3 cashiers, Poisson arrivals, busy 90 % of the time, service time lognormal (mean 1 min, CV 1: most checkouts quick, a few very slow).
  separate : each arrival joins the shortest line (people waiting + being served), ties random, nobody switches
  snake    : one shared line, the next free cashier takes the next person
Both see exactly the same arrivals and the same service times."""
import numpy as np, json, os
rng = np.random.default_rng(15)
C, RHO, N = 3, 0.90, 400_000
CV = 1.0
s2 = np.log(1 + CV ** 2); mu = -s2 / 2                          # lognormal with mean 1
svc = rng.lognormal(mu, np.sqrt(s2), N)
arr = np.cumsum(rng.exponential(1 / (C * RHO), N))

st = np.empty(N)                                                # service start times of the separate-lines run


def separate():
    free = np.zeros(C)                                          # time each cashier finishes its whole line
    ends = [[] for _ in range(C)]                               # departure times per line (to count people present)
    wait = np.empty(N)
    for i in range(N):
        t = arr[i]
        n = np.array([sum(1 for d in ends[k][-60:] if d > t) for k in range(C)])
        ks = np.flatnonzero(n == n.min()); k = ks[rng.integers(len(ks))]
        start = max(t, free[k]); wait[i] = start - t
        free[k] = start + svc[i]; ends[k].append(free[k]); st[i] = start
    return wait

def snake():
    free = np.zeros(C); wait = np.empty(N)
    for i in range(N):
        k = free.argmin(); start = max(arr[i], free[k]); wait[i] = start - arr[i]; free[k] = start + svc[i]
    return wait

out = {}
for name, w in (('separate', separate()), ('snake', snake())):
    w = w[N // 10:]                                             # drop warm-up
    out[name] = dict(mean=w.mean(), p50=np.percentile(w, 50), p90=np.percentile(w, 90), p99=np.percentile(w, 99), sd=w.std(),
                     over5=(w > 5).mean(), tail10_mean=w[w >= np.percentile(w, 90)].mean())
    out[name]['q100'] = np.percentile(w, np.arange(100) + .5).tolist()       # 100 trips sorted by wait (the bar chart in act 2)
    out[name]['hist'] = np.histogram(w, bins=24, range=(0, 12))[0].tolist()

# overtaken: someone who arrived AFTER you starts paying BEFORE you (impossible in one shared line)
lo = N // 10
later_first = np.empty(N - lo - 50)
for j, i in enumerate(range(lo, N - 50)):
    later_first[j] = (st[i + 1:i + 50] < st[i]).sum()
out['separate']['overtaken_frac'] = (later_first > 0).mean()
out['separate']['overtaken_mean'] = later_first.mean()

# "your line is the fastest": three lines, 4 people ahead in each, same service-time law; whose last person finishes first
T = 100_000
tot = rng.lognormal(mu, np.sqrt(s2), (T, 3, 5)).sum(2)
out['p_fastest_3'] = (tot[:, 0] < tot[:, 1:].min(1)).mean()
# running share of trips where your line won (the on-screen tally converges on this)
seq = (tot[:1000, 0] < tot[:1000, 1:].min(1)).astype(int)
out['tally1000'] = seq.tolist(); out['tally1000_frac'] = seq.mean()
tot5 = rng.lognormal(mu, np.sqrt(s2), (T, 5, 5)).sum(2)
out['p_fastest_5'] = (tot5[:, 0] < tot5[:, 1:].min(1)).mean()
# 100 trips to the shop (the tally shown on screen), seed fixed so the film is reproducible
r2 = np.random.default_rng(1015)
trips = r2.lognormal(mu, np.sqrt(s2), (100, 3, 5)).sum(2)
win = trips[:, 0] < trips[:, 1:].min(1)
out['trips_win'] = int(win.sum()); out['trips_seq'] = win.astype(int).tolist()
out['params'] = dict(cashiers=C, busy=RHO, service_mean_min=1.0, service_cv=CV, customers=N)

json.dump(out, open('data/stats.json', 'w'), indent=1, default=float)
with open('data/stats_out.txt', 'w') as f:
    for k in ('separate', 'snake'):
        d = out[k]; f.write(f"{k:9s} mean {d['mean']:.2f}  p50 {d['p50']:.2f}  p90 {d['p90']:.2f}  p99 {d['p99']:.2f}  sd {d['sd']:.2f}  >5min {d['over5']:.1%}  worst10%mean {d['tail10_mean']:.2f}\n")
    f.write(f"separate: overtaken by a later arrival {out['separate']['overtaken_frac']:.1%} of customers, avg {out['separate']['overtaken_mean']:.2f} people\n")
    f.write(f"tally of first 1000 trips → {out['tally1000_frac']:.1%}\n")
    f.write(f"P(fastest of 3) {out['p_fastest_3']:.4f}   P(fastest of 5) {out['p_fastest_5']:.4f}   100 trips → won {out['trips_win']}\n")
print(open('data/stats_out.txt').read())
