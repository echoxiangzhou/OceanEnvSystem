import apiClient from './apiClient';
import { 
  ApiResponse,
  DatasetMetadata, 
  Dataset,
  DataConversionResponse,
  FileUploadResponse,
  FusionTaskResponse,
  TaskStatus,
  FusionTaskRequest
} from '../types/api';
import { mockDatasets, mockOpenDAPData } from '../mocks/mockData';

// 检查是否使用模拟数据（开发环境使用模拟数据）
const USE_MOCK_DATA = false;

/**
 * DataService - handles all data-related API calls
 */
class DataService {
  private static instance: DataService;

  // Private constructor to prevent direct instantiation
  private constructor() {}

  // Public static method to get the singleton instance
  public static getInstance(): DataService {
    if (!DataService.instance) {
      DataService.instance = new DataService();
    }
    return DataService.instance;
  }

  /**
   * Get a list of data files
   */
  async getDataList(ext?: string): Promise<ApiResponse<string[]>> {
    if (USE_MOCK_DATA) {
      return { data: mockDatasets.map(d => d.file_location) };
    }
    
    try {
      // 确保返回的是数组
      const response = await apiClient.get<string[]>('/data/list', { ext });
      if (!response.data) {
        return { data: [] };
      }
      return response;
    } catch (error) {
      console.error("Error fetching data list:", error);
      return { data: [], error: error instanceof Error ? error.message : String(error) };
    }
  }

  /**
   * Get metadata for a specific data file
   */
  async getDataMetadata(relpath: string): Promise<ApiResponse<DatasetMetadata>> {
    if (USE_MOCK_DATA) {
      return { data: mockOpenDAPData };
    }
    
    try {
      return await apiClient.get<DatasetMetadata>('/data/metadata', { relpath });
    } catch (error) {
      console.error("Error fetching data metadata:", error);
      return { error: error instanceof Error ? error.message : String(error) };
    }
  }

  /**
   * Get a formatted list of Thredds datasets
   */
  async getThreddsDatasets(ext?: string): Promise<ApiResponse<Dataset[]>> {
    if (USE_MOCK_DATA) {
      return { data: mockDatasets };
    }
    
    const response = await apiClient.get<Dataset[]>('/data/list/thredds/formatted', { ext });
    console.log("Thredds datasets response from apiClient:", response);
      
    if (response && response.error) {
      throw new Error(response.error); 
    }
      
    if (!response || !response.data || !Array.isArray(response.data)) {
      console.warn("API did not return a valid array for Thredds datasets:", response?.data);
      throw new Error('获取到的数据格式不正确或为空');
    }
      
    return response;
  }

  /**
   * Get a formatted list of standard datasets (CF-converted files)
   */
  async getStandardDatasets(ext?: string): Promise<ApiResponse<Dataset[]>> {
    if (USE_MOCK_DATA) {
      return { data: mockDatasets };
    }
    
    const params = ext ? { ext } : {};
    const response = await apiClient.get<Dataset[]>('/data/list/standard', { params });
    console.log("Standard datasets response from apiClient:", response);
      
    if (response && response.error) {
      throw new Error(response.error); 
    }
      
    if (!response || !response.data || !Array.isArray(response.data)) {
      console.warn("API did not return a valid array for standard datasets:", response?.data);
      throw new Error('获取到的标准数据格式不正确或为空');
    }
      
    return response;
  }

  /**
   * Get Thredds metadata by dataset ID
   */
  async getThreddsMetadataById(datasetId: string): Promise<ApiResponse<DatasetMetadata>> {
    if (USE_MOCK_DATA) {
      return { data: mockOpenDAPData };
    }
    
    try {
      const metadata = await apiClient.get<DatasetMetadata>(`/data/thredds/datasets/${datasetId}/metadata`);
      return { data: metadata };
    } catch (error: any) {
      console.error(`Error fetching Thredds metadata for ID ${datasetId}:`, error);
      return { error: this.formatErrorMessage(error, '获取Thredds元数据失败') };
    }
  }

