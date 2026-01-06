#!/bin/sh

# 1. 定义开关桌面的函数 (完全照搬您的脚本)
start_ui() { systemctl start systemui 2>/dev/null; }
stop_ui()  { systemctl stop  systemui 2>/dev/null; }

# 2. 无论脚本怎么退出，最后都把桌面恢复回来 (照搬您的脚本)
trap 'start_ui; exit 0' INT TERM
trap 'start_ui' EXIT

# 3. 关掉桌面，腾出屏幕
echo "正在关闭桌面环境，接管屏幕..."
stop_ui
sleep 1  # 等一秒让屏幕释放

# 4. 配置推流参数
HOST_IP=192.168.10.100
PORT=5000

echo "正在启动：网络推流(192.168.10.100) + 本地屏幕直显..."

# 5. 启动 GStreamer
# 注意：这里我们使用 linuxfbdevsink，因为桌面关了，fb0 就归我们管了
# 必须加上 videoconvert，因为 framebuffer 可能只吃特定格式(如RGB16)
gst-launch-1.0 -v \
    v4l2src device=/dev/video1 ! \
    image/jpeg,width=640,height=480,framerate=30/1 ! \
    tee name=t \
    \
    t. ! queue ! \
    rtpjpegpay ! \
    udpsink host=$HOST_IP port=$PORT sync=false \
    \
    t. ! queue max-size-buffers=1 leaky=downstream ! \
    jpegdec ! \
    videoconvert ! \
    fbdevsink sync=false
