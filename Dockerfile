# 使用官方 Python 基底映像
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 複製必要檔案
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 開放容器內的 8000 port
EXPOSE 8000

# 啟動應用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