  /**
   * Download a data file
   */
  async downloadDataFile(relpath: string, filename: string): Promise<string | null> {
    if (USE_MOCK_DATA) {
      console.log(`Mocked download of file: ${relpath} as ${filename}`);
      return null;
    }
    
    try {
      return await apiClient.downloadFile('/data/download/thredds', filename, { relpath });
    } catch (error) {
      console.error("Error downloading data file:", error);
      return null;
    }
  }

  /**
   * Download a file from Thredds server
   */
  async downloadThreddsFile(filePath: string, fileName?: string): Promise<void> {
    if (!filePath) {
      console.error('downloadThreddsFile called with empty filePath');
      throw new Error('文件路径不能为空');
    }
    try {
      const response = await apiClient.get<Blob>('/data/thredds/download', {
        params: { relpath: filePath },
        responseType: 'blob', 
      });

      const blobData = response.data; 
      if (!blobData) {
        throw new Error('下载失败：未收到文件数据');
      }

      const url = window.URL.createObjectURL(blobData);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName || filePath.split('/').pop() || 'download');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(`Error downloading Thredds file ${filePath}:`, error);
      throw error; 
    }
  }

  /**
   * Convert an uploaded file to NetCDF format
   */
  async convertData(file: File, fileType: 'csv' | 'xlsx' | 'cnv'): Promise<ApiResponse<DataConversionResponse>> {
    if (USE_MOCK_DATA) {
      return { 
        data: { 
          netcdf_path: `converted/${file.name.replace(/\.[^/.]+$/, "")}.nc`,
          message: '转换成功' 
        } 
      };
    }
    
    try {
      return await apiClient.uploadFile<DataConversionResponse>(
        '/data/convert', 
        file, 
        'file', 
        { file_type: fileType }
      );
    } catch (error) {
      console.error("Error converting data:", error);
      return { error: error instanceof Error ? error.message : String(error) };
    }
  }

  /**
   * Retrieve OPeNDAP dataset information
   * @deprecated Use getOpendapMetadataByPath instead
   */
  async getOpenDAPData(datasetPath: string): Promise<ApiResponse<DatasetMetadata>> {
    if (USE_MOCK_DATA) {
      return { data: mockOpenDAPData };
    }
    
    try {
      return await apiClient.get<DatasetMetadata>('/opendap/open', { dataset_path: datasetPath });
    } catch (error) {
      console.error("Error fetching OPeNDAP data:", error);
      return { error: error instanceof Error ? error.message : String(error) };
    }
  }

  /**
   * Get OPeNDAP dataset metadata
   * @deprecated Use getOpendapMetadataByPath instead
   */
  async getOpenDAPMetadata(datasetPath: string): Promise<ApiResponse<DatasetMetadata>> {
    if (USE_MOCK_DATA) {
      return { data: mockOpenDAPData };
    }
    
    try {
      return await apiClient.get<DatasetMetadata>('/opendap/metadata', { dataset_path: datasetPath });
    } catch (error) {
      console.error("Error fetching OPeNDAP metadata:", error);
      return { error: error instanceof Error ? error.message : String(error) };
    }
  }

  /**
   * Get enhanced metadata for an OPeNDAP dataset by its relative path.
   * @param datasetPath The relative path to the dataset
   * @returns Enhanced metadata containing title, time range, spatial range, etc.
   */
  async getOpendapMetadataByPath(datasetPath: string): Promise<any> {
    if (!datasetPath) {
      console.error('getOpendapMetadataByPath called with empty datasetPath');
      return { error: '数据集路径不能为空' };
    }
    
    if (USE_MOCK_DATA) {
      // 返回示例元数据
      return {
        title: "daily mean fields from Global Ocean Physics Analysis and Forecast updated Daily",
        description: "No description available.",
        time_range: {
          start: "2024-07-11T00:00:00.000000000",
          end: "2024-07-31T00:00:00.000000000",
          count: 21
        },
        spatial_range: {
          latitude: {
            min: 12.25,
            max: 42.16667175292969,
            units: "degrees_north"
          },
          longitude: {
            min: 104.33334350585938,
            max: 132.91668701171875,
            units: "degrees_east"
          }
        },
        variables: [
          {
            name: "thetao",
            standard_name: "sea_water_potential_temperature",
            long_name: "Temperature",
            units: "degrees_C",
            dimensions: ["time", "depth", "latitude", "longitude"],
            shape: [21, 49, 360, 344]
          }
        ],
        source_information: {
          institution: "Mercator Ocean International",
          source: "MOI GLO12"
        },
        global_attributes: {
          "Conventions": "CF-1.8",
          "area": "Global",
          "institution": "Mercator Ocean International",
          "source": "MOI GLO12",
          "title": "daily mean fields from Global Ocean Physics Analysis and Forecast updated Daily"
        },
        dimensions: {
          depth: 49,
          latitude: 360,
          longitude: 344,
          time: 21
        }
      };
    }
    
    try {
      // 直接构造带查询参数的 URL
      const urlWithParams = `/opendap/metadata?dataset_path=${encodeURIComponent(datasetPath)}`;
      // 调用 apiClient.get 时不再传递第二个参数对象
      const response = await apiClient.get<any>(urlWithParams); 
      return response; 
    } catch (error: any) {
      console.error(`Error fetching OPeNDAP metadata for path ${datasetPath}:`, error);
      let serviceErrorMessage = '获取元数据时发生未知错误';
      if (error.response) {
        const { status, data } = error.response;
        const detail = data?.detail || data?.error || data?.message || '服务器未能处理请求';
        serviceErrorMessage = `服务器错误 ${status}: ${String(detail)}`.trim();
      } else if (error.request) {
        serviceErrorMessage = '服务器无响应，请检查网络或稍后再试';
      } else {
        serviceErrorMessage = error.message || '无法发送请求';
      }
      return { error: serviceErrorMessage };
    }
  }

  /**
   * Register a new dataset
   */
  async registerDataset(dataset: Omit<Dataset, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<{ id: string, message: string }>> {
    if (USE_MOCK_DATA) {
      return { 
        data: { 
          id: `mock-${Date.now()}`,
          message: '数据集注册成功' 
        } 
      };
    }
    
    try {
      return await apiClient.post<{ id: string, message: string }>('/datasets', dataset);
    } catch (error) {
      console.error("Error registering dataset:", error);
      return { error: error instanceof Error ? error.message : String(error) };
    }
  }

  /**
   * Get dataset details
   */
  async getDataset(id: string): Promise<ApiResponse<Dataset>> {
    if (USE_MOCK_DATA) {
      const dataset = mockDatasets.find(d => d.id === id);
      return { data: dataset || mockDatasets[0] };
    }
    
    try {
      return await apiClient.get<Dataset>(`/datasets/${id}`);
    } catch (error) {
      console.error("Error fetching dataset:", error);
      return { error: error instanceof Error ? error.message : String(error) };
    }
  }

  /**
   * Delete a dataset
   */
  async deleteDataset(id: string): Promise<ApiResponse<{ id: string, message: string }>> {
    if (USE_MOCK_DATA) {
      return { 
        data: { 
          id,
          message: '数据集已删除' 
        } 
      };
    }
    
    try {
      return await apiClient.delete<{ id: string, message: string }>(`/datasets/${id}`);
    } catch (error) {
      console.error("Error deleting dataset:", error);
      return { error: error instanceof Error ? error.message : String(error) };
    }
  }

  /**
   * Query a data subset
   */
  async queryDataSubset(query: {
    dataset_id: string;
    variables?: string[];
    spatial_range?: { lat: [number, number]; lon: [number, number] };
    time_range?: { start: string; end: string };
  }): Promise<ApiResponse<{ data: any[] }>> {
    if (USE_MOCK_DATA) {
      return { data: { data: [] } };
    }
    
    try {
      return await apiClient.post<{ data: any[] }>('/data/query', query);
    } catch (error) {
      console.error("Error querying data subset:", error);
      return { data: { data: [] }, error: error instanceof Error ? error.message : String(error) };
    }
  }

  /**
   * List all registered datasets
   */
  async getAllDatasets(): Promise<ApiResponse<Dataset[]>> {
    if (USE_MOCK_DATA) {
      return { data: mockDatasets };
    }
    
    try {
      return await apiClient.get<Dataset[]>('/datasets');
    } catch (error) {
      console.error("Error fetching all datasets:", error);
      return { data: [], error: error instanceof Error ? error.message : String(error) };
    }
  }

  /**
   * Upload a data file.
   */
  async uploadFile(file: File, metadata: Record<string, any>): Promise<ApiResponse<FileUploadResponse>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));

    try {
      const response = await apiClient.post<FileUploadResponse>('/data/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      if (response.data) return response;
      throw new Error((response as ApiResponse<any>).error || '上传文件失败，未收到有效响应数据');
    } catch (error) {
      console.error('Error uploading file:', error);
      return { error: this.formatErrorMessage(error, '上传文件失败') };
    }
  }

  // Fusion Task Methods
  async createFusionTask(taskData: FusionTaskRequest): Promise<ApiResponse<FusionTaskResponse>> {
    try {
      const response = await apiClient.post<FusionTaskResponse>('/fusion/tasks', taskData);
      if (response.data) return response;
      throw new Error((response as ApiResponse<any>).error || '创建融合任务失败');
    } catch (error) {
      console.error('Error creating fusion task:', error);
      return { error: this.formatErrorMessage(error, '创建融合任务失败') };
    }
  }

  async getFusionTaskStatus(taskId: string): Promise<ApiResponse<TaskStatus>> {
    try {
      const response = await apiClient.get<TaskStatus>(`/fusion/tasks/${taskId}/status`);
      if (response.data) return response;
      throw new Error((response as ApiResponse<any>).error || '获取任务状态失败');
    } catch (error) {
      console.error(`Error fetching status for task ${taskId}:`, error);
      return { error: this.formatErrorMessage(error, '获取任务状态失败') };
    }
  }

  async getFusionTaskResult(taskId: string): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.get<any>(`/fusion/tasks/${taskId}/result`);
      return { data: response.data || response };
    } catch (error) {
      console.error(`Error fetching result for task ${taskId}:`, error);
      return { error: this.formatErrorMessage(error, '获取任务结果失败') };
    }
  }
  
  async listFusionTasks(): Promise<ApiResponse<FusionTaskResponse[]>> {
    try {
      const response = await apiClient.get<FusionTaskResponse[]>('/fusion/tasks');
      if (response.data) return { data: response.data };
      throw new Error((response as ApiResponse<any>).error || '获取融合任务列表失败');
    } catch (error) {
      console.error('Error listing fusion tasks:', error);
      return { error: this.formatErrorMessage(error, '获取融合任务列表失败') };
    }
  }

  // Helper to format error messages consistently
  private formatErrorMessage(error: any, defaultMessage: string): string {
    if (error.response) { // Axios error structure for HTTP errors
      const { status, data } = error.response;
      const detail = data?.detail || data?.error || data?.message || defaultMessage;
      return `服务器错误 ${status}: ${String(detail)}`.trim();
    } else if (error.request) { // Network error
      return '服务器无响应，请检查网络或稍后再试';
    } else { // Other errors (e.g., setup error, or error already a string/object with message)
      return error.message || String(error) || defaultMessage;
    }
  }
}

// Export a singleton instance of the service
export const dataService = DataService.getInstance();