import cv2
import uvicorn
import ultralytics
from fastapi import FastAPI
from fastapi.responses import Response


app = FastAPI(title = "Google Cloud Run Testing")

@app.get("/")
def read_root():
    return {"message": "Welcome to my google cloud run test apps"}

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port = 8080)