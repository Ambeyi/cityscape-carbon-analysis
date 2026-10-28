"""Summarize recorded carbon footprints by transport mode."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MODE = 'Mode_of_Transport'
VALUE = 'Carbon_Footprint_kgCO2'

def summarize(frame):
    if not {MODE, VALUE}.issubset(frame.columns):
        raise ValueError('Missing required transport or footprint column')
    d = frame[[MODE, VALUE]].copy()
    d[VALUE] = pd.to_numeric(d[VALUE], errors='raise')
    present = d[VALUE].dropna()
    if not (np.isfinite(present) & (present >= 0)).all():
        raise ValueError('Footprints must be finite and nonnegative')
    d[MODE] = d[MODE].astype('string').str.strip().replace('', pd.NA)
    d = d.dropna()
    if d.empty:
        raise ValueError('No complete observations')
    rows = []
    for mode, group in d.groupby(MODE, sort=True):
        v = group[VALUE]
        n = len(v)
        sd = float(v.std(ddof=1)) if n > 1 else np.nan
        half = stats.t.ppf(.975, n-1)*sd/np.sqrt(n) if n > 1 else np.nan
        rows.append({'transport_mode':mode,'n':n,'mean':v.mean(),'median':v.median(),
                     'sd':sd,'ci95_lower':v.mean()-half,'ci95_upper':v.mean()+half})
    return d, pd.DataFrame(rows)

def run(frame, output):
    d, summary = summarize(frame)
    out = Path(output); out.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out/'transport_summary.csv', index=False)
    groups = [g[VALUE].to_numpy() for _, g in d.groupby(MODE, sort=True)]
    report = {'input_rows':len(frame),'complete_rows':len(d),'excluded_rows':len(frame)-len(d),
              'transport_modes':len(groups),'overall_mean':float(d[VALUE].mean())}
    # Inferential tests require replicated, nonconstant groups.
    if len(groups)>1 and all(len(g)>1 and np.var(g)>0 for g in groups):
        f,p = stats.f_oneway(*groups)
        w,q = stats.levene(*groups, center='median')
        report['anova'] = {'F':float(f),'p_value':float(p)}
        report['median_centered_levene'] = {'statistic':float(w),'p_value':float(q)}
    (out/'analysis.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    fig,ax = plt.subplots(figsize=(8,5))
    ax.boxplot(groups, tick_labels=summary.transport_mode.tolist())
    ax.set(title='Recorded carbon footprint by transport mode',ylabel='Carbon footprint (kg CO2)',xlabel='Transport mode')
    ax.spines[['top','right']].set_visible(False)
    fig.tight_layout(); fig.savefig(out/'transport_comparison.svg'); plt.close(fig)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input'); p.add_argument('--output',default='results')
    a=p.parse_args(); print(json.dumps(run(pd.read_csv(a.input),a.output),indent=2))
