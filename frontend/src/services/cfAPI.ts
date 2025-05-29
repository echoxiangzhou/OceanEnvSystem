// CF规范监控相关的API接口定义和调用

export interface MonitorStatus {
  status: 'running' | 'stopped';
  message?: string;
  processing_results_count?: number;
}

export interface ValidationResult {
  cf_version?: string;
  critical_issues: number;
  warning_issues: number;
  info_issues: number;
  details?: string[];
}

export interface ProcessingResult {
  file_path: string;
  relative_path: string;
  status: 'valid' | 'converted' | 'failed' | 'error';
  timestamp: string;
  validation_result: ValidationResult;
}

export interface ProcessingResultsResponse {
  results: ProcessingResult[];
  total: number;
}

export interface FileInfo {
  name: string;
  path: string;
  full_path: string;
  size: number;
  modified: number;
}

export interface DirectoryStructure {
  standard: FileInfo[];
  raw: FileInfo[];  
  processing: FileInfo[];
}

// 新增：CF规范验证相关接口
export interface ValidationIssue {
  level: 'critical' | 'warning' | 'info';
  code: string;
  message: string;
  location: string;
  suggestion?: string;
}

export interface FileValidationResult {
  is_valid: boolean;
  cf_version?: string;
  critical_issues: number;
  warning_issues: number;
  info_issues: number;
  issues: ValidationIssue[];
}

export interface ConversionResult {
  success: boolean;
  message: string;
  output_path?: string;
  issues_fixed: ValidationIssue[];
  remaining_issues: ValidationIssue[];
  backup_path?: string;
}

const API_BASE = '/api/v1';

// API客户端类
class CFApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API请求失败: ${response.status} ${errorText}`);
    }

    return response.json();
  }

  private async uploadFile<T>(endpoint: string, file: File, additionalData?: Record<string, any>): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const formData = new FormData();
    formData.append('file', file);
    
    if (additionalData) {
      Object.keys(additionalData).forEach(key => {
        formData.append(key, String(additionalData[key]));
      });
    }

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`文件上传失败: ${response.status} ${errorText}`);
    }

    return response.json();
  }

  // ==================== 监控服务相关 ====================

  // 获取监控服务状态
  async getMonitorStatus(): Promise<MonitorStatus> {
    return this.request<MonitorStatus>('/cf/monitor/status');
  }

  // 启动监控服务
  async startMonitor(dataDir: string): Promise<void> {
    return this.request<void>('/cf/monitor/start', {
      method: 'POST',
      body: JSON.stringify({ data_dir: dataDir }),
    });
  }

  // 停止监控服务
  async stopMonitor(): Promise<void> {
    return this.request<void>('/cf/monitor/stop', {
      method: 'POST',
    });
  }

  // 获取处理结果
  async getProcessingResults(limit: number = 100): Promise<ProcessingResultsResponse> {
    return this.request<ProcessingResultsResponse>(`/cf/monitor/results?limit=${limit}`);
  }

  // 获取目录结构
  async getDirectoryStructure(dataDir: string): Promise<DirectoryStructure> {
    return this.request<DirectoryStructure>(`/cf/monitor/structure?data_dir=${encodeURIComponent(dataDir)}`);
  }

  // 扫描目录
  async scanDirectory(): Promise<void> {
    return this.request<void>('/cf/monitor/scan', {
      method: 'POST',
    });
  }

  // 手动处理单个文件
  async processFileManually(filePath: string): Promise<ProcessingResult> {
    return this.request<ProcessingResult>('/cf/monitor/process', {
      method: 'POST',
      body: JSON.stringify({ file_path: filePath }),
    });
  }

  // ==================== 文件验证与转换相关 ====================

  // 验证上传的文件
  async validateUploadedFile(file: File): Promise<FileValidationResult> {
    return this.uploadFile<FileValidationResult>('/cf/validate', file);
  }

  // 转换上传的文件
  async convertUploadedFile(file: File, autoFix: boolean = true): Promise<ConversionResult> {
    return this.uploadFile<ConversionResult>('/cf/convert', file, { auto_fix: autoFix });
  }

  // 验证本地文件（通过路径）
  async validateLocalFile(filePath: string): Promise<FileValidationResult> {
    return this.request<FileValidationResult>('/cf/validate/local', {
      method: 'POST',
      body: JSON.stringify({ file_path: filePath }),
    });
  }

  // 转换本地文件（通过路径）
  async convertLocalFile(filePath: string, autoFix: boolean = true): Promise<ConversionResult> {
    return this.request<ConversionResult>('/cf/convert/local', {
      method: 'POST',
      body: JSON.stringify({ file_path: filePath, auto_fix: autoFix }),
    });
  }

  // ==================== 文件下载相关 ====================

  // 下载转换后的文件
  async downloadConvertedFile(filePath: string): Promise<void> {
    const url = `${API_BASE}/cf/download?file_path=${encodeURIComponent(filePath)}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`下载失败: ${response.status}`);
    }

    // 触发浏览器下载
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = downloadUrl;
    a.download = filePath.split('/').pop() || 'download';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    document.body.removeChild(a);
  }

  // 下载验证报告
  async downloadValidationReport(filePath: string, format: 'json' | 'html' | 'txt' = 'html'): Promise<void> {
    const url = `${API_BASE}/cf/report?file_path=${encodeURIComponent(filePath)}&format=${format}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`报告下载失败: ${response.status}`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = downloadUrl;
    a.download = `cf-validation-report.${format}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    document.body.removeChild(a);
  }

  // ==================== 工具方法 ====================

  // 轮询处理结果的工具方法
  startPollingResults(
    onUpdate: (results: ProcessingResult[]) => void,
    interval: number = 3000,
    limit: number = 100
  ): () => void {
    const poll = async () => {
      try {
        const data = await this.getProcessingResults(limit);
        onUpdate(data.results);
      } catch (error) {
        console.error('轮询处理结果失败:', error);
      }
    };

    // 立即执行一次
    poll();

    // 设置定时器
    const intervalId = setInterval(poll, interval);

    // 返回清理函数
    return () => clearInterval(intervalId);
  }

  // 检查文件格式是否支持
  isValidNetCDFFile(file: File): boolean {
    const validExtensions = ['.nc', '.netcdf', '.nc4'];
    return validExtensions.some(ext => 
      file.name.toLowerCase().endsWith(ext)
    );
  }

  // 格式化问题级别显示文本
  formatIssueLevel(level: string): string {
    const levelMap = {
      'critical': '严重',
      'warning': '警告', 
      'info': '信息'
    };
    return levelMap[level as keyof typeof levelMap] || level;
  }

  // 格式化文件大小
  formatFileSize(bytes: number): string {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }
}

// 导出单例实例
export const cfAPI = new CFApiClient();
