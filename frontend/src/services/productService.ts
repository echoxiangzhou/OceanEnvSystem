import apiClient from './apiClient';
import { 
  ApiResponse,
  ProductGenerationRequest,
  ProductGenerationResponse
} from '../types/api';

/**
 * ProductService - handles all product generation related API calls
 */
class ProductService {
  /**
   * Generate a report based on the provided configuration
   */
  async generateReport(config: ProductGenerationRequest['config']): Promise<ApiResponse<ProductGenerationResponse>> {
    return apiClient.post<ProductGenerationResponse>('/products/generate', { config });
  }

  /**
   * Get available report templates
   */
  async getReportTemplates(): Promise<ApiResponse<{ id: string, name: string, description: string }[]>> {
    return apiClient.get<{ id: string, name: string, description: string }[]>('/products/reports/templates');
  }

  /**
   * Generate a specific report
   */
  async createReport(templateId: string, parameters: any, sourceResults: string[]): Promise<ApiResponse<{ id: string, file_location: string }>> {
    return apiClient.post<{ id: string, file_location: string }>('/products/reports', {
      template_id: templateId,
      parameters,
      source_results: sourceResults
    });
  }

  /**
   * Get a list of generated reports
   */
  async getReports(): Promise<ApiResponse<{ id: string, name: string, description: string, file_location: string, created_at: string }[]>> {
    return apiClient.get<{ id: string, name: string, description: string, file_location: string, created_at: string }[]>('/products/reports');
  }

  /**
   * Get details of a specific report
   */
  async getReportDetails(id: string): Promise<ApiResponse<{ id: string, name: string, description: string, file_location: string, created_at: string }>> {
    return apiClient.get<{ id: string, name: string, description: string, file_location: string, created_at: string }>(`/products/reports/${id}`);
  }

  /**
   * Download a report file
   */
  async downloadReport(id: string, filename: string): Promise<string | null> {
    return apiClient.downloadFile(`/products/reports/${id}/download`, filename);
  }

  /**
   * Create a visualization
   */
  async createVisualization(type: string, datasetId: string, parameters: any): Promise<ApiResponse<{ id: string, image_location: string }>> {
    return apiClient.post<{ id: string, image_location: string }>('/products/visualizations', {
      type,
      dataset_id: datasetId,
      parameters
    });
  }

  /**
   * Get a list of visualizations
   */
  async getVisualizations(): Promise<ApiResponse<{ id: string, name: string, description: string, type: string, image_location: string }[]>> {
    return apiClient.get<{ id: string, name: string, description: string, type: string, image_location: string }[]>('/products/visualizations');
  }

  /**
   * Get details of a specific visualization
   */
  async getVisualizationDetails(id: string): Promise<ApiResponse<{ id: string, name: string, description: string, type: string, image_location: string }>> {
    return apiClient.get<{ id: string, name: string, description: string, type: string, image_location: string }>(`/products/visualizations/${id}`);
  }

  /**
   * Export a visualization
   */
  async exportVisualization(id: string, format: 'png' | 'jpg' | 'svg' | 'pdf'): Promise<string | null> {
    return apiClient.downloadFile(`/products/visualizations/${id}/export`, `visualization.${format}`, { format });
  }
}

const productService = new ProductService();
export default productService;
