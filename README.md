# 智能驾驶辅助系统（ADAS）- Jetson 与 STM32

该项目实现了一个基于 **Jetson** 的智能驾驶辅助系统（ADAS），用于视频流处理和目标检测。该系统使用 **Jetson** 执行 AI 推理（基于 YOLOv8 模型），并使用 **STM32** 负责视频采集、数据传输和警报处理。

## 项目概述

该系统使用以下组件：
- **Jetson**：接收来自 STM32 的视频流，使用 YOLOv8 模型执行对象检测，并将检测结果返回给 STM32。
- **STM32**：负责从摄像头捕获视频，发送视频数据到 Jetson 进行处理。接收 Jetson 传回的检测结果，并根据检测到的目标触发警报。

## 文件说明

### 1. **`adas_inference_mjpeg.py`**
- **环境**：Jetson
- **描述**：该脚本在 Jetson 上执行，接收来自 STM32 的视频帧，使用 YOLOv8 模型进行目标检测，并将检测结果发送回 STM32。
- **依赖**：
  - GStreamer
  - YOLOv8（Ultralytics）
  - OpenCV
- **关键功能**：
  - 通过 UDP 接收 MJPEG 视频流。
  - 使用 YOLOv8 模型进行推理。
  - 将检测结果发送到 STM32 进行后续处理。

### 2. **`alarm_receiver.py`**
- **环境**：STM32
- **描述**：该脚本在 STM32 上执行，监听来自 Jetson 的报警信号（检测结果），并根据检测到的目标触发警报。
- **依赖**：
  - Python
- **关键功能**：
  - 监听端口 5555 上的 UDP 数据包。
  - 解析 JSON 格式的检测结果并评估危险等级。
  - 根据检测到的目标，打印报警信息或触发报警。

### 3. **`start_mjpeg_stream.sh`**
- **环境**：STM32
- **描述**：该脚本用于配置 STM32 捕获视频流，进行 MJPEG 编码，并通过 UDP 将视频流传输到 Jetson 进行处理。
- **依赖**：
  - GStreamer
- **关键功能**：
  - 捕获摄像头视频并进行 MJPEG 编码。
  - 通过 UDP 将视频流传输给 Jetson 进行目标检测。

## 使用说明

### 1. **Jetson 设置（ADAS 推理）**

要运行 Jetson 端的系统，请按照以下步骤操作：

1. 安装所需的依赖：
   ```bash
   sudo apt update
   sudo apt install python3-pip
   pip3 install ultralytics opencv-python gstreamer
````

2. 将 `adas_inference_mjpeg.py` 放到 Jetson 上，确保脚本中的 STM32 IP 地址设置正确：

   ```python
   STM32_IP = "192.168.10.101"  # 替换为 STM32 的 IP 地址
   ```

3. 运行推理脚本：

   ```bash
   python3 adas_inference_mjpeg.py
   ```

### 2. **STM32 设置（视频捕获与报警接收）**

#### a. **启动视频流**

1. 在 STM32 上安装必要的依赖（如果尚未安装）：

   ```bash
   sudo apt update
   sudo apt install gstreamer
   ```

2. 配置 STM32 的 IP 地址，确保与 Jetson 在同一网络中，可以使用 `ifconfig` 或 `ip` 命令进行配置。

3. 运行视频流脚本：

   ```bash
   ./start_mjpeg_stream.sh
   ```

#### b. **启动报警接收**

1. 在 STM32 上运行报警接收脚本，监听来自 Jetson 的报警信息：

   ```bash
   python3 alarm_receiver.py
   ```

2. 脚本将根据检测到的目标输出报警信息，并触发相应的警报。

## 故障排除

* **Jetson 没有接收到视频**：

  * 确保 STM32 正在正确发送 MJPEG 视频流，并且网络连接正常。
  * 使用工具如 `tcpdump` 或 `netstat` 验证 UDP 包是否正在传输。

* **检测结果没有显示**：

  * 确保 YOLO 模型已正确加载，并且 GStreamer 管道能够正确处理视频。
  * 检查控制台日志中的错误信息，找出依赖项或网络配置的潜在问题。



