import os
import cv2
import shutil
import uvicorn
import tempfile
from ultralytics import YOLO
from typing import Annotated
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, Response

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

@app.post("/video_analytics")
async def video_analytics(file: Annotated[UploadFile, File()],
                          background_tasks: BackgroundTasks):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, file.filename)
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {input_path}")

        temp_output_path = os.path.join(tmpdir, "output.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        model = YOLO('model/yolo11n.pt')
        model.fuse()

        out = cv2.VideoWriter(temp_output_path, fourcc, fps, (width, height))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = model.track(frame, tracker="bytetrack.yaml", persist=True)
            if results[0].boxes:
                for box in results[0].boxes:
                    if not hasattr(box, 'id') or box.id is None:
                        continue
                    track_id = int(box.id.item())
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    class_id = int(box.cls.item())
                    class_name = model.names[class_id]

                    color = (0, 255, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    label = f"{class_name} ID: {track_id}"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            out.write(frame)

        cap.release()
        out.release()

        final_output_path = os.path.join("outputs", f"processed_{file.filename}")
        os.makedirs("outputs", exist_ok=True)
        shutil.copy(temp_output_path, final_output_path)

        background_tasks.add_task(os.remove, final_output_path)

    return FileResponse(final_output_path, media_type="video/mp4", filename="processed_video.mp4")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)