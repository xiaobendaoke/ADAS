import socket
import json

# 监听配置
BIND_IP = "0.0.0.0"  # 监听所有来源
PORT = 5555          # 必须与 Jetson 端代码里的 ALERT_PORT 一致

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((BIND_IP, PORT))

print(f"正在监听报警信号 (Port: {PORT})...")

while True:
    try:
        # 接收数据
        data, addr = sock.recvfrom(4096)
        
        # 解析 JSON
        json_str = data.decode('utf-8')
        msg = json.loads(json_str)
        
        detections = msg.get("detections", [])
        
        # 简单的报警逻辑
        max_danger = 0
        for d in detections:
            if d['danger'] > max_danger:
                max_danger = d['danger']
        
        # 打印报警信息
        if max_danger == 2:
            # 红色字体打印紧急报警
            print(f"\033[31m[紧急] ⚠️  注意危险！停止倒车！(检测到 {len(detections)} 个目标)\033[0m")
        elif max_danger == 1:
            # 黄色字体打印警告
            print(f"\033[33m[警告] ⚠️  注意障碍物\033[0m")
        else:
            print(f"[安全] 收到数据，无危险目标")
            
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"错误: {e}")