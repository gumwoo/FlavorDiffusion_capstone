import pandas as pd
import numpy as np
import math

# =====================================================
# 1) 기존 CSV 불러오기
# =====================================================
df_nodes = pd.read_csv("nodes_191120.csv")  # node_id, name, id, node_type, is_hub
df_edges = pd.read_csv("edges_191120.csv")  # id_1, id_2, score, edge_type

# -----------------------------------------------------
# (노드 ID 중 최대값 찾기 → 새 노드에 부여할 때 사용)
# -----------------------------------------------------
if len(df_nodes) == 0:
    current_max_node_id = 0
else:
    # node_id 컬럼을 정수 변환 (에러 방지)
    df_nodes["node_id"] = pd.to_numeric(df_nodes["node_id"], errors="coerce")
    current_max_node_id = df_nodes["node_id"].max()
    if pd.isna(current_max_node_id):
        current_max_node_id = 0
    else:
        current_max_node_id = int(current_max_node_id)

# =====================================================
# 2) "향기성분 프로파일" 엑셀 읽기
#    - 0,1행이 비어있고 2,3행이 컬럼(헤더)
#    - header=[2, 3] → MultiIndex
# =====================================================
df_profile = pd.read_excel("향기성분 프로파일_v250319.xlsx", header=[2, 3])

# -----------------------------------------------------
# MultiIndex → 단일 문자열 컬럼
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

# =====================================================
# (A) 컬럼명에서 "i.d3)"를 "i.d"로 바꾸기
#     예: "i.d3)" → "i.d"
# (B) 중복된 "i.d3)" 컬럼이 2개라면 1개만 남기고 제거
# (C) 스페이스(' ')를 언더바('_')로 치환
# =====================================================

### (A) & (B) 먼저 처리 ###
# 1) 만약 "i.d3)"라는 컬럼명이 2개 이상이면 → 하나만 남기고 나머지는 드롭
#    (혹은 "i.d3)"가 2개 이상인지 체크 후 drop_duplicates)
df_profile = df_profile.loc[:, ~df_profile.columns.duplicated()]  # 중복 칼럼 제거

# 2) "i.d3)"를 "i.d"로 rename
df_profile.rename(columns=lambda x: x.replace("i.d3)", "i.d"), inplace=True)

### (C) 스페이스 → 언더바 치환 ###
df_profile.columns = [col.replace(" ", "_") for col in df_profile.columns]

# =====================================================
# 최종 컬럼 확인
# =====================================================
print("=== After reading Excel ===")
print("Columns:", df_profile.columns.tolist())
print(df_profile.head(3))

# =====================================================
# 3) 어떤 컬럼이 compound, 어떤 컬럼이 술(ingredient)인지 식별
# =====================================================
compound_col = "Compound_name"  # 이제 "Compound name" → "Compound_name" (공백→언더바)
#   만약 실제 결과에서 'Compound_name'이 아니라 다른 형태면 print(...) 결과를 보고 맞추세요.

beverage_cols = [c for c in df_profile.columns if c.startswith("Concentration2)_")]

# =====================================================
# 4) 빠른 look-up 위해 노드 정보 딕셔너리화
#    key=(name, is_hub) → value=node_id
# =====================================================
node_map = {}
for idx, row in df_nodes.iterrows():
    n_id = row["node_id"]
    n_name = str(row["name"]).strip()
    n_hub = str(row["is_hub"]).strip()
    key = (n_name, n_hub)
    node_map[key] = n_id

# =====================================================
# 함수: 노드 생성
# =====================================================
def create_node(name, node_type, is_hub, ext_id=None):
    global current_max_node_id
    current_max_node_id += 1
    new_node_id = current_max_node_id
    
    df_nodes.loc[len(df_nodes)] = {
        "node_id": new_node_id,
        "name": name,
        "id": ext_id if ext_id else np.nan,  # food/drug가 아니면 NaN
        "node_type": node_type,
        "is_hub": is_hub
    }
    node_map[(name, is_hub)] = new_node_id
    return new_node_id

# =====================================================
# 5) "술(ingredient)" 노드 생성/확인
# =====================================================
beverage_name_to_id = {}

for col in beverage_cols:
    # 예: "Concentration2)_도원결의_(40%)"
    #     (공백→언더바 때문에)
    if "_" in col:
        # split("_", 1) → top="Concentration2)", bev_name_raw="도원결의_(40%)"
        _, bev_name_raw = col.split("_", 1)
    else:
        bev_name_raw = col
    bev_name = bev_name_raw.strip()

    key = (bev_name, "no_hub")
    if key in node_map:
        bev_id = node_map[key]
    else:
        bev_id = create_node(
            name=bev_name,
            node_type="ingredient",
            is_hub="no_hub",
            ext_id=None
        )
    beverage_name_to_id[bev_name] = bev_id

# =====================================================
# 6) 화합물 + 엣지 생성
# =====================================================
new_edges = []

def edge_exists(id1, id2, edge_type):
    cond = (
        ((df_edges["id_1"] == id1) & (df_edges["id_2"] == id2) & (df_edges["edge_type"] == edge_type))
        | ((df_edges["id_1"] == id2) & (df_edges["id_2"] == id1) & (df_edges["edge_type"] == edge_type))
    )
    return cond.any()

for i, row in df_profile.iterrows():
    # Compound_name 컬럼에서 화합물 이름
    if compound_col not in row or pd.isna(row[compound_col]):
        continue
    comp_raw = str(row[compound_col]).strip()
    if not comp_raw:
        continue
    
    # compound 노드
    key_c = (comp_raw, "food")
    if key_c in node_map:
        comp_id = node_map[key_c]
    else:
        comp_id = create_node(
            name=comp_raw,
            node_type="food-compound",
            is_hub="food",
            ext_id=None
        )
    
    # 술(ingredient)들과 연결
    for col in beverage_cols:
        val = row[col]
        if pd.notna(val):
            if "_" in col:
                _, bev_name_raw = col.split("_", 1)
            else:
                bev_name_raw = col
            bev_name = bev_name_raw.strip()

            ingr_id = beverage_name_to_id[bev_name]
            
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
