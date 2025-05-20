import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { fusionService } from '../services';
import { 
  ApiResponse, 
  OptimalInterpolationParams, 
  OptimalInterpolationResult,
  KalmanFilterParams,
  KalmanFilterResult,
  FusionTaskRequest,
  FusionTaskResponse,
  TaskStatus
} from '../types/api';

/**
 * Custom hook for fetching fusion algorithms
 */
export const useFusionAlgorithms = (options?: UseQueryOptions<ApiResponse<{ id: string, name: string, description: string }[]>, Error>) => {
  return useQuery<ApiResponse<{ id: string, name: string, description: string }[]>, Error>({
    queryKey: ['fusionAlgorithms'],
    queryFn: () => fusionService.getFusionAlgorithms(),
    ...options
  });
};

/**
 * Custom hook for fetching fusion algorithm details
 */
export const useFusionAlgorithmDetails = (id: string, options?: UseQueryOptions<ApiResponse<{ id: string, name: string, description: string, parameters: any }>, Error>) => {
  return useQuery<ApiResponse<{ id: string, name: string, description: string, parameters: any }>, Error>({
    queryKey: ['fusionAlgorithmDetails', id],
    queryFn: () => fusionService.getFusionAlgorithmDetails(id),
    enabled: !!id,
    ...options
  });
};

/**
 * Custom hook for running optimal interpolation
 */
export const useOptimalInterpolation = (options?: UseMutationOptions<
  ApiResponse<OptimalInterpolationResult>,
  Error,
  OptimalInterpolationParams
>) => {
  return useMutation<
    ApiResponse<OptimalInterpolationResult>,
    Error,
    OptimalInterpolationParams
  >({
    mutationFn: (params) => fusionService.runOptimalInterpolation(params),
    ...options
  });
};

/**
 * Custom hook for running Kalman filter
 */
export const useKalmanFilter = (options?: UseMutationOptions<
  ApiResponse<KalmanFilterResult>,
  Error,
  KalmanFilterParams
>) => {
  return useMutation<
    ApiResponse<KalmanFilterResult>,
    Error,
    KalmanFilterParams
  >({
    mutationFn: (params) => fusionService.runKalmanFilter(params),
    ...options
  });
};

/**
 * Custom hook for running any fusion algorithm
 */
export const useRunFusion = <T,>(options?: UseMutationOptions<
  ApiResponse<T>,
  Error,
  FusionTaskRequest
>) => {
  return useMutation<
    ApiResponse<T>,
    Error,
    FusionTaskRequest
  >({
    mutationFn: (request) => fusionService.runFusion<T>(request),
    ...options
  });
};

/**
 * Custom hook for creating asynchronous fusion tasks
 */
export const useCreateFusionTask = (options?: UseMutationOptions<
  ApiResponse<FusionTaskResponse>,
  Error,
  FusionTaskRequest
>) => {
  const queryClient = useQueryClient();
  
  return useMutation<
    ApiResponse<FusionTaskResponse>,
    Error,
    FusionTaskRequest
  >({
    mutationFn: (request) => fusionService.createAsyncFusionTask(request),
    onSuccess: () => {
      // Invalidate fusion tasks query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['fusionTasks'] });
    },
    ...options
  });
};

/**
 * Custom hook for fetching fusion task status
 */
export const useFusionTaskStatus = (taskId: string, 
  options?: UseQueryOptions<ApiResponse<TaskStatus>, Error> & { pollInterval?: number }
) => {
  const { pollInterval = 0, ...queryOptions } = options || {};
  
  return useQuery<ApiResponse<TaskStatus>, Error>({
    queryKey: ['fusionTaskStatus', taskId],
    queryFn: () => fusionService.getFusionTaskStatus(taskId),
    enabled: !!taskId,
    // Enable polling if pollInterval is provided
    refetchInterval: pollInterval > 0 ? pollInterval : undefined,
    // Stop polling when task is completed
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    ...queryOptions
  });
};

/**
 * Custom hook for canceling a fusion task
 */
export const useCancelFusionTask = (options?: UseMutationOptions<
  ApiResponse<{ task_id: string; status: string }>,
  Error,
  string
>) => {
  const queryClient = useQueryClient();
  
  return useMutation<
    ApiResponse<{ task_id: string; status: string }>,
    Error,
    string
  >({
    mutationFn: (taskId) => fusionService.cancelFusionTask(taskId),
    onSuccess: (_, taskId) => {
      // Invalidate fusion tasks query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['fusionTasks'] });
      // Invalidate the specific task status
      queryClient.invalidateQueries({ queryKey: ['fusionTaskStatus', taskId] });
    },
    ...options
  });
};

/**
 * Custom hook for fetching fusion tasks
 */
export const useFusionTasks = (
  status?: string, 
  limit: number = 20, 
  options?: UseQueryOptions<ApiResponse<TaskStatus[]>, Error>
) => {
  return useQuery<ApiResponse<TaskStatus[]>, Error>({
    queryKey: ['fusionTasks', status, limit],
    queryFn: () => fusionService.getFusionTasks(status, limit),
    ...options
  });
};
