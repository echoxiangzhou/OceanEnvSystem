import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { taskService } from '../services';
import { ApiResponse, TaskStatus } from '../types/api';

/**
 * Custom hook for fetching all tasks
 */
export const useTasks = (params?: { 
  status?: string, 
  type?: string, 
  page?: number, 
  limit?: number 
}, options?: UseQueryOptions<ApiResponse<TaskStatus[]>, Error>) => {
  return useQuery<ApiResponse<TaskStatus[]>, Error>({
    queryKey: ['tasks', params],
    queryFn: () => taskService.getTasks(params),
    ...options
  });
};

/**
 * Custom hook for fetching task details
 */
export const useTaskDetails = (id: string, options?: UseQueryOptions<ApiResponse<TaskStatus>, Error>) => {
  return useQuery<ApiResponse<TaskStatus>, Error>({
    queryKey: ['taskDetails', id],
    queryFn: () => taskService.getTaskDetails(id),
    enabled: !!id,
    ...options
  });
};

/**
 * Custom hook for canceling a task
 */
export const useCancelTask = (options?: UseMutationOptions<
  ApiResponse<{ id: string, status: string }>,
  Error,
  string
>) => {
  const queryClient = useQueryClient();
  
  return useMutation<
    ApiResponse<{ id: string, status: string }>,
    Error,
    string
  >({
    mutationFn: (id) => taskService.cancelTask(id),
    onSuccess: (_, id) => {
      // Invalidate tasks query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      // Invalidate the specific task details
      queryClient.invalidateQueries({ queryKey: ['taskDetails', id] });
      // Invalidate task status
      queryClient.invalidateQueries({ queryKey: ['taskStatus', id] });
    },
    ...options
  });
};

/**
 * Custom hook for fetching task status with polling
 */
export const useTaskStatus = (id: string, pollInterval: number = 2000, options?: UseQueryOptions<ApiResponse<{ status: string, progress: number }>, Error>) => {
  return useQuery<ApiResponse<{ status: string, progress: number }>, Error>({
    queryKey: ['taskStatus', id],
    queryFn: () => taskService.getTaskStatus(id),
    enabled: !!id,
    // Enable polling if task is not in a terminal state
    refetchInterval: (data) => {
      if (!data?.data || ['finished', 'failed', 'cancelled'].includes(data.data.status)) {
        return false; // Stop polling
      }
      return pollInterval; // Continue polling
    },
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    ...options
  });
};

/**
 * Custom hook for fetching scheduled tasks
 */
export const useScheduledTasks = (options?: UseQueryOptions<ApiResponse<TaskStatus[]>, Error>) => {
  return useQuery<ApiResponse<TaskStatus[]>, Error>({
    queryKey: ['scheduledTasks'],
    queryFn: () => taskService.getScheduledTasks(),
    ...options
  });
};

/**
 * Custom hook for polling a task until completion
 */
export const usePollTask = (options?: UseMutationOptions<
  ApiResponse<TaskStatus>,
  Error,
  {
    id: string,
    onStatusChange?: (status: { status: string, progress: number }) => void,
    intervalMs?: number,
    timeoutMs?: number
  }
>) => {
  return useMutation<
    ApiResponse<TaskStatus>,
    Error,
    {
      id: string,
      onStatusChange?: (status: { status: string, progress: number }) => void,
      intervalMs?: number,
      timeoutMs?: number
    }
  >({
    mutationFn: ({ id, onStatusChange, intervalMs, timeoutMs }) => 
      taskService.pollTaskUntilCompletion(id, onStatusChange, intervalMs, timeoutMs),
    ...options
  });
};
