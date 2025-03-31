import pandas as pd
import json

# CSV 파일 로드

path = input("Input csv file name in dataset folder: ")
path = "../dataset/" + path + ".csv"

csv_file = path
df = pd.read_csv(csv_file)

# NaN 값을 None으로 변환 (JSON에서 null로 표현됨)
df = df.where(pd.notna(df), None)

# JSON 변환 (리스트 형태)
json_data = df.to_dict(orient="records")

# JSON 파일로 저장
json_file = "output.json"
with open(json_file, "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=4, ensure_ascii=False)

print(f"JSON 변환 완료! {json_file} 파일이 생성되었습니다.")
