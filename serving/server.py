from fastapi import FastAPI, UploadFile, File
import pandas as pd
import numpy as np
import joblib
import uvicorn
import io

app = FastAPI()

# ML 모델 로드 (예제)
model = joblib.load("model.pth")  # 학습된 모델 로드

# CSV 데이터 전처리 함수
def preprocess_csv(file: UploadFile) -> np.ndarray:
    try:
        # CSV 파일을 판다스로 변환
        df = pd.read_csv(io.StringIO(file.file.read().decode("utf-8")))

        # 예제: 필요한 열만 선택하거나 정규화 수행 가능
        processed_data = df.to_numpy() / 10.0  # 예제: 간단한 정규화

        return processed_data

    except Exception as e:
        raise ValueError(f"CSV 파일 처리 오류: {str(e)}")

# 예측 후 결과 가공 함수
def postprocess_result(result: np.ndarray) -> list:
    return [{"prediction": float(pred) * 100} for pred in result]

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    try:
        # 1️⃣ CSV 데이터 전처리
        processed_input = preprocess_csv(file)

        # 2️⃣ 모델 예측 수행
        prediction = model.predict(processed_input)

        # 3️⃣ 후처리 및 응답 반환
        output = postprocess_result(prediction)
        return {"predictions": output}

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
