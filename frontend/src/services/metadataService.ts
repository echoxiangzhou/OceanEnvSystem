/**
 * 元数据服务
 * 提供NetCDF文件元数据的查询、列表、统计等功能
 */

import apiClient from './apiClient';

// 元数据响应类型
export interface MetadataItem {
  id: number;
  file_name: string;
  file_path: string;
  file_size?: number;
  cf_version?: string;
  is_cf_compliant: boolean;
  title?: string;
  summary?: string;
  institution?: string;
  source?: string;
  time_coverage_start?: string;
  time_coverage_end?: string;
  geospatial_lat_min?: number;
  geospatial_lat_max?: number;
  geospatial_lon_min?: number;
  geospatial_lon_max?: number;
  geospatial_vertical_min?: number;
  geospatial_vertical_max?: number;
  variables?: Record<string, any>;
  dimensions?: Record<string, any>;
  processing_status: string;
  created_at: string;
  updated_at: string;
}

export interface MetadataListResponse {
  total: number;
  items: MetadataItem[];
  page: number;
  size: number;
}

export interface MetadataStatsResponse {
  total_files: number;
  cf_compliant_files: number;
  processing_status_counts: Record<string, number>;
  file_size_stats: {
    average: number;
    total: number;
    minimum: number;
    maximum: number;
  };
  institution_counts: Record<string, number>;
}

export interface MetadataListParams {
  page?: number;
  size?: number;
  processing_status?: string;
  is_cf_compliant?: boolean;
  institution?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

class MetadataService {
  private baseUrl = '/metadata';

  /**
   * 获取元数据列表
   */
  async getMetadataList(params: MetadataListParams = {}): Promise<MetadataListResponse> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.size) queryParams.append('size', params.size.toString());
      if (params.processing_status) queryParams.append('processing_status', params.processing_status);
      if (params.is_cf_compliant !== undefined) queryParams.append('is_cf_compliant', params.is_cf_compliant.toString());
      if (params.institution) queryParams.append('institution', params.institution);
      if (params.search) queryParams.append('search', params.search);
      if (params.sort_by) queryParams.append('sort_by', params.sort_by);
      if (params.sort_order) queryParams.append('sort_order', params.sort_order);

      const url = `${this.baseUrl}/list${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await apiClient.get(url);
      return response.data;
    } catch (error) {
      console.error('获取元数据列表失败:', error);
      throw error;
    }
  }

  /**
   * 获取单个元数据详情
   */
  async getMetadataDetail(metadataId: number): Promise<MetadataItem> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/detail/${metadataId}`);
      return response.data;
    } catch (error) {
      console.error('获取元数据详情失败:', error);
      throw error;
    }
  }

  /**
   * 获取元数据统计信息
   */
  async getMetadataStats(): Promise<MetadataStatsResponse> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/stats`);
      return response.data;
    } catch (error) {
      console.error('获取元数据统计失败:', error);
      throw error;
    }
  }

  /**
   * 手动提取文件元数据
   */
  async extractMetadata(filePath: string, processingStatus: string = 'standard'): Promise<any> {
    try {
      const response = await apiClient.post(`${this.baseUrl}/extract/${encodeURIComponent(filePath)}`, null, {
        params: { processing_status: processingStatus }
      });
      return response.data;
    } catch (error) {
      console.error('提取元数据失败:', error);
      throw error;
    }
  }

  /**
   * 删除元数据记录
   */
  async deleteMetadata(metadataId: number): Promise<any> {
    try {
      const response = await apiClient.delete(`${this.baseUrl}/delete/${metadataId}`);
      return response.data;
    } catch (error) {
      console.error('删除元数据失败:', error);
      throw error;
    }
  }

  /**
   * 获取所有唯一变量名
   */
  async getUniqueVariables(): Promise<string[]> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/variables`);
      return response.data.variables;
    } catch (error) {
      console.error('获取变量列表失败:', error);
      throw error;
    }
  }

  /**
   * 获取所有唯一机构名
   */
  async getUniqueInstitutions(): Promise<string[]> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/institutions`);
      return response.data.institutions;
    } catch (error) {
      console.error('获取机构列表失败:', error);
      throw error;
    }
  }
}

export const metadataService = new MetadataService();
export default metadataService; 