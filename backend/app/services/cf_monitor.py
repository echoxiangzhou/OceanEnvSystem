"""
文件系统监控服务
监控数据目录中的NetCDF文件变化，自动触发CF规范检查和转换
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileMovedEvent
import threading
from .cf_validator import validate_netcdf_file, ValidationResult
from .cf_converter import convert_netcdf_to_cf

logger = logging.getLogger(__name__)


class NetCDFFileHandler(FileSystemEventHandler):
    """NetCDF文件事件处理器"""
    
    def __init__(self, processor: 'FileProcessor'):
        self.processor = processor
        self.processed_files = set()  # 避免重复处理
        self.last_process_time = {}   # 记录最后处理时间
        self.pending_files = {}       # 待处理文件队列，用于延迟处理
        
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory and self._is_netcdf_file(event.src_path):
            # 跳过已转换的文件和特定目录中的文件
            if self._should_skip_file(event.src_path):
                return
            
            # 检查是否已经处理过
            if event.src_path in self.processed_files:
                logger.debug(f"文件创建事件：文件已处理过，跳过: {event.src_path}")
                return
            
            logger.info(f"检测到新NetCDF文件创建: {event.src_path}")
            self._schedule_delayed_processing(event.src_path, event_type="created")
    
    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory and self._is_netcdf_file(event.src_path):
            # 跳过已转换的文件和特定目录中的文件
            if self._should_skip_file(event.src_path):
                return
            
            # 检查是否已经处理过 - 这是关键的重复检查
            if event.src_path in self.processed_files:
                logger.debug(f"文件修改事件：文件已处理过，跳过: {event.src_path}")
                return
            
            # 避免重复处理（文件修改可能触发多次事件）
            current_time = time.time()
            last_time = self.last_process_time.get(event.src_path, 0)
            
            if current_time - last_time > 2:  # 减少到2秒间隔，提高响应性
                logger.info(f"检测到NetCDF文件修改: {event.src_path}")
                self._schedule_delayed_processing(event.src_path, event_type="modified")
                self.last_process_time[event.src_path] = current_time

    def on_moved(self, event):
        """文件移动事件 - 处理剪切粘贴操作"""
        if not event.is_directory and self._is_netcdf_file(event.dest_path):
            if self._should_skip_file(event.dest_path):
                return
            
            # 检查是否已经处理过
            if event.dest_path in self.processed_files:
                logger.debug(f"文件移动事件：文件已处理过，跳过: {event.dest_path}")
                return
            
            logger.info(f"检测到NetCDF文件移动: {event.src_path} -> {event.dest_path}")
            self._schedule_delayed_processing(event.dest_path, event_type="moved")
    
    def _schedule_delayed_processing(self, file_path: str, event_type: str = "unknown"):
        """延迟处理文件，确保文件完全复制完成"""
        current_time = time.time()
        
        # 检查文件是否已经被处理过
        if file_path in self.processed_files:
            logger.debug(f"文件已处理过，跳过: {file_path}")
            return
        
        # 检查是否已经在待处理队列中
        if file_path in self.pending_files:
            logger.debug(f"文件已在待处理队列中，更新时间戳: {file_path}")
            self.pending_files[file_path]['timestamp'] = current_time
            self.pending_files[file_path]['event_type'] = event_type
            return
        
        # 记录待处理文件
        self.pending_files[file_path] = {
            'timestamp': current_time,
            'event_type': event_type,
            'size_checks': []
        }
        
        logger.debug(f"文件加入待处理队列: {file_path} (事件类型: {event_type})")
        
        # 启动延迟检查线程
        threading.Thread(
            target=self._delayed_file_check,
            args=(file_path,),
            daemon=True
        ).start()
    
    def _delayed_file_check(self, file_path: str):
        """延迟检查文件是否完全复制完成"""
        import os
        
        max_wait_time = 30  # 最大等待30秒
        check_interval = 2  # 每2秒检查一次
        stable_checks = 2   # 需要连续2次检查文件大小不变
        
        start_time = time.time()
        stable_count = 0
        last_size = -1
        
        while time.time() - start_time < max_wait_time:
            try:
                # 检查是否已经被其他线程处理过
                if file_path in self.processed_files:
                    logger.debug(f"文件在等待期间已被处理，停止检查: {file_path}")
                    if file_path in self.pending_files:
                        del self.pending_files[file_path]
                    return
                
                if not os.path.exists(file_path):
                    logger.debug(f"文件不存在，停止检查: {file_path}")
                    if file_path in self.pending_files:
                        del self.pending_files[file_path]
                    return
                
                # 检查文件大小是否稳定
                current_size = os.path.getsize(file_path)
                
                if current_size == last_size and current_size > 0:
                    stable_count += 1
                    logger.debug(f"文件大小稳定检查 {stable_count}/{stable_checks}: {file_path} ({current_size} bytes)")
                else:
                    stable_count = 0
                    logger.debug(f"文件大小变化: {file_path} ({last_size} -> {current_size} bytes)")
                
                last_size = current_size
                
                # 如果文件大小连续稳定，且文件可读，开始处理
                if stable_count >= stable_checks:
                    # 额外检查：尝试打开文件确保文件完整
                    if self._is_file_accessible(file_path):
                        logger.info(f"文件稳定且可访问，开始处理: {file_path}")
                        # 在实际开始处理前标记
                        self.processed_files.add(file_path)
                        self._schedule_processing(file_path)
                        break
                    else:
                        logger.debug(f"文件暂时不可访问，继续等待: {file_path}")
                        stable_count = 0  # 重置计数
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.warning(f"检查文件时出错 {file_path}: {str(e)}")
                break
        
        # 清理待处理文件记录
        if file_path in self.pending_files:
            del self.pending_files[file_path]
            
        # 如果超时未处理，强制处理（如果文件存在且未被处理）
        if time.time() - start_time >= max_wait_time:
            if os.path.exists(file_path) and file_path not in self.processed_files:
                logger.warning(f"文件检查超时，强制开始处理: {file_path}")
                self.processed_files.add(file_path)
                self._schedule_processing(file_path)
    
    def _is_file_accessible(self, file_path: str) -> bool:
        """检查文件是否可访问（简单的完整性检查）"""
        try:
            # 对于NetCDF文件，尝试简单读取文件头
            with open(file_path, 'rb') as f:
                header = f.read(4)
                # NetCDF文件通常以 "CDF\001" 或 "\211HDF" 开头
                if header.startswith(b'CDF\001') or header.startswith(b'\211HDF'):
                    return True
                # 也可能是其他有效的NetCDF格式
                f.seek(0)
                # 尝试读取更多内容确保文件不被锁定
                f.read(1024)
                return True
        except (IOError, OSError, PermissionError) as e:
            logger.debug(f"文件访问检查失败 {file_path}: {str(e)}")
            return False
        except Exception as e:
            logger.debug(f"文件格式检查失败 {file_path}: {str(e)}")
            # 即使格式检查失败，如果文件可读也继续处理
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)
                return True
            except:
                return False
    
    def _is_netcdf_file(self, file_path: str) -> bool:
        """检查是否为NetCDF文件"""
        return file_path.lower().endswith(('.nc', '.netcdf', '.nc4'))
    
    def _should_skip_file(self, file_path: str) -> bool:
        """检查是否应该跳过此文件"""
        path = Path(file_path)
        
        # 跳过已转换的文件（文件名包含_cf）
        if '_cf' in path.stem:
            return True
        
        # 跳过在processing和standard目录中的文件
        if any(part in ['processing', 'standard'] for part in path.parts):
            return True
        
        return False
    
    def _schedule_processing(self, file_path: str):
        """调度文件处理"""
        # 最后一次检查，避免处理已删除的文件
        if not os.path.exists(file_path):
            logger.debug(f"文件不存在，取消处理: {file_path}")
            # 从已处理集合中移除，以防文件再次出现
            self.processed_files.discard(file_path)
            return
            
        # 使用线程池异步处理，避免阻塞文件监控
        threading.Thread(
            target=self._safe_process_file,
            args=(file_path,),
            daemon=True
        ).start()
    
    def _safe_process_file(self, file_path: str):
        """安全的文件处理包装器"""
        try:
            # 在处理前再次确认文件存在
            if not os.path.exists(file_path):
                logger.debug(f"处理前发现文件不存在: {file_path}")
                self.processed_files.discard(file_path)
                return
                
            # 调用实际的处理逻辑
            self.processor.process_file(file_path)
            
            # 处理完成后，保持在已处理集合中一段时间，避免重复触发
            # 使用定时器在一段时间后清理
            threading.Timer(
                300.0,  # 5分钟后清理
                lambda: self.processed_files.discard(file_path)
            ).start()
            
        except Exception as e:
            logger.error(f"安全处理文件失败 {file_path}: {str(e)}", exc_info=True)
            # 处理失败时从已处理集合中移除，允许重试
            self.processed_files.discard(file_path)


class FileProcessor:
    """文件处理器"""
    
    def __init__(self, data_dir: str, callback: Optional[Callable] = None):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / 'raw'
        self.processing_dir = self.data_dir / 'processing' 
        self.standard_dir = self.data_dir / 'standard'
        self.callback = callback
        
        # 创建必要的目录
        self._create_directories()
    
    def _create_directories(self):
        """创建目录结构"""
        for directory in [self.raw_dir, self.processing_dir, self.standard_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"确保目录存在: {directory}")
    
    def process_file(self, file_path: str):
        """处理单个文件"""
        try:
            file_path = Path(file_path)
            
            # 检查文件是否存在且为NetCDF格式
            if not file_path.exists():
                logger.warning(f"文件不存在: {file_path}")
                return
            
            if not self._is_netcdf_file(str(file_path)):
                logger.info(f"跳过非NetCDF文件: {file_path}")
                return
            
            # 跳过已经转换过的文件（文件名包含_cf）
            if '_cf' in file_path.stem:
                logger.info(f"跳过已转换的文件: {file_path}")
                return
            
            # 主要处理raw目录中的文件，跳过processing和standard目录中的文件
            if any(part in ['processing', 'standard'] for part in file_path.parts):
                logger.debug(f"跳过processing/standard目录中的文件: {file_path}")
                return
            
            # 优先处理raw目录中的文件
            if 'raw' not in str(file_path):
                logger.info(f"文件不在raw目录，跳过处理: {file_path}")
                return
            
            logger.info(f"开始处理raw目录中的文件: {file_path}")
            
            # 计算相对路径（相对于data_dir）
            try:
                rel_path = file_path.relative_to(self.data_dir)
            except ValueError:
                # 文件不在data_dir内，移动到raw目录
                rel_path = Path('raw') / file_path.name
                raw_target = self.raw_dir / file_path.name
                raw_target.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(file_path, raw_target)
                file_path = raw_target
                rel_path = file_path.relative_to(self.data_dir)
            
            # 验证CF规范
            validation_result = validate_netcdf_file(str(file_path))
            
            # 根据验证结果决定处理方式
            if validation_result.is_valid:
                # 文件已符合CF标准，移动到standard目录
                self._move_to_standard(file_path, rel_path)
                status = 'valid'
            else:
                # 文件不符合CF标准，尝试转换
                status = self._convert_file(file_path, rel_path, validation_result)
            
            # 调用回调函数
            if self.callback:
                self.callback({
                    'file_path': str(file_path),
                    'relative_path': str(rel_path),
                    'status': status,
                    'validation_result': validation_result,
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {str(e)}", exc_info=True)
    
    def _move_to_standard(self, file_path: Path, rel_path: Path):
        """移动符合CF标准的文件到standard目录"""
        try:
            # 计算目标路径
            standard_path = self.standard_dir / rel_path.name
            standard_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果standard目录中已存在同名文件，先删除
            if standard_path.exists():
                standard_path.unlink()
                logger.info(f"删除已存在的standard文件: {standard_path}")
            
            # 复制文件到standard目录
            import shutil
            shutil.copy2(file_path, standard_path)
            logger.info(f"文件已移动到standard目录: {standard_path}")
            
            # 提取并保存元数据到数据库
            try:
                from app.services.metadata_extractor import extract_and_save_metadata
                extract_and_save_metadata(str(standard_path), "standard")
                logger.info(f"标准文件元数据已保存到数据库: {standard_path}")
            except Exception as e:
                logger.warning(f"保存标准文件元数据失败: {str(e)}")
            
            # 删除raw目录中的原文件
            if file_path.exists() and 'raw' in str(file_path):
                try:
                    file_path.unlink()
                    logger.info(f"已删除raw目录中的原文件: {file_path}")
                except Exception as e:
                    logger.warning(f"删除raw目录中的原文件失败: {str(e)}")
                    # 即使删除失败也继续执行，避免阻塞
                
        except Exception as e:
            logger.error(f"移动文件到standard目录失败: {str(e)}", exc_info=True)
            raise
    
    def _convert_file(self, file_path: Path, rel_path: Path, validation_result: ValidationResult) -> str:
        """转换文件"""
        processing_path = None
        try:
            # 移动到processing目录
            processing_path = self.processing_dir / rel_path.name
            processing_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            if str(file_path) != str(processing_path):
                shutil.copy2(file_path, processing_path)
                logger.info(f"文件复制到processing目录: {processing_path}")
            
            # 转换文件，保存到standard目录
            original_name = file_path.stem
            converted_filename = f"{original_name}.nc"  # 保持原文件名
            standard_path = self.standard_dir / converted_filename
            standard_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果standard目录中已存在同名文件，先删除
            if standard_path.exists():
                standard_path.unlink()
                logger.info(f"删除已存在的standard文件: {standard_path}")
            
            convert_result = convert_netcdf_to_cf(
                str(processing_path),
                str(standard_path),
                auto_fix=True,
                backup=True
            )
            
            if convert_result['success']:
                logger.info(f"文件转换成功，保存到standard目录: {standard_path}")
                
                # 转换成功后删除raw目录中的原文件
                if file_path.exists() and 'raw' in str(file_path):
                    try:
                        file_path.unlink()
                        logger.info(f"转换成功，已删除raw目录中的原文件: {file_path}")
                    except Exception as e:
                        logger.warning(f"删除raw目录中的原文件失败: {str(e)}")
                        # 即使删除失败也继续执行
                
                # 保留processing目录中的备份文件，不删除
                logger.info(f"备份文件保留在processing目录: {processing_path}")
                
                return 'converted'
            else:
                logger.error(f"文件转换失败: {convert_result['message']}")
                return 'failed'
                
        except Exception as e:
            logger.error(f"转换文件失败: {str(e)}", exc_info=True)
            return 'error'
    
    def _is_netcdf_file(self, file_path: str) -> bool:
        """检查是否为NetCDF文件"""
        return file_path.lower().endswith(('.nc', '.netcdf', '.nc4'))
    
    def _should_skip_file_path(self, file_path: Path) -> bool:
        """检查是否应该跳过此文件（Path对象版本）"""
        # 跳过已转换的文件（文件名包含_cf）
        if '_cf' in file_path.stem:
            return True
        
        # 跳过在processing和standard目录中的文件
        if any(part in ['processing', 'standard'] for part in file_path.parts):
            return True
        
        return False


class DataDirectoryMonitor:
    """数据目录监控器"""
    
    def __init__(self, data_dir: str, callback: Optional[Callable] = None):
        self.data_dir = data_dir
        self.callback = callback
        self.processor = FileProcessor(data_dir, callback)
        self.observer = Observer()
        self.is_monitoring = False
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            logger.warning("监控已经启动")
            return
        
        # 创建事件处理器
        event_handler = NetCDFFileHandler(self.processor)
        
        # 添加监控路径
        self.observer.schedule(event_handler, self.data_dir, recursive=True)
        
        # 启动监控
        self.observer.start()
        self.is_monitoring = True
        
        logger.info(f"开始监控数据目录: {self.data_dir}")
        
        # 处理现有文件
        self.scan_existing_files()
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return
        
        self.observer.stop()
        self.observer.join()
        self.is_monitoring = False
        
        logger.info("数据目录监控已停止")
    
    def scan_existing_files(self):
        """扫描现有文件"""
        logger.info("扫描raw目录中的现有NetCDF文件...")
        
        # 主要扫描raw目录
        raw_path = Path(self.data_dir) / 'raw'
        if not raw_path.exists():
            raw_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建raw目录: {raw_path}")
        
        netcdf_files = []
        
        # 递归查找raw目录中的NetCDF文件
        for pattern in ['**/*.nc', '**/*.netcdf', '**/*.nc4']:
            netcdf_files.extend(raw_path.glob(pattern))
        
        # 过滤文件
        filtered_files = []
        for file_path in netcdf_files:
            # 跳过已转换的文件
            if '_cf' not in file_path.stem:
                filtered_files.append(file_path)
        
        logger.info(f"在raw目录发现 {len(netcdf_files)} 个NetCDF文件，过滤后剩余 {len(filtered_files)} 个需要处理")
        
        # 处理每个文件
        for file_path in filtered_files:
            threading.Thread(
                target=self.processor.process_file,
                args=(str(file_path),),
                daemon=True
            ).start()
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_monitoring()


class CFMonitorService:
    """CF规范监控服务"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.monitor = None
        self.processing_results = []  # 存储处理结果
    
    def start(self):
        """启动服务"""
        self.monitor = DataDirectoryMonitor(
            self.data_dir,
            callback=self._on_file_processed
        )
        self.monitor.start_monitoring()
        logger.info("CF规范监控服务已启动")
    
    def stop(self):
        """停止服务"""
        if self.monitor:
            self.monitor.stop_monitoring()
            self.monitor = None
        logger.info("CF规范监控服务已停止")
    
    def _on_file_processed(self, result: Dict[str, Any]):
        """文件处理完成回调"""
        self.processing_results.append(result)
        
        # 保留最近100个处理结果
        if len(self.processing_results) > 100:
            self.processing_results = self.processing_results[-100:]
        
        logger.info(f"文件处理完成: {result['file_path']} -> {result['status']}")
    
    def get_processing_results(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取处理结果"""
        return self.processing_results[-limit:]
    
    def get_pending_files_status(self) -> Dict[str, Any]:
        """获取待处理文件状态"""
        if not self.monitor or not hasattr(self.monitor.processor, 'event_handler'):
            return {"pending_files": [], "count": 0}
        
        try:
            # 尝试从事件处理器获取待处理文件
            event_handler = None
            for handler in getattr(self.monitor.observer, '_handlers', {}).values():
                for h in handler:
                    if hasattr(h, 'pending_files'):
                        event_handler = h
                        break
                if event_handler:
                    break
            
            if event_handler and hasattr(event_handler, 'pending_files'):
                pending_files = []
                current_time = time.time()
                
                for file_path, info in event_handler.pending_files.items():
                    pending_files.append({
                        "file_path": file_path,
                        "event_type": info.get('event_type', 'unknown'),
                        "waiting_time": current_time - info.get('timestamp', current_time),
                        "timestamp": datetime.fromtimestamp(info.get('timestamp', current_time)).isoformat()
                    })
                
                return {
                    "pending_files": pending_files,
                    "count": len(pending_files)
                }
        except Exception as e:
            logger.warning(f"获取待处理文件状态失败: {str(e)}")
        
        return {"pending_files": [], "count": 0}
    
    def get_monitor_status(self) -> Dict[str, Any]:
        """获取详细的监控状态"""
        base_status = {
            "service_running": self.monitor is not None,
            "data_dir": self.data_dir,
            "processing_results_count": len(self.processing_results)
        }
        
        if self.monitor:
            base_status.update({
                "monitoring_active": self.monitor.is_monitoring,
                "observer_running": self.monitor.observer.is_alive() if self.monitor.observer else False
            })
            
            # 添加待处理文件信息
            pending_status = self.get_pending_files_status()
            base_status.update(pending_status)
        
        return base_status
    
    def scan_directory(self):
        """手动扫描目录"""
        if self.monitor:
            self.monitor.scan_existing_files()
    
    def process_file_manually(self, file_path: str) -> Dict[str, Any]:
        """手动处理单个文件"""
        if not self.monitor:
            raise RuntimeError("监控服务未启动")
        
        # 同步处理文件
        self.monitor.processor.process_file(file_path)
        
        # 查找最新的处理结果
        for result in reversed(self.processing_results):
            if result['file_path'] == file_path:
                return result
        
        return {'status': 'not_found', 'file_path': file_path}


def create_cf_monitor_service(data_dir: str) -> CFMonitorService:
    """创建CF规范监控服务实例"""
    return CFMonitorService(data_dir)


if __name__ == "__main__":
    # 测试代码
    import sys
    import signal
    
    if len(sys.argv) > 1:
        data_directory = sys.argv[1]
    else:
        data_directory = "/tmp/test_data"
    
    # 创建测试目录
    os.makedirs(data_directory, exist_ok=True)
    
    # 创建监控服务
    service = CFMonitorService(data_directory)
    
    def signal_handler(sig, frame):
        print("\n正在停止监控服务...")
        service.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        service.start()
        print(f"监控服务已启动，监控目录: {data_directory}")
        print("按 Ctrl+C 停止监控")
        
        # 保持程序运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        service.stop()
        print("监控服务已停止")
