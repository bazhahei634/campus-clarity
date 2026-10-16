from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import json
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class NoticeRequest(BaseModel):
    text: str
    role: str

@app.post("/api/translate")
async def translate_notice(data: NoticeRequest):
    # ⚠️⚠️⚠️ 在这里填入你真实的 DeepSeek API Key ⚠️⚠️⚠️
import os
API_KEY = os.getenv("DEEPSEEK_API_KEY")

    prompt = f"""你是校园通知翻译器，用户身份是：{data.role}。
请解析下面的通知，严格输出 JSON 格式（不要任何其他解释文字）。

判断规则：
1. 只有当通知里**明确写了**"做什么、截止时间、交给谁、准备什么材料"时，才填写对应字段。
2. 如果没有写明，对应字段填 **空字符串 ""**，不要填"未明确"或"无"，也不要自己编造。
3. 特别注意：截止时间如果写的是"近期""下周"等模糊词，填成"近期（未明确具体日期）"。

JSON 格式：
{{
  "task": "要做的具体动作，没有则填空字符串",
  "deadline": "截止时间（如'10月20日 17:00'），没有则填空字符串",
  "submit_to": "交给谁，没有则填空字符串",
  "materials": ["需要准备的材料，没有则填空数组 []"],
  "subtext": "潜台词，没有则填空字符串",
  "personal_action": "针对该身份的行动建议，没有则填空字符串"
}}
通知原文：
{data.text}
"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            },
            timeout=30.0
        )
    
    if response.status_code != 200:
        return {"error": "API Key 无效或余额不足", "detail": response.text}
    
    result = response.json()
    content = json.loads(result["choices"][0]["message"]["content"])
    return content

app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)