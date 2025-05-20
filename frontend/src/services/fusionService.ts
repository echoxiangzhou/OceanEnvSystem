import apiClient from './apiClient';
import { 
  ApiResponse,
  OptimalInterpolationParams,
  OptimalInterpolationResult,
  KalmanFilterParams,
  KalmanFilterResult,
  FusionTaskRequest,
  FusionTaskResponse,
  TaskStatus,
  FusionTask
} from '../types/api';

/**
 * FusionService - handles all data fusion related API calls
 */
class FusionService {
  /**
   * Run optimal interpolation algorithm
   */
  async runOptimalInterpolation(params: OptimalInterpolationParams): Promise<ApiResponse<OptimalInterpolationResult>> {
    return apiClient.post<OptimalInterpolationResult>('/fusion/oi/run', params);
  }

  /**
   * Run Kalman filter algorithm
   */
  async runKalmanFilter(params: KalmanFilterParams): Promise<ApiResponse<KalmanFilterResult>> {
    return apiClient.post<KalmanFilterResult>('/fusion/kalman/run', params);
  }

  /**
   * Run a fusion algorithm
   */
  async runFusion<T>(request: FusionTaskRequest): Promise<ApiResponse<T>> {
    return apiClient.post<T>('/fusion/run', request);
  }

  /**
   * Create an asynchronous fusion task
   */
  async createAsyncFusionTask(request: FusionTaskRequest): Promise<ApiResponse<FusionTaskResponse>> {
    return apiClient.post<FusionTaskResponse>('/fusion/run_async', request);
  }

  /**
   * Get the status of a fusion task
   */
  async getFusionTaskStatus(taskId: string): Promise<ApiResponse<TaskStatus>> {
    return apiClient.get<TaskStatus>(`/fusion/task_status/${taskId}`);
  }

  /**
   * Cancel or delete a fusion task
   */
  async cancelFusionTask(taskId: string): Promise<ApiResponse<{ task_id: string; status: string }>> {
    return apiClient.delete<{ task_id: string; status: string }>(`/fusion/task/${taskId}`);
  }

  /**
   * Get a list of fusion tasks
   */
  async getFusionTasks(status?: string, limit: number = 20): Promise<ApiResponse<TaskStatus[]>> {
    return apiClient.get<TaskStatus[]>('/fusion/tasks', { status, limit });
  }
  
  /**
   * Get available fusion algorithms
   */
  async getFusionAlgorithms(): Promise<ApiResponse<{ id: string, name: string, description: string }[]>> {
    return apiClient.get<{ id: string, name: string, description: string }[]>('/fusion/algorithms');
  }
  
  /**
   * Get details of a specific fusion algorithm
   */
  async getFusionAlgorithmDetails(id: string): Promise<ApiResponse<{ id: string, name: string, description: string, parameters: any }>> {
    return apiClient.get<{ id: string, name: string, description: string, parameters: any }>(`/fusion/algorithms/${id}`);
  }
  
  /**
   * Validate fusion parameters
   */
  async validateFusionParameters(algorithmId: string, parameters: any): Promise<ApiResponse<{ valid: boolean, errors?: string[] }>> {
    return apiClient.post<{ valid: boolean, errors?: string[] }>('/fusion/validate', { algorithm_id: algorithmId, parameters });
  }
}

const fusionService = new FusionService();
export default fusionService;
