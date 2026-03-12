#!/bin/bash
# [已弃用] Ollama GPU 使用情况检查脚本
# GPU 检查已改用 Python 实现（utils/gpu_check.py），跨平台通用。
# 本脚本保留供日后 debug 参考。

echo "=========================================="
echo "Ollama GPU 使用情况检查"
echo "=========================================="
echo ""

# 1. 检查容器 GPU 配置
echo "1. 检查容器 GPU 配置..."
echo "----------------------------------------"
sudo docker inspect ollama | grep -A 5 "DeviceRequests" | head -10
echo ""

# 2. 检查环境变量
echo "2. 检查 NVIDIA 环境变量..."
echo "----------------------------------------"
sudo docker inspect ollama | grep -i "NVIDIA_VISIBLE_DEVICES\|NVIDIA_DRIVER" | head -5
echo ""

# 3. 检查 GPU 识别日志
echo "3. 检查 GPU 识别日志..."
echo "----------------------------------------"
sudo docker logs ollama 2>&1 | grep -i "inference compute" | tail -3
echo ""

# 4. 检查模型加载时的 backend
echo "4. 检查模型加载时的 backend..."
echo "----------------------------------------"
sudo docker logs ollama 2>&1 | grep -i "load_backend" | tail -5
echo ""

# 5. 检查层卸载信息
echo "5. 检查层卸载到 GPU 的情况..."
echo "----------------------------------------"
sudo docker logs ollama 2>&1 | grep -i "offload" | tail -5
echo ""

# 6. 检查设备使用情况
echo "6. 检查设备使用情况（CPU vs GPU）..."
echo "----------------------------------------"
sudo docker logs ollama 2>&1 | grep -i "device=" | tail -5
echo ""

# 7. 检查最新的模型加载日志
echo "7. 最新的模型加载相关信息..."
echo "----------------------------------------"
sudo docker logs ollama 2>&1 | tail -100 | grep -E "load_backend|offload|device=|CUDA|cpu" | tail -10
echo ""

# 8. 总结
echo "=========================================="
echo "检查总结"
echo "=========================================="
echo ""

# 检查是否使用 CUDA backend
CUDA_BACKEND=$(sudo docker logs ollama 2>&1 | grep -i "load_backend.*cuda" | wc -l)
CPU_BACKEND=$(sudo docker logs ollama 2>&1 | grep -i "load_backend.*cpu" | wc -l)

if [ "$CUDA_BACKEND" -gt 0 ]; then
    echo "✓ 检测到 CUDA backend 使用记录"
else
    echo "✗ 未检测到 CUDA backend 使用记录"
fi

if [ "$CPU_BACKEND" -gt 0 ]; then
    echo "⚠ 检测到 CPU backend 使用记录（可能未使用 GPU）"
else
    echo "✓ 未检测到 CPU backend 使用记录"
fi

# 检查层卸载情况
OFFLOADED=$(sudo docker logs ollama 2>&1 | grep -i "offloaded.*layers to GPU" | grep -v "offloaded 0/" | wc -l)
if [ "$OFFLOADED" -gt 0 ]; then
    echo "✓ 检测到层卸载到 GPU 的记录"
    echo "  最近的卸载记录："
    sudo docker logs ollama 2>&1 | grep -i "offloaded.*layers to GPU" | grep -v "offloaded 0/" | tail -1
else
    echo "✗ 未检测到层卸载到 GPU 的记录（可能所有层都在 CPU 上）"
fi

# 检查 GPU 识别
GPU_DETECTED=$(sudo docker logs ollama 2>&1 | grep -i "inference compute.*CUDA" | wc -l)
if [ "$GPU_DETECTED" -gt 0 ]; then
    echo "✓ GPU 已被识别"
    echo "  GPU 信息："
    sudo docker logs ollama 2>&1 | grep -i "inference compute.*CUDA" | tail -1
else
    echo "✗ GPU 未被识别"
fi

echo ""
echo "=========================================="
echo "提示：如果看到 CPU backend 或 offloaded 0/X，"
echo "      说明模型未使用 GPU。"
echo "=========================================="
