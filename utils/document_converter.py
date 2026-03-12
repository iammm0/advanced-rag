"""文档转换工具：将.doc格式转换为.docx（使用 LibreOffice）"""
import os
import tempfile
import subprocess
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DocumentConverter:
    """文档转换器：将.doc格式转换为.docx"""
    
    @staticmethod
    def convert_doc_to_docx(file_path: str) -> Optional[str]:
        """
        将.doc文件转换为.docx
        使用 LibreOffice 命令行工具进行转换
        
        Args:
            file_path: 源文件路径
            
        Returns:
            转换后的.docx文件路径，如果转换失败返回None
            
        Raises:
            Exception: 如果 LibreOffice 不可用，会抛出异常
        """
        result = DocumentConverter._convert_with_libreoffice(file_path)
        if result:
            return result
        
        # 如果 LibreOffice 不可用，抛出异常
        raise Exception(
            "LibreOffice 不可用，无法转换 .doc 文件。"
            "请安装 LibreOffice 并确保 soffice 在 PATH 中，"
            "或设置 LIBREOFFICE_PATH 环境变量。"
            "在 Docker 容器中，LibreOffice 应该已通过 Dockerfile 安装。"
        )
    
    @staticmethod
    def _convert_with_libreoffice(file_path: str) -> Optional[str]:
        """使用 LibreOffice 命令行工具进行转换"""
        # 尝试不同的 LibreOffice 命令名称和路径
        libreoffice_cmds = []
        
        # 首先检查环境变量
        env_path = os.environ.get('LIBREOFFICE_PATH')
        if env_path and os.path.exists(env_path):
            libreoffice_cmds.append(env_path)
            logger.debug(f"从环境变量找到 LibreOffice: {env_path}")
        
        # Linux 常见安装路径（容器环境）
        if os.name != 'nt':  # Linux/Unix
            linux_paths = [
                '/usr/lib/libreoffice/program/soffice',
                '/usr/bin/libreoffice',
                '/usr/bin/soffice',
                '/opt/libreoffice/program/soffice',
            ]
            for path in linux_paths:
                if os.path.exists(path):
                    libreoffice_cmds.append(path)
                    logger.debug(f"找到 LibreOffice 安装路径: {path}")
        
        # Windows 常见安装路径
        if os.name == 'nt':  # Windows
            common_paths = [
                r'C:\Program Files\LibreOffice\program\soffice.exe',
                r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
            ]
            # 检查用户安装路径
            user_profile = os.environ.get('USERPROFILE', '')
            if user_profile:
                common_paths.append(
                    os.path.join(user_profile, r'AppData\Local\Programs\LibreOffice\program\soffice.exe')
                )
            
            # 检查环境变量中的路径
            program_files = os.environ.get('ProgramFiles', '')
            program_files_x86 = os.environ.get('ProgramFiles(x86)', '')
            if program_files:
                common_paths.append(os.path.join(program_files, r'LibreOffice\program\soffice.exe'))
            if program_files_x86:
                common_paths.append(os.path.join(program_files_x86, r'LibreOffice\program\soffice.exe'))
            
            for path in common_paths:
                if os.path.exists(path):
                    libreoffice_cmds.append(path)
                    logger.debug(f"找到 LibreOffice 安装路径: {path}")
        
        # 添加到 PATH 中的命令
        libreoffice_cmds.extend(['libreoffice', 'soffice', 'soffice.exe'])
        
        cmd_path = None
        
        for cmd in libreoffice_cmds:
            try:
                # 检查命令是否存在
                result = subprocess.run(
                    [cmd, '--version'],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                if result.returncode == 0:
                    cmd_path = cmd
                    logger.info(f"找到 LibreOffice: {cmd_path}")
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
            except Exception as e:
                logger.debug(f"检查 LibreOffice 命令 {cmd} 失败: {str(e)}")
                continue
        
        if not cmd_path:
            logger.debug("LibreOffice 未安装或不在 PATH 中")
            return None
        
        try:
            # 创建临时输出目录
            output_dir = tempfile.mkdtemp()
            
            # 使用 LibreOffice 转换
            result = subprocess.run(
                [
                    cmd_path,
                    '--headless',
                    '--convert-to', 'docx',
                    '--outdir', output_dir,
                    file_path
                ],
                capture_output=True,
                timeout=60,
                text=True
            )
            
            if result.returncode == 0:
                # 查找生成的 docx 文件
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                generated_docx = os.path.join(output_dir, f"{base_name}.docx")
                
                if os.path.exists(generated_docx):
                    # 移动到目标位置
                    final_docx = file_path.rsplit('.', 1)[0] + '_converted.docx'
                    import shutil
                    shutil.move(generated_docx, final_docx)
                    
                    # 清理临时目录
                    try:
                        os.rmdir(output_dir)
                    except:
                        pass
                    
                    logger.info(f"使用 LibreOffice 成功转换: {final_docx}")
                    return final_docx
        except subprocess.TimeoutExpired:
            logger.debug("LibreOffice 转换超时")
        except Exception as e:
            logger.debug(f"LibreOffice 转换失败: {str(e)}")
        
        return None
