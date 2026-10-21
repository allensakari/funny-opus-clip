"""S005 新能源车 · 可复现统计 → stats.json
全部数字来自公安部网站（公安部交通管理局 / 人民公安报）发布，原文快照在 sources_raw/mps_*.txt（2026-10-11 抓取）。"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
# (时间点, 新能源汽车保有量 万辆, 占汽车总量 %) —— 公安部原文
STOCK = [('2022-06', 1001, 3.23), ('2023-12', 2041, 6.07), ('2024-06', 2472, 7.18), ('2025-06', 3689, 10.27), ('2025-12', 4397, 12.01), ('2026-06', 4897, 13.19)]
# 新注册登记新能源汽车（万辆，占当期新注册登记汽车 %）
NEWREG = {'2019': (120, None), '2023': (743, 30.25), '2025': (1293, 49.38), '2026H1': (519.5, 49.42)}
NEWREG_DERIVED = {'2022': 743 - 207, '2024': 1293 - 168}          # 原文「与2022年相比增加207万辆」「与2024年相比增加168万辆」
SECONDS_PER_YEAR = 365 * 24 * 3600
BEV_SHARE = {'2022-06': 80.93, '2023-12': 76.04, '2024-06': 73.35, '2025-06': 69.23, '2025-12': 68.74, '2026-06': 68.77}   # 纯电动占新能源 %（公安部）
CHARGERS = dict(total_wan=2305.7, public_wan=500.9, private_wan=1804.8, yoy=43.2, date='2026-06')                          # 国家能源局 2026-07-28
IEA = dict(global_ev_sales_2025_mn=20, global_share_2025=25, china_makers_share=60)                                         # IEA GEVO 2026 执行摘要

S = dict(
    stock=STOCK, newreg=NEWREG, newreg_derived=NEWREG_DERIVED,
    stock_now_wan=4897, share_now=13.19, cars_now_yi=3.71,
    one_in=round(100 / 13.19, 1),                               # 路上约每 7.6 辆汽车有 1 辆新能源
    of_8_cars=round(8 * 13.19 / 100, 2),                        # 红灯前 8 辆车 → 约 1.06 辆
    new_share_2026h1=49.42, new_share_2025=49.38,
    sec_per_new_2025=round(SECONDS_PER_YEAR / (1293e4), 2),     # 2025 年平均每多少秒新注册登记一辆
    growth_2019_2025=round(1293 / 120, 1),
    bev_share=BEV_SHARE, chargers=CHARGERS, iea=IEA,
    nev_per_charger=round(4897 / 2305.7, 2),                    # 每个充电枪对应约 2.1 辆新能源车（推算）
    fuel_cars_yi=round(3.71 - 0.4897, 2),                       # 路上其余（非新能源）汽车约 3.22 亿辆
    per_day_2025=round(1293e4 / 365),                           # 2025 年平均每天新上牌
)

if __name__ == '__main__':
    json.dump(S, open(HERE + '/stats.json', 'w'), ensure_ascii=False, indent=1)
    for k, v in S.items(): print(f'{k:20s} {v}')
