# 给网卡 enP8p1s0 设置静态 IP
sudo ifconfig enP8p1s0 192.168.10.100 netmask 255.255.255.0 up


import sys
import gi
import time
import socket
import json
import numpy as np
from ultralytics import YOLO

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

# --- 全局配置 ---
UDP_PORT = 5000
MODEL_PATH = "yolov8n.pt"

# --- [修复点] 必须定义目标 IP 和端口 ---
STM32_IP = "192.168.10.101"  # 请确认这是 STM32 的 IP
ALERT_PORT = 5555            # 报警端口

# --- 初始化 UDP Socket ---
alert_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- 模型加载 ---
print(f"正在加载模型 {MODEL_PATH} ...")
model = YOLO(MODEL_PATH)

# --- GStreamer 初始化 ---
Gst.init(None)

pipeline_str = f"""
    udpsrc port={UDP_PORT} ! 
    application/x-rtp, media=video, clock-rate=90000, encoding-name=JPEG, payload=26 ! 
    rtpjpegdepay ! 
    jpegdec ! 
    videoconvert ! 
    video/x-raw, format=BGR ! 
    appsink name=sink emit-signals=true sync=false max-buffers=1 drop=true
"""

print(f"正在启动接收管道 (Port: {UDP_PORT})...")
pipeline = Gst.parse_launch(pipeline_str)
appsink = pipeline.get_by_name("sink")

def on_new_sample(sink):
    sample = sink.emit("pull-sample")
    if not sample:
        return Gst.FlowReturn.ERROR

    # 获取图像数据
    buffer = sample.get_buffer()
    caps = sample.get_caps()
    h = caps.get_structure(0).get_value("height")
    w = caps.get_structure(0).get_value("width")
    
    success, map_info = buffer.map(Gst.MapFlags.READ)
    if not success:
        return Gst.FlowReturn.ERROR

    # 转换为 Numpy 数组
    img_array = np.ndarray((h, w, 3), buffer=map_info.data, dtype=np.uint8)
    
    # --- 执行推理 ---
    results = model(img_array, verbose=False)
    
    # --- 结果解析 ---
    detection_list = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            # [修复点] 使用 [0] 和 .item() 修复所有 Numpy 警告
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            conf = float(box.conf.item())
            cls = int(box.cls.item())
            label = model.names[cls]
            
            # 危险等级逻辑
            area = (x2 - x1) * (y2 - y1)
            danger_level = 0
            if area > (w * h * 0.15):
                danger_level = 2 # 紧急
            elif area > (w * h * 0.05):
                danger_level = 1 # 警告

            detection_list.append({
                "label": label,
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "conf": round(conf, 2),
                "danger": danger_level
            })

            # 打印到 Jetson 终端
            print(f"检测到: {label} (Conf: {conf:.2f}, Danger: {danger_level})")

    # --- 发送元数据 (UDP) ---
    if len(detection_list) > 0:
        msg = {
            "ts": time.time(),
            "detections": detection_list
        }
        json_str = json.dumps(msg)
        try:
            # 发送给 STM32
            alert_socket.sendto(json_str.encode('utf-8'), (STM32_IP, ALERT_PORT))
        except Exception as e:
            print(f"发送失败: {e}")
    
    buffer.unmap(map_info)
    return Gst.FlowReturn.OK

# 绑定信号
appsink.connect("new-sample", on_new_sample)

# 启动管道
pipeline.set_state(Gst.State.PLAYING)

try:
    loop = GObject.MainLoop()
    loop.run()
except KeyboardInterrupt:
    print("正在停止...")
    pipeline.set_state(Gst.State.NULL)
