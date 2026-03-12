#!/bin/bash
# 下载GitHub依赖到本地vendor目录
# 用于在构建Docker镜像前预先下载依赖，避免构建时从GitHub拉取

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENDOR_DIR="${SCRIPT_DIR}/vendor"

echo "开始下载GitHub依赖到本地..."

# 创建vendor目录
mkdir -p "${VENDOR_DIR}"

# 下载 PaddleOCR
if [ -d "${VENDOR_DIR}/PaddleOCR" ]; then
    echo "PaddleOCR 已存在，跳过下载"
    echo "如需更新，请删除 ${VENDOR_DIR}/PaddleOCR 后重新运行此脚本"
else
    echo "正在克隆 PaddleOCR..."
    cd "${VENDOR_DIR}"
    git clone --depth 1 https://github.com/PaddlePaddle/PaddleOCR.git
    echo "PaddleOCR 下载完成"
fi

echo ""
echo "所有依赖下载完成！"
echo "现在可以运行 docker build 构建镜像了"
