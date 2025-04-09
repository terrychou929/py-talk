# 🧑‍🤝‍🧑 Anonymous WebSocket Chatroom

This is a simple anonymous chatroom built using **FastAPI** and **WebSocket**. It allows users to chat with each other in real-time through a web interface — no login, no username, just messages. The project is lightweight, self-contained, and easy to deploy locally or in a Dockerized environment.

## 🔧 Technologies Used

- **Python 3.10+**
- **FastAPI** – for serving HTTP and WebSocket endpoints
- **WebSocket** – for real-time communication
- **Uvicorn** – ASGI server for running FastAPI
- **HTML + JavaScript** – simple front-end interface
- **Docker** – for containerized deployment

## 📦 Installation

### Run Locally (Python)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --reload
   http://localhost:8000
   ```
2. Build the Docker image
    ```bash
    docker build -t py-talk .    
    docker run -d -p 8000:8000 py-talk
    http://localhost:8000
    ```
