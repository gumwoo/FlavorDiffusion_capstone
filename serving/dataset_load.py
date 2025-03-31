from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import uvicorn
import io
import json
import os, sys

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def main_page():
    return "This is FlavorDiffusion model API"


current_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(current_dir, "../dataset/input_data.json")

# JSON 파일 로드 (서버 시작 시 한 번만 실행)
with open(dataset_path, "r", encoding="utf-8") as f:
    input_data = json.load(f)

@app.get("/test")
def test_page():
    return "아니 왜 작동을 안해"

# 유저가 검색하지 않은 상태에서 기본적으로 표시하기.
# 휠 내렸을 때 추가적으로 표현 요청청
@app.get("/input_items")
async def get_items(
    start: int = Query(0, alias="start"),
    limit: int = Query(100, alias="limit"),
):
    """ 요청된 start부터 limit 개수만큼 데이터를 반환하는 API (검색 포함) """
    filtered_data = input_data
    
    end = start + limit
    return {"data": filtered_data[start:end], "total": len(filtered_data)}

# 유저가 검색창에 입력했을 때
# preprocessed json 받아서 top 100개 입력하기
@app.get("/input_items/search")
async def get_items_search(
    start: int = Query(0, alias="start"),
    limit: int = Query(100, alias="limit"),
    search: str = Query(None, alias="search")
):
    
    """ 요청된 start부터 limit 개수만큼 데이터를 반환하는 API (검색) """
    filtered_data = [item for item in input_data if search.lower() in item["name"].lower()] if search else input_data

    end = start + limit
    return {"data": filtered_data[start:end], "total": len(filtered_data)}


class FlavorDiffusionModel(BaseModel):
    """
    모델 관련 정보 입력
    """
    dummy: np.ndarray
# Input data를 받아서 model에 전달하고 예측하기
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from src.FlavorDiffusion import FlavorDiffusion
model = BaseModel(FlavorDiffusion)

model_database = None

@app.get("/predict")
async def predict_model(data):
    predicted_data = model(data)    # metapath2Vec으로 할 방법 구현해야함함
    model_database = predicted_data # copy deepcopy 사용 가능
    return predicted_data # predicted data에서 node_edge




# 노드 관련 정보 전달

"""with open(dataset_path, "r", encoding="utf-8") as f: 무언가 노드 관련 정보 """
@app.get("/node_info")
async def node_info(node_id):
    return # 무언가 node_dataset(node_id)


"""with open(dataset_path, "r", encoding="utf-8") as f: 무언가 엣지 관련 정보 """
# Edge 관련 정보 전달
@app.get("/edge_info")
async def edge_info(edge_id):
    return # model에서 predict한 값에서 NMI 받아오기?




# Chatgpt call 모델
# Authentication endpoint

# ChatGPT API Key 입력하는 곳
"""
key_dir = os.path.join(os.path.dirname(sys.executable), "key.txt")
if not os.path.exists(key_dir):
    f = open(key_dir, 'w')
    f.write(str(uuid.uuid4()))
    f.close()
f = open(key_dir, 'r')
key = f.read()
f.close()
"""

@app.get("/gpt_auth")
async def auth():
    return {"dir": key_dir}

class GPTItem(BaseModel):
    prompt: str
    model_path: str
    temperature: float
    top_p: float
    top_k: int
    max_tokens: int
    presence_penalty: float
    frequency_penalty: float
    repeat_penalty: float
    n_ctx: int
    stop: List[str]

app.n_ctx = 2000
app.last_model_path = ""
app.llm:GPT = None

def stream_chat_gpt(item:GPTItem):
    chunks = app.llm.create_completion(
        prompt = item.prompt,
        temperature = item.temperature,
        # top_p = item.top_p,
        # top_k = item.top_k,
        # max_tokens = item.max_tokens,
        # presence_penalty = item.presence_penalty,
        # frequency_penalty = item.frequency_penalty,
        # repeat_penalty = item.repeat_penalty,
        # stop=item.stop,
        stream=False,
    )
    if(type(chunks) == str):
        print(chunks, end="")
        yield chunks
        return
    if(type(chunks) == bytes):
        print(chunks.decode('utf-8'), end="")
        yield chunks.decode('utf-8')
        return
    if(type(chunks) == dict and "choices" in chunks):
        print(chunks["choices"][0]["text"], end="")
        yield chunks["choices"][0]["text"]
        return

    for chunk in chunks:
        if(type(chunk) == str):
            print(chunk, end="")
            yield chunk
            continue
        if(type(chunk) == bytes):
            print(chunk.decode('utf-8'), end="")
            yield chunk.decode('utf-8')
            continue
        cont:CompletionChunk  = chunk
        print(cont)
        encoded = cont["choices"][0]["text"]
        print(encoded, end="")
        yield encoded

@app.post("/gpt_chat")
async def gpt_chat(item:GPTItem, x_auth: Annotated[Union[str, None], Header()] = None) -> StreamingResponse:
    if key != x_auth:
        return {"error": "Invalid key"}
    return StreamingResponse((item))