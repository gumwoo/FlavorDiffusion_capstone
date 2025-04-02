import pandas as pd
import numpy as np
import math
import re

# =====================================================
# 0) 전처리(정규화) 함수
#    - 전부 소문자로
#    - 공백(여러 개) → 언더바
#    - (이미 α, β, γ 등이 들어있으면 그대로 둠)
# =====================================================
def normalize_string(original: str) -> str:
    # 1) 소문자로
    s = original.lower()
    # 2) 공백(\s+) → 언더바(_)
    s = re.sub(r"\s+", "_", s.strip())
    return s

# =====================================================
# 1) 기존 CSV 불러오기
#    (nodes_191120.csv, edges_191120.csv)
# =====================================================
df_nodes = pd.read_csv("nodes_updated.csv")  
df_edges = pd.read_csv("edges_updated.csv")

# -----------------------------------------------------
# (노드 ID 중 최대값 찾기)
# -----------------------------------------------------
if len(df_nodes) == 0:
    current_max_node_id = 0
else:
    df_nodes["node_id"] = pd.to_numeric(df_nodes["node_id"], errors="coerce")
    current_max_node_id = df_nodes["node_id"].max()
    if pd.isna(current_max_node_id):
        current_max_node_id = 0
    else:
        current_max_node_id = int(current_max_node_id)

# -----------------------------------------------------
# (원본 이름 보관용 'original_name' 컬럼이 없으면 추가)
# -----------------------------------------------------
if "original_name" not in df_nodes.columns:
    df_nodes["original_name"] = np.nan

# =====================================================
# 2) "향기성분 프로파일" 엑셀 읽기
#    - 0,1행 비어 있고, 2,3행이 헤더 → header=[2,3]
# =====================================================
df_profile = pd.read_excel("향기성분 프로파일_v250319.xlsx", header=[2, 3])

# -----------------------------------------------------
# MultiIndex → 단일 컬럼
# -----------------------------------------------------
new_cols = []
for top, bottom in df_profile.columns:
    top = str(top).strip() if pd.notna(top) else ""
    bottom = str(bottom).strip() if pd.notna(bottom) else ""
    if ("Unnamed" in bottom) or (bottom == ""):
        new_cols.append(top)
    else:
        new_cols.append(f"{top}_{bottom}")

df_profile.columns = new_cols

# -----------------------------------------------------
# i.d3) → i.d 로 rename, 중복 컬럼 제거, 공백 → 언더바
# -----------------------------------------------------
df_profile = df_profile.loc[:, ~df_profile.columns.duplicated()]  # 중복 컬럼 제거
df_profile.rename(columns=lambda x: x.replace("i.d3)", "i.d"), inplace=True)
df_profile.columns = [col.replace(" ", "_") for col in df_profile.columns]

print("=== After reading Excel ===")
print("Columns:", df_profile.columns.tolist())
print(df_profile.head(3))

# =====================================================
# 3) 컬럼 식별(화합물/술)
# =====================================================
compound_col = "Compound_name"  
beverage_cols = [c for c in df_profile.columns if c.startswith("Concentration2)_")]

# =====================================================
# 4) node_map: (정규화된 name, is_hub) → node_id
# =====================================================
node_map = {}
for idx, row in df_nodes.iterrows():
    n_id = row["node_id"]
    stored_name = str(row["name"]).strip()  # 이미 전처리된 상태일 수도
    stored_hub = str(row["is_hub"]).strip()
    node_map[(stored_name, stored_hub)] = n_id

# =====================================================
# 노드 생성 함수
# =====================================================
def create_node(original_text, node_type, is_hub, ext_id=None):
    global current_max_node_id

    # 1) 원본 그대로
    orig = original_text.strip()
    # 2) 전처리(소문자 + 공백→언더바)
    norm = normalize_string(orig)

    current_max_node_id += 1
    new_id = current_max_node_id

    df_nodes.loc[len(df_nodes)] = {
        "node_id": new_id,
        "name": norm,           # 전처리 결과
        "original_name": orig,  # 원본
        "id": ext_id if ext_id else np.nan,
        "node_type": node_type,
        "is_hub": is_hub
    }

    node_map[(norm, is_hub)] = new_id
    return new_id

# =====================================================
# 5) 술(ingredient) 노드 생성
# =====================================================
beverage_name_to_id = {}

for col in beverage_cols:
    if "_" in col:
        _, bev_name_raw = col.split("_", 1)
    else:
        bev_name_raw = col

    original_bev_name = bev_name_raw.strip()
    norm_bev_name = normalize_string(original_bev_name)

    key = (norm_bev_name, "no_hub")
    if key in node_map:
        bev_id = node_map[key]
    else:
        bev_id = create_node(
            original_text=original_bev_name,
            node_type="ingredient",
            is_hub="no_hub",
            ext_id=None
        )
    beverage_name_to_id[norm_bev_name] = bev_id

# =====================================================
# 6) 화합물(compound) + 엣지
# =====================================================
new_edges = []

def edge_exists(id1, id2, edge_type):
    cond = (
        ((df_edges["id_1"] == id1) & (df_edges["id_2"] == id2) & (df_edges["edge_type"] == edge_type))
        | ((df_edges["id_1"] == id2) & (df_edges["id_2"] == id1) & (df_edges["edge_type"] == edge_type))
    )
    return cond.any()

for i, row in df_profile.iterrows():
    if compound_col not in row or pd.isna(row[compound_col]):
        continue
    
    comp_raw = str(row[compound_col]).strip()
    if not comp_raw:
        continue

    norm_comp = normalize_string(comp_raw)
    ckey = (norm_comp, "food")

    if ckey in node_map:
        comp_id = node_map[ckey]
    else:
        comp_id = create_node(
            original_text=comp_raw,
            node_type="food-compound",
            is_hub="food",
            ext_id=None
        )

    # NaN이 아닌 술 열과 연결
    for col in beverage_cols:
        val = row[col]
        if pd.notna(val):
            if "_" in col:
                _, bev_name_raw = col.split("_", 1)
            else:
                bev_name_raw = col
            
            original_bev_name = bev_name_raw.strip()
            norm_bev_name = normalize_string(original_bev_name)

            ingr_id = beverage_name_to_id.get(norm_bev_name)
            if ingr_id is None:
                ingr_id = create_node(original_bev_name, "ingredient", "no_hub")
                beverage_name_to_id[norm_bev_name] = ingr_id

            if not edge_exists(ingr_id, comp_id, "ingr-fcomp"):
                new_edges.append({
                    "id_1": ingr_id,
                    "id_2": comp_id,
                    "score": np.nan,
                    "edge_type": "ingr-fcomp"
                })

# =====================================================
# 7) 새 엣지를 df_edges에 합치고 중복 제거
# =====================================================
df_new_edges = pd.DataFrame(new_edges)
if len(df_new_edges) > 0:
    df_edges = pd.concat([df_edges, df_new_edges], ignore_index=True)

df_edges.drop_duplicates(subset=["id_1", "id_2", "edge_type"], keep="first", inplace=True)

# =====================================================
# 8) CSV 저장
# =====================================================
df_nodes.to_csv("nodes_updated.csv", index=False, encoding="utf-8")
df_edges.to_csv("edges_updated.csv", index=False, encoding="utf-8")

print("=== Done ===")
print(f"새로 추가된 엣지 수: {len(df_new_edges)}")
print("nodes_updated.csv, edges_updated.csv 파일이 생성되었습니다.")
