# Vendor 目录说明

此目录用于存放从GitHub下载的依赖包，避免在Docker构建时从GitHub拉取。

## 使用方法

### 1. 下载依赖

在构建Docker镜像之前，请先运行下载脚本：

**Linux/macOS:**
```bash
chmod +x download_dependencies.sh
./download_dependencies.sh
```

**Windows CMD:**
```cmd
download_dependencies.cmd
```

**Windows PowerShell:**
```powershell
.\download_dependencies.ps1
```

### 2. 构建Docker镜像

下载完成后，即可正常构建Docker镜像：

```bash
docker build -t advanced-rag .
```

## 当前依赖

- **PaddleOCR**: `https://github.com/PaddlePaddle/PaddleOCR.git`
  - 用于OCR功能，支持扫描版PDF识别

## 更新依赖

如果需要更新依赖，请删除对应的目录后重新运行下载脚本：

```bash
# Linux/macOS
rm -rf vendor/PaddleOCR
./download_dependencies.sh

# Windows CMD
rmdir /s /q vendor\PaddleOCR
download_dependencies.cmd

# Windows PowerShell
Remove-Item -Recurse -Force vendor\PaddleOCR
.\download_dependencies.ps1
```

## 注意事项

1. **必须预先下载**: 构建Docker镜像前必须运行下载脚本，否则构建会失败
2. **网络要求**: 下载脚本需要能够访问GitHub，建议在能正常访问GitHub的环境中运行
3. **版本控制**: vendor目录中的.git目录会被.dockerignore排除，但源代码会被包含
4. **镜像大小**: vendor目录会增加镜像大小，但可以避免构建时的网络问题
