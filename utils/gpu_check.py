"""
GPU / CUDA 设备检查工具

使用 Python 检查 CUDA 设备是否就绪，跨平台通用，无需各平台单独脚本。
"""
import subprocess
from typing import Tuple


def check_cuda_ready() -> Tuple[bool, str]:
    """
    检查 CUDA 设备是否就绪。

    Returns:
        (success, message): 是否就绪及说明信息
    """
    # 方法1: PyTorch（若已安装）
    try:
        import torch
        if torch.cuda.is_available():
            count = torch.cuda.device_count()
            name = torch.cuda.get_device_name(0) if count > 0 else "N/A"
            return True, f"CUDA 可用，{count} 个设备，首设备: {name}"
        return False, "PyTorch 已安装但 CUDA 不可用"
    except ImportError:
        pass
    except Exception as e:
        return False, f"PyTorch CUDA 检查异常: {e}"

    # 方法2: pynvml（nvidia-ml-py3，轻量级）
    try:
        import pynvml
        pynvml.nvmlInit()
        count = pynvml.nvmlDeviceGetCount()
        if count > 0:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            name_bytes = pynvml.nvmlDeviceGetName(handle)
            name = name_bytes.decode("utf-8") if isinstance(name_bytes, bytes) else str(name_bytes)
            pynvml.nvmlShutdown()
            return True, f"CUDA 可用，{count} 个设备，首设备: {name}"
        pynvml.nvmlShutdown()
        return False, "未检测到 GPU 设备"
    except ImportError:
        pass
    except Exception as e:
        return False, f"pynvml 检查异常: {e}"

    # 方法3: nvidia-smi（系统命令，无额外依赖）
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            devices = result.stdout.strip().split("\n")
            return True, f"CUDA 可用，{len(devices)} 个设备，首设备: {devices[0].strip()}"
        return False, "nvidia-smi 未检测到 GPU"
    except FileNotFoundError:
        return False, "nvidia-smi 未找到（请确认已安装 NVIDIA 驱动）"
    except subprocess.TimeoutExpired:
        return False, "nvidia-smi 执行超时"
    except Exception as e:
        return False, f"nvidia-smi 检查异常: {e}"
