import apiClient from './apiClient';
import { 
  ApiResponse,
  ClineDetectionParams,
  ClineDetectionResult,
  EddyDetectionParams,
  EddyDetectionResult,
  FrontDetectionParams,
  FrontDetectionResult,
  TaskStatus
} from '../types/api';

/**
 * DiagnosticsService - handles all diagnostic algorithm related API calls
 */
class DiagnosticsService {
  /**
   * Detect cline (thermocline, pycnocline, sound speed cline) from a profile
   */
  async detectCline(params: ClineDetectionParams): Promise<ApiResponse<ClineDetectionResult>> {
    return apiClient.post<ClineDetectionResult>('/diagnostics/cline/detect', params);
  }

  /**
   * Detect eddies from SSH (Sea Surface Height) data
   */
  async detectEddies(params: EddyDetectionParams): Promise<ApiResponse<EddyDetectionResult>> {
    return apiClient.post<EddyDetectionResult>('/diagnostics/eddy/detect', params);
  }

  /**
   * Detect fronts from SST (Sea Surface Temperature) data
   */
  async detectFronts(params: FrontDetectionParams): Promise<ApiResponse<FrontDetectionResult>> {
    return apiClient.post<FrontDetectionResult>('/diagnostics/front/detect', params);
  }

  /**
   * Get available diagnostic algorithms
   */
  async getDiagnosticAlgorithms(): Promise<ApiResponse<{ id: string, name: string, description: string }[]>> {
    return apiClient.get<{ id: string, name: string, description: string }[]>('/diagnostics/algorithms');
  }

  /**
   * Get details for a specific diagnostic algorithm
   */
  async getDiagnosticAlgorithmDetails(id: string): Promise<ApiResponse<{ id: string, name: string, description: string }>> {
    return apiClient.get<{ id: string, name: string, description: string }>(`/diagnostics/algorithms/${id}`);
  }

  /**
   * Get parameters for a diagnostic algorithm
   */
  async getDiagnosticAlgorithmParameters(id: string): Promise<ApiResponse<any>> {
    return apiClient.get<any>(`/diagnostics/algorithms/${id}/parameters`);
  }

  /**
   * Create a diagnostic task
   */
  async createDiagnosticTask(algorithmId: string, parameters: any, datasetId: string): Promise<ApiResponse<{ task_id: string, status: string }>> {
    return apiClient.post<{ task_id: string, status: string }>('/diagnostics/tasks', {
      algorithm_id: algorithmId,
      parameters,
      dataset_id: datasetId
    });
  }

  /**
   * Get a list of diagnostic tasks
   */
  async getDiagnosticTasks(): Promise<ApiResponse<TaskStatus[]>> {
    return apiClient.get<TaskStatus[]>('/diagnostics/tasks');
  }

  /**
   * Get details of a specific diagnostic task
   */
  async getDiagnosticTaskDetails(id: string): Promise<ApiResponse<TaskStatus>> {
    return apiClient.get<TaskStatus>(`/diagnostics/tasks/${id}`);
  }

  /**
   * Get results of a diagnostic task
   */
  async getDiagnosticTaskResults(id: string): Promise<ApiResponse<any>> {
    return apiClient.get<any>(`/diagnostics/tasks/${id}/results`);
  }

  /**
   * Run specialized thermocline diagnosis
   */
  async runThermoclineDiagnosis(params: any): Promise<ApiResponse<any>> {
    return apiClient.post<any>('/diagnostics/thermocline', params);
  }

  /**
   * Run specialized eddy diagnosis
   */
  async runEddyDiagnosis(params: any): Promise<ApiResponse<any>> {
    return apiClient.post<any>('/diagnostics/eddy', params);
  }

  /**
   * Run specialized front diagnosis
   */
  async runFrontDiagnosis(params: any): Promise<ApiResponse<any>> {
    return apiClient.post<any>('/diagnostics/front', params);
  }
}

const diagnosticsService = new DiagnosticsService();
export default diagnosticsService;
