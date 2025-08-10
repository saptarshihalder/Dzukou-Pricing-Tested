import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime
from pathlib import Path

# Utility functions

def csv_load(url: str) -> pd.DataFrame:
    return pd.read_csv(url, encoding='latin1')

# FX rates using open API

def currency_convert(amount: float, from_cur: str, to_cur: str, date: str | None = None) -> float:
    if from_cur == to_cur:
        return amount
    # Use open er-api for latest rates
    resp = requests.get(f"https://open.er-api.com/v6/latest/{from_cur}")
    data = resp.json()
    rate = data['rates'][to_cur]
    return amount * rate

# Competitor price simulator

COMPETITORS = [
    "Amazon",
    "Walmart",
    "Target",
    "BestBuy",
    "eBay",
]


def simulate_competitors(row):
    base_price = row['current_price']
    rng = np.random.default_rng(hash(row['item_id']) % 2**32)
    comps = []
    for comp in COMPETITORS:
        price = float(base_price) * rng.uniform(0.8, 1.2)
        comps.append({
            'source': comp,
            'url': 'https://example.com',
            'matched_title': row['item_name'],
            'match_score': round(rng.uniform(0.8, 0.99), 2),
            'effective_price': round(price, 2),
            'currency': 'USD',
            'stock': 'in_stock'
        })
    return comps


# Demand model using constant elasticity
DEFAULT_ELASTICITY = -1.5
BASE_DEMAND = 100


def expected_demand(price: float, current_price: float, elasticity: float = DEFAULT_ELASTICITY) -> float:
    return BASE_DEMAND * (price / current_price) ** elasticity


# Price optimization

def optimize_price(row, competitors):
    min_comp_price = min(c['effective_price'] for c in competitors)
    cogs = row['unit_cost']
    cur_price = row['current_price']

    # price grid: from margin floor 5% above cogs to 120% of min competitor
    lower = max(cogs * 1.05, 0.5 * cur_price)
    upper = min(min_comp_price * 1.2, cur_price * 1.5)
    prices = np.linspace(lower, upper, 50)

    best = {'price': cur_price, 'profit': -np.inf, 'units': 0}
    for p in prices:
        units = expected_demand(p, cur_price)
        profit = (p - cogs) * units
        if profit > best['profit']:
            best.update({'price': p, 'profit': profit, 'units': units})

    # psychological pricing
    best['price'] = round(np.floor(best['price']) + 0.99, 2)
    best['profit'] = round(best['profit'], 2)
    best['units'] = round(best['units'], 2)
    return best


def main():
    url = "https://github.com/saptarshihalder/dzukou-dynamic-pricing-LLM/raw/refs/heads/main/Dzukou_Pricing_Overview_With_Names%20-%20Copy.csv"
    df = csv_load(url)
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    df.rename(columns={'product_id': 'item_id', 'product_name': 'item_name', 'current_price': 'current_price', 'unit_cost': 'unit_cost'}, inplace=True)
    # clean numeric fields removing stray characters
    for col in ['current_price', 'unit_cost']:
        df[col] = df[col].astype(str).str.replace(r'[^0-9\\.]', '', regex=True)
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['currency'] = 'USD'

    results = []
    comp_snapshot = {}

    for _, row in df.iterrows():
        competitors = simulate_competitors(row)
        best = optimize_price(row, competitors)
        profit_current = (row['current_price'] - row['unit_cost']) * expected_demand(row['current_price'], row['current_price'])
        profit_uplift = (best['profit'] - profit_current) / profit_current * 100 if profit_current else 0
        demand_uplift = (best['units'] - BASE_DEMAND) / BASE_DEMAND * 100

        results.append({
            'item_id': row['item_id'],
            'item_name': row['item_name'],
            'current_price': round(row['current_price'], 2),
            'recommended_price': round(best['price'], 2),
            'currency': row['currency'],
            'expected_units': best['units'],
            'expected_profit': best['profit'],
            'profit_uplift_vs_current_%': round(profit_uplift, 2),
            'demand_lift_vs_current_%': round(demand_uplift, 2),
            'competitor_summary': competitors,
            'rationale': f"Price optimized against min competitor {min(c['effective_price'] for c in competitors):.2f}",
            'confidence': 'low',
            'flags': []
        })

        comp_snapshot[row['item_id']] = competitors

    # Outputs
    today = datetime.utcnow().date().isoformat()
    data_dir = Path('data'); data_dir.mkdir(exist_ok=True)
    report_dir = Path('reports'); report_dir.mkdir(exist_ok=True)

    json_path = data_dir / f"competitor_prices_{today}.json"
    with open(json_path, 'w') as f:
        json.dump(comp_snapshot, f, indent=2)

    df_out = pd.DataFrame(results)
    csv_path = data_dir / f"pricing_recommendations_{today}.csv"
    df_out.to_csv(csv_path, index=False)
    json_rec_path = data_dir / f"pricing_recommendations_{today}.json"
    with open(json_rec_path, 'w') as f:
        json.dump(results, f, indent=2)

    # Markdown report
    md_path = Path('reports/pricing_report.md')
    total_profit_uplift = df_out['profit_uplift_vs_current_%'].mean()
    inc = (df_out['recommended_price'] > df_out['current_price']).sum()
    dec = (df_out['recommended_price'] <= df_out['current_price']).sum()
    with open(md_path, 'w') as f:
        f.write(f"# Pricing Report {today}\n\n")
        f.write(f"Average profit uplift: {total_profit_uplift:.2f}%\n\n")
        f.write(f"Price increases: {inc}, decreases: {dec}\n\n")
        f.write("## Items\n")
        for r in results:
            f.write(f"- **{r['item_name']}** ({r['item_id']}): recommend {r['recommended_price']}, expected profit {r['expected_profit']:.2f}\n")

    print("Saved:", json_path, csv_path, md_path)

if __name__ == '__main__':
    main()
