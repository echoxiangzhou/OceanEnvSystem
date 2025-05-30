import apiClient from './apiClient';

export interface FileUploadResponse {
  temp_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  file_path: string;
  upload_time: string;
  parse_status: 'success' | 'warning' | 'error';
  parse_message: string;
  db_record_id: number;
}

export interface DataPreview {
  temp_id: string;
  row_count: number;
  column_count: number;
  columns: Array<{
    name: string;
    data_type: string;
    sample_values: string[];
    missing_count: number;
    total_count: number;
    suggested_cf_name?: string;
    suggested_units?: string;
    confidence: number;
    description?: string;
  }>;
  preview_data: Array<Record<string, any>>;
  parsing_config: {
    file_format: string;
    instrument_type?: string;
    data_start_line?: number;
    bad_flag?: number;
  };
  quality_report: {
    total_rows: number;
    total_columns: number;
    missing_data_percentage: number;
    data_types_detected: Record<string, number>;
    anomalies: Record<string, string[]>;
  };
}

export interface MetadataConfig {
  temp_id: string;
  variables: Record<string, {
    standard_name?: string;
    long_name?: string;
    units?: string;
    description?: string;
  }>;
  global_attributes: Record<string, string>;
  coordinate_variables: Record<string, string>;
}

export interface ValidationResult {
  temp_id: string;
  is_valid: boolean;
  cf_version: string;
  total_issues: number;
  error_count: number;
  warning_count: number;
  info_count: number;
  issues: Array<{
    level: 'error' | 'warning' | 'info';
    code: string;
    message: string;
    location: string;
    suggestion?: string;
  }>;
  compliance_score: number;
}

export interface ConversionResult {
  temp_id: string;
  success: boolean;
  output_path: string;
  tds_url: string;
  opendap_url: string;
  file_size: number;
  processing_time: number;
  message: string;
  metadata_extracted: boolean;
  metadata_record_id?: number;
}

class ImportService {
  /**
   * 上传文件
   */
  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<FileUploadResponse>(
      '/data/import/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }

  /**
   * 获取数据预览
   */
  async getDataPreview(tempId: string): Promise<DataPreview> {
    const response = await apiClient.get<DataPreview>(
      `/data/import/preview/${tempId}`
    );
    return response.data;
  }

  /**
   * 获取元数据配置
   */
  async getMetadataConfig(tempId: string): Promise<MetadataConfig> {
    const response = await apiClient.get<MetadataConfig>(
      `/data/import/metadata/${tempId}`
    );
    return response.data;
  }

  /**
   * 更新元数据配置
   */
  async updateMetadataConfig(tempId: string, config: Partial<MetadataConfig>): Promise<void> {
    await apiClient.put(`/data/import/metadata/${tempId}`, config);
  }

  /**
   * 验证数据
   */
  async validateData(tempId: string): Promise<ValidationResult> {
    const response = await apiClient.post<ValidationResult>(
      `/data/import/validate/${tempId}`
    );
    return response.data;
  }

  /**
   * 转换为NetCDF
   */
  async convertToNetCDF(tempId: string): Promise<ConversionResult> {
    const response = await apiClient.post<ConversionResult>(
      `/data/import/convert/${tempId}`
    );
    return response.data;
  }
}

export const importService = new ImportService();
export default importService; 