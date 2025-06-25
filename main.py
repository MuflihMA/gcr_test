import os
import cv2
import shutil
import uvicorn
import tempfile

from ultralytics import YOLO
from typing import Annotated
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, Response

import torch
import logging
import google.cloud.logging

# from log_supressor import suppress_stderr

# with suppress_stderr:
#     import torch


app = FastAPI(title = "Google Cloud Run Testing")

torch.backends.nnpack.enabled = False

client = google.cloud.logging.Client()
client.setup_logging(log_level=logging.DEBUG)

logger = logging.getLogger("video_processing")
logger.setLevel(logging.DEBUG)

log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

cloud_logger = logging.StreamHandler()
cloud_logger.setLevel(logging.DEBUG)
cloud_logger.setFormatter(log_format)

logger.addHandler(cloud_logger)


@app.get("/", response_class=HTMLResponse)
def read_root():
    logger.debug("Requested root endpoint")
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>My Cloud Run App</title>
        </head>
        <body>
            <h1>Selamat Datang di app Google Cloud Run buatan gueeeeh</h1>
            <p>Ini HTML Page simple yang dibuat dengan FastAPI atau semcamnya gatau KMS</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/favicon.ico")
def favicon():
    logger.debug("Requested favicorn")
    return Response(status_code=204)


@app.post("/video_analytics")
async def video_analytics(file: Annotated[UploadFile, File()],
                          background_tasks: BackgroundTasks):
    
    logging.getLogger('ultralytics').setLevel(logging.ERROR)

    logger.debug(f"Starting video processing for file: {file.filename}")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, file.filename)
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        logger.debug(f"Saved uploaded file to: {input_path}")

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            logger.error("Cannot open video file: {input_path}")
            raise ValueError(f"Cannot open video file: {input_path}")

        temp_output_path = os.path.join(tmpdir, "output.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logger.info(f"Video properties: FPS: {fps}, Width: {width}, Height: {height}")

        model = YOLO('model/yolo11n.pt')
        model.fuse()

        out = cv2.VideoWriter(temp_output_path, fourcc, fps, (width, height))

        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1

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

        logger.info(f"Finished processed {frame_count} frames")
        cap.release()
        out.release()

        # final_output_path = os.path.join("outputs", f"processed_{file.filename}")
        final_output_path = os.path.join("/tmp", f"processed_{file.filename}")
        os.makedirs("outputs", exist_ok=True)
        shutil.copy(temp_output_path, final_output_path)

        logger.info(f"Saved processed video to: {final_output_path}")

        background_tasks.add_task(os.remove, final_output_path)

    return FileResponse(final_output_path, media_type="video/mp4", filename="processed_video.mp4")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)