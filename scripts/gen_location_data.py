#!/usr/bin/env python3
"""
从和风天气官方 CSV 生成省→市→区三级级联 JSON 数据

数据来源: https://github.com/qwd/LocationList
用法: python3 scripts/gen_location_data.py
输出: data/qweather_china.json
"""
import csv
import json
import urllib.request
import sys
from pathlib import Path

CSV_URL = "https://raw.githubusercontent.com/qwd/LocationList/refs/heads/master/China-City-List-latest.csv"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "qweather_china.json"


def download_csv():
    print(f"下载 {CSV_URL} ...")
    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "Umi-Float/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    return raw


def parse_csv(csv_text):
    provinces = {}
    lines = csv_text.splitlines()
    if not lines:
        print("错误: CSV 为空")
        sys.exit(1)

    header_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("Location_ID,"):
            header_idx = i
            break

    if header_idx < 0:
        print("错误: 未找到 CSV 表头")
        sys.exit(1)

    reader = csv.DictReader(lines[header_idx:])
    count = 0
    for row in reader:
        loc_id = row.get("Location_ID", "").strip()
        loc_name = row.get("Location_Name_ZH", "").strip()
        adm1 = row.get("Adm1_Name_ZH", "").strip()
        adm2 = row.get("Adm2_Name_ZH", "").strip()
        country = row.get("Country_Region_ZH", "").strip()

        if country != "中国" or not loc_id or not adm1:
            continue

        if adm1 not in provinces:
            provinces[adm1] = {}
        if adm2 not in provinces[adm1]:
            provinces[adm1][adm2] = []
        provinces[adm1][adm2].append({"name": loc_name, "id": loc_id})
        count += 1

    print(f"解析完成: {len(provinces)} 省, {count} 地区")
    return provinces


def build_json(provinces):
    result = []
    for prov_name in sorted(provinces.keys()):
        cities = []
        for city_name in sorted(provinces[prov_name].keys()):
            districts = provinces[prov_name][city_name]
            cities.append({"name": city_name, "districts": districts})
        result.append({"name": prov_name, "cities": cities})
    return result


def main():
    csv_text = download_csv()
    provinces = parse_csv(csv_text)
    data = build_json(provinces)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = OUTPUT.stat().st_size / 1024
    print(f"已生成: {OUTPUT} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
