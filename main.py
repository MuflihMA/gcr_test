# import cv2
import os
import uvicorn
# import tempfile
# import ultralytics
from fastapi import FastAPI
from fastapi.responses import Response, HTMLResponse

app = FastAPI(title = "Google Cloud Run Testing")

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>My Cloud Run App</title>
        </head>
        <body>
            <h1>Welcome to my Google Cloud Run test app</h1>
            <p>This is a simple HTML page served by FastAPI.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)