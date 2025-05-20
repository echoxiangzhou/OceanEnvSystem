// 简单的API客户端，用于开发环境
const baseUrl = '/api/v1'; // API前缀

// 通用响应类型
export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

// 模拟延迟
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// 简单的API客户端
const apiClient = {
  // GET请求
  async get<T>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    console.log(`[API] GET ${endpoint}`, params);
    // 开发环境下模拟API调用
    await delay(500);
    return { data: {} as T };
  },

  // POST请求
  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    console.log(`[API] POST ${endpoint}`, data);
    // 开发环境下模拟API调用
    await delay(800);
    return { data: {} as T };
  },

  // PUT请求
  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    console.log(`[API] PUT ${endpoint}`, data);
    // 开发环境下模拟API调用
    await delay(600);
    return { data: {} as T };
  },

  // DELETE请求
  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    console.log(`[API] DELETE ${endpoint}`);
    // 开发环境下模拟API调用
    await delay(700);
    return { data: {} as T };
  },

  // 文件上传
  async uploadFile<T>(endpoint: string, file: File, fieldName: string = 'file', additionalData?: Record<string, string>): Promise<ApiResponse<T>> {
    console.log(`[API] UPLOAD to ${endpoint}`, { file, additionalData });
    // 开发环境下模拟API调用
    await delay(1000);
    return { data: {} as T };
  },

  // 文件下载
  async downloadFile(endpoint: string, filename: string): Promise<string | null> {
    console.log(`[API] DOWNLOAD from ${endpoint} as ${filename}`);
    // 开发环境下模拟API调用
    await delay(1200);
    return null;
  }
};

export default apiClient;
