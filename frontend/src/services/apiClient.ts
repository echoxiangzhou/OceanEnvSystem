import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    // 根据环境确定API基础URL
    const isDevelopment = import.meta.env.MODE === 'development';
    const baseURL = isDevelopment 
      ? 'http://localhost:8000/api/v1'  // 开发环境：直接指向后端服务器
      : '/api/v1';                      // 生产环境：使用相对路径

    this.client = axios.create({
      baseURL,
      timeout: 30000, // 30秒超时
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error);
        
        // 处理常见错误
        if (error.code === 'ECONNRESET' || error.code === 'ECONNABORTED') {
          console.error('连接被重置或超时');
          error.message = '网络连接超时，请检查服务器状态';
        } else if (error.code === 'ERR_NETWORK') {
          console.error('网络错误');
          error.message = '网络连接失败，请检查后端服务是否启动';
        } else if (error.response?.status === 500) {
          console.error('服务器内部错误');
          error.message = '服务器处理请求时出错';
        } else if (error.response?.status === 404) {
          console.error('资源未找到');
          error.message = '请求的资源不存在';
        }
        
        return Promise.reject(error);
      }
    );
  }

  // 设置认证Token
  setAuthToken(token: string | null): void {
    if (token) {
      this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete this.client.defaults.headers.common['Authorization'];
    }
  }

  // GET请求
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config);
  }

  // POST请求
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config);
  }

  // PUT请求
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config);
  }

  // DELETE请求
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config);
  }

  // 文件上传
  async uploadFile<T = any>(
    url: string, 
    file: File, 
    fieldName: string = 'file',
    additionalData?: Record<string, any>,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    const formData = new FormData();
    formData.append(fieldName, file);
    
    // 添加额外数据
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, typeof value === 'string' ? value : JSON.stringify(value));
      });
    }

    return this.client.post<T>(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers,
      },
    });
  }

  // 文件下载
  async downloadFile(
    url: string, 
    filename: string, 
    params?: Record<string, any>
  ): Promise<string> {
    try {
      const response = await this.client.get(url, {
        params,
        responseType: 'blob',
      });

      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      return downloadUrl;
    } catch (error) {
      console.error('Error downloading file:', error);
      throw error;
    }
  }
}

// 创建单例实例
const apiClient = new ApiClient();

// 导出为默认导出和命名导出，兼容不同的导入方式
export default apiClient;
export { apiClient };
