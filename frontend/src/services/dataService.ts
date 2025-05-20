import apiClient from './apiClient';
import { 
  ApiResponse,
  DatasetMetadata, 
  Dataset,
  DataConversionResponse,
  FileUploadResponse
} from '../types/api';
import { mockDatasets, mockOpenDAPData } from '../mocks/mockData';

// 检查是否使用模拟数据（开发环境使用模拟数据）
const USE_MOCK_DATA = true;

/**
 * DataService - handles all data-related API calls
 */
class DataService {
  /**
   * Get a list of data files
   */
  async getDataList(ext?: string): Promise<ApiResponse<string[]>> {
    if (USE_MOCK_DATA) {
      return { data: mockDatasets.map(d => d.file_location) };
    }
    return apiClient.get<string[]>('/data/list', { ext });
  }

  /**
   * Get metadata for a specific data file
   */
  async getDataMetadata(relpath: string): Promise<ApiResponse<DatasetMetadata>> {
    if (USE_MOCK_DATA) {
      return { data: mockOpenDAPData };
    }
    return apiClient.get<DatasetMetadata>('/data/metadata', { relpath });
  }

  /**
   * Download a data file
   */
  async downloadDataFile(relpath: string, filename: string): Promise<string | null> {
    if (USE_MOCK_DATA) {
      console.log(`Mocked download of file: ${relpath} as ${filename}`);
      return null;
    }
    return apiClient.downloadFile('/data/download', filename, { relpath });
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
    return apiClient.uploadFile<DataConversionResponse>(
      '/data/convert', 
      file, 
      'file', 
      { file_type: fileType }
    );
  }

  /**
   * Retrieve OPeNDAP dataset information
   */
  async getOpenDAPData(datasetPath: string): Promise<ApiResponse<DatasetMetadata>> {
    if (USE_MOCK_DATA) {
      return { data: mockOpenDAPData };
    }
    return apiClient.get<DatasetMetadata>('/opendap/open', { dataset_path: datasetPath });
  }

  /**
   * Get OPeNDAP dataset metadata
   */
  async getOpenDAPMetadata(datasetPath: string): Promise<ApiResponse<DatasetMetadata>> {
    if (USE_MOCK_DATA) {
      return { data: mockOpenDAPData };
    }
    return apiClient.get<DatasetMetadata>('/opendap/metadata', { dataset_path: datasetPath });
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
    return apiClient.post<{ id: string, message: string }>('/datasets', dataset);
  }

  /**
   * Get dataset details
   */
  async getDataset(id: string): Promise<ApiResponse<Dataset>> {
    if (USE_MOCK_DATA) {
      const dataset = mockDatasets.find(d => d.id === id);
      return { data: dataset || mockDatasets[0] };
    }
    return apiClient.get<Dataset>(`/datasets/${id}`);
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
    return apiClient.delete<{ id: string, message: string }>(`/datasets/${id}`);
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
    return apiClient.post<{ data: any[] }>('/data/query', query);
  }

  /**
   * List all registered datasets
   */
  async getAllDatasets(): Promise<ApiResponse<Dataset[]>> {
    if (USE_MOCK_DATA) {
      return { data: mockDatasets };
    }
    return apiClient.get<Dataset[]>('/datasets');
  }
}

const dataService = new DataService();
export default dataService;
