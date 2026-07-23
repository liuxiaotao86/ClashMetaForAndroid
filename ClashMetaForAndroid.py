import os
import csv
import json
from datetime import datetime, timezone, timedelta

# 输入文件（手动维护）
DIRECT_TXT = "DirectApps.txt"
SYSTEM_TXT = "SystemApps.txt"
APP_LIST_CSV = "app-list.csv"

# 生成文件
DB_JSON = "PackageNames.json"
PROXY_TXT = "ProxyApps.txt"

DIRECT_YAML = "DirectApps.yaml"
PROXY_YAML = "ProxyApps.yaml"
SYSTEM_YAML = "SystemApps.yaml"

PREFIX = "  - PROCESS-NAME,"

def get_bj_time_str():
    """获取 UTC+8 (北京时间) 格式化字符串"""
    bj_time = datetime.now(timezone.utc) + timedelta(hours=8)
    return bj_time.strftime("%Y-%m-%d %H:%M:%S")

def clean_and_sort_file(file_path):
    """读取 txt 文件，去重并按包名排序写回，返回清洗后的集合"""
    if not os.path.exists(file_path):
        return set()
    
    with open(file_path, "r", encoding="utf-8") as f:
        pkgs = {line.strip() for line in f if line.strip()}
    
    sorted_pkgs = sorted(list(pkgs))
    
    # 写回去重并排序后的 txt 文件
    with open(file_path, "w", encoding="utf-8") as f:
        for pkg in sorted_pkgs:
            f.write(f"{pkg}\n")
            
    return set(sorted_pkgs)

def update_package_names_db():
    """根据 app-list.csv 更新 PackageNames.json (只增不删，主键为 Package Name)"""
    db = {}
    if os.path.exists(DB_JSON):
        try:
            with open(DB_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    db = data
        except Exception as e:
            print(f"⚠️ 读取现有 {DB_JSON} 异常，将重新建表: {e}")

    csv_app_names = {}
    if os.path.exists(APP_LIST_CSV):
        with open(APP_LIST_CSV, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            app_idx, pkg_idx = 0, 1
            if header:
                for idx, col in enumerate(header):
                    c = col.strip()
                    if c == "App Name":
                        app_idx = idx
                    elif c == "Package Name":
                        pkg_idx = idx
            
            for row in reader:
                if len(row) > max(app_idx, pkg_idx):
                    app_name = row[app_idx].strip()
                    pkg_name = row[pkg_idx].strip()
                    if pkg_name and app_name:
                        # 主键为 Package Name，更新或新增
                        db[pkg_name] = app_name
                        csv_app_names[pkg_name] = app_name

    # 字典按 Key (Package Name) 排序
    sorted_db = dict(sorted(db.items()))

    with open(DB_JSON, "w", encoding="utf-8") as f:
        json.dump(sorted_db, f, ensure_ascii=False, indent=2)

    print(f"✅ [1/4] {DB_JSON} 更新成功，当前映射库总量: {len(sorted_db)} 条")
    return sorted_db, csv_app_names

def generate_yaml(txt_file, yaml_file, app_db, time_str):
    """根据 txt 包名清单和包名映射生成对应的 Clash YAML 规则文件"""
    if not os.path.exists(txt_file):
        print(f"⚠️ 未找到 {txt_file}，跳过生成 {yaml_file}")
        return

    with open(txt_file, "r", encoding="utf-8") as f:
        pkgs = [line.strip() for line in f if line.strip()]

    # 确保生成 YAML 时的规则也是有序的
    sorted_pkgs = sorted(list(dict.fromkeys(pkgs)))

    yaml_lines = [f"payload: # CreatedTime：{time_str}\n"]
    for pkg in sorted_pkgs:
        app_name = app_db.get(pkg, "")
        if app_name:
            yaml_lines.append(f"{PREFIX}{pkg}\t #{app_name}\n")
        else:
            yaml_lines.append(f"{PREFIX}{pkg}\n")

    with open(yaml_file, "w", encoding="utf-8") as f:
        f.writelines(yaml_lines)

    print(f"✅ 生成规则文件: {yaml_file} ({len(sorted_pkgs)} 条规则)")

if __name__ == "__main__":
    time_str = get_bj_time_str()
    print(f"🕒 当前批次处理时间: {time_str}")

    # 步骤 0: 预处理，对 DirectApps.txt 和 SystemApps.txt 原地去重并按包名排序
    direct_pkgs = clean_and_sort_file(DIRECT_TXT)
    system_pkgs = clean_and_sort_file(SYSTEM_TXT)
    print(f"🧹 [0/4] 预处理完成: DirectApps ({len(direct_pkgs)} 条), SystemApps ({len(system_pkgs)} 条)")

    # 步骤 1: 读取 app-list.csv 更新 PackageNames.json
    db, csv_app_pkgs = update_package_names_db()

    # 步骤 2: 生成 DirectApps.yaml
    generate_yaml(DIRECT_TXT, DIRECT_YAML, db, time_str)

    # 步骤 3: 提取 ProxyApps.txt (从 app-list.csv 剔除 SystemApps 和 DirectApps)
    csv_all_pkgs = set(csv_app_pkgs.keys())
    proxy_pkgs = csv_all_pkgs - system_pkgs - direct_pkgs
    sorted_proxy_pkgs = sorted(list(proxy_pkgs))

    # 写回 ProxyApps.txt (保持去重与包名排序)
    with open(PROXY_TXT, "w", encoding="utf-8") as f:
        for pkg in sorted_proxy_pkgs:
            f.write(f"{pkg}\n")
    print(f"🧹 [3/4] 自动筛选生成 {PROXY_TXT} ({len(sorted_proxy_pkgs)} 条)")

    # 生成 ProxyApps.yaml
    generate_yaml(PROXY_TXT, PROXY_YAML, db, time_str)

    # 步骤 4: 生成 SystemApps.yaml
    generate_yaml(SYSTEM_TXT, SYSTEM_YAML, db, time_str)

    print("🎉 所有任务均已顺利完成！")
