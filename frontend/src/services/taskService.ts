import apiClient from './apiClient';
import { ApiResponse, TaskStatus } from '../types/api';

/**
 * TaskService - centralized service for managing different types of tasks
 */
class TaskService {
  /**
   * Get a list of all tasks
   */
  async getTasks(params?: { 
    status?: string, 
    type?: string, 
    page?: number, 
    limit?: number 
  }): Promise<ApiResponse<TaskStatus[]>> {
    return apiClient.get<TaskStatus[]>('/tasks', params);
  }

  /**
   * Get task details
   */
  async getTaskDetails(id: string): Promise<ApiResponse<TaskStatus>> {
    return apiClient.get<TaskStatus>(`/tasks/${id}`);
  }

  /**
   * Cancel a running task
   */
  async cancelTask(id: string): Promise<ApiResponse<{ id: string, status: string }>> {
    return apiClient.put<{ id: string, status: string }>(`/tasks/${id}/cancel`);
  }

  /**
   * Get task status
   */
  async getTaskStatus(id: string): Promise<ApiResponse<{ status: string, progress: number }>> {
    return apiClient.get<{ status: string, progress: number }>(`/tasks/${id}/status`);
  }

  /**
   * Get scheduled tasks
   */
  async getScheduledTasks(): Promise<ApiResponse<TaskStatus[]>> {
    return apiClient.get<TaskStatus[]>('/tasks/scheduled');
  }

  /**
   * Poll task status until completion or failure
   * @param id Task ID
   * @param onStatusChange Callback for status updates
   * @param intervalMs Polling interval in milliseconds
   * @param timeoutMs Maximum time to poll in milliseconds
   */
  async pollTaskUntilCompletion(
    id: string,
    onStatusChange?: (status: { status: string, progress: number }) => void,
    intervalMs: number = 2000,
    timeoutMs: number = 1000 * 60 * 30 // 30 minutes default timeout
  ): Promise<ApiResponse<TaskStatus>> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      let intervalId: number | undefined;

      const checkStatus = async () => {
        try {
          const response = await this.getTaskStatus(id);
          
          if (response.error) {
            clearInterval(intervalId);
            reject(new Error(response.error));
            return;
          }

          const status = response.data;
          
          if (onStatusChange && status) {
            onStatusChange(status);
          }

          if (status && ['finished', 'failed', 'cancelled'].includes(status.status)) {
            clearInterval(intervalId);
            const fullTaskDetails = await this.getTaskDetails(id);
            resolve(fullTaskDetails);
            return;
          }

          // Check for timeout
          if (Date.now() - startTime > timeoutMs) {
            clearInterval(intervalId);
            reject(new Error(`Task polling timed out after ${timeoutMs / 1000} seconds`));
            return;
          }
        } catch (error) {
          console.error('Error polling task status:', error);
          // Don't stop polling on network errors, try again
        }
      };

      // Start polling
      checkStatus(); // Check immediately
      intervalId = window.setInterval(checkStatus, intervalMs);
    });
  }
}

const taskService = new TaskService();
export default taskService;
