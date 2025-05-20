import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { diagnosticsService } from '../services';
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
 * Custom hook for fetching diagnostic algorithms
 */
export const useDiagnosticAlgorithms = (options?: UseQueryOptions<ApiResponse<{ id: string, name: string, description: string }[]>, Error>) => {
  return useQuery<ApiResponse<{ id: string, name: string, description: string }[]>, Error>({
    queryKey: ['diagnosticAlgorithms'],
    queryFn: () => diagnosticsService.getDiagnosticAlgorithms(),
    ...options
  });
};

/**
 * Custom hook for fetching diagnostic algorithm details
 */
export const useDiagnosticAlgorithmDetails = (id: string, options?: UseQueryOptions<ApiResponse<{ id: string, name: string, description: string }>, Error>) => {
  return useQuery<ApiResponse<{ id: string, name: string, description: string }>, Error>({
    queryKey: ['diagnosticAlgorithmDetails', id],
    queryFn: () => diagnosticsService.getDiagnosticAlgorithmDetails(id),
    enabled: !!id,
    ...options
  });
};

/**
 * Custom hook for fetching diagnostic algorithm parameters
 */
export const useDiagnosticAlgorithmParameters = (id: string, options?: UseQueryOptions<ApiResponse<any>, Error>) => {
  return useQuery<ApiResponse<any>, Error>({
    queryKey: ['diagnosticAlgorithmParameters', id],
    queryFn: () => diagnosticsService.getDiagnosticAlgorithmParameters(id),
    enabled: !!id,
    ...options
  });
};

/**
 * Custom hook for cline detection
 */
export const useClineDetection = (options?: UseMutationOptions<
  ApiResponse<ClineDetectionResult>,
  Error,
  ClineDetectionParams
>) => {
  return useMutation<
    ApiResponse<ClineDetectionResult>,
    Error,
    ClineDetectionParams
  >({
    mutationFn: (params) => diagnosticsService.detectCline(params),
    ...options
  });
};

/**
 * Custom hook for eddy detection
 */
export const useEddyDetection = (options?: UseMutationOptions<
  ApiResponse<EddyDetectionResult>,
  Error,
  EddyDetectionParams
>) => {
  return useMutation<
    ApiResponse<EddyDetectionResult>,
    Error,
    EddyDetectionParams
  >({
    mutationFn: (params) => diagnosticsService.detectEddies(params),
    ...options
  });
};

/**
 * Custom hook for front detection
 */
export const useFrontDetection = (options?: UseMutationOptions<
  ApiResponse<FrontDetectionResult>,
  Error,
  FrontDetectionParams
>) => {
  return useMutation<
    ApiResponse<FrontDetectionResult>,
    Error,
    FrontDetectionParams
  >({
    mutationFn: (params) => diagnosticsService.detectFronts(params),
    ...options
  });
};

/**
 * Custom hook for creating diagnostic tasks
 */
export const useCreateDiagnosticTask = (options?: UseMutationOptions<
  ApiResponse<{ task_id: string, status: string }>,
  Error,
  { algorithmId: string, parameters: any, datasetId: string }
>) => {
  const queryClient = useQueryClient();
  
  return useMutation<
    ApiResponse<{ task_id: string, status: string }>,
    Error,
    { algorithmId: string, parameters: any, datasetId: string }
  >({
    mutationFn: ({ algorithmId, parameters, datasetId }) => 
      diagnosticsService.createDiagnosticTask(algorithmId, parameters, datasetId),
    onSuccess: () => {
      // Invalidate diagnostic tasks query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['diagnosticTasks'] });
    },
    ...options
  });
};

/**
 * Custom hook for fetching diagnostic tasks
 */
export const useDiagnosticTasks = (options?: UseQueryOptions<ApiResponse<TaskStatus[]>, Error>) => {
  return useQuery<ApiResponse<TaskStatus[]>, Error>({
    queryKey: ['diagnosticTasks'],
    queryFn: () => diagnosticsService.getDiagnosticTasks(),
    ...options
  });
};

/**
 * Custom hook for fetching diagnostic task details
 */
export const useDiagnosticTaskDetails = (id: string, options?: UseQueryOptions<ApiResponse<TaskStatus>, Error>) => {
  return useQuery<ApiResponse<TaskStatus>, Error>({
    queryKey: ['diagnosticTaskDetails', id],
    queryFn: () => diagnosticsService.getDiagnosticTaskDetails(id),
    enabled: !!id,
    ...options
  });
};

/**
 * Custom hook for fetching diagnostic task results
 */
export const useDiagnosticTaskResults = (id: string, options?: UseQueryOptions<ApiResponse<any>, Error>) => {
  return useQuery<ApiResponse<any>, Error>({
    queryKey: ['diagnosticTaskResults', id],
    queryFn: () => diagnosticsService.getDiagnosticTaskResults(id),
    enabled: !!id,
    ...options
  });
};

/**
 * Custom hook for running specialized thermocline diagnosis
 */
export const useThermoclineDiagnosis = (options?: UseMutationOptions<
  ApiResponse<any>,
  Error,
  any
>) => {
  return useMutation<
    ApiResponse<any>,
    Error,
    any
  >({
    mutationFn: (params) => diagnosticsService.runThermoclineDiagnosis(params),
    ...options
  });
};

/**
 * Custom hook for running specialized eddy diagnosis
 */
export const useEddyDiagnosis = (options?: UseMutationOptions<
  ApiResponse<any>,
  Error,
  any
>) => {
  return useMutation<
    ApiResponse<any>,
    Error,
    any
  >({
    mutationFn: (params) => diagnosticsService.runEddyDiagnosis(params),
    ...options
  });
};

/**
 * Custom hook for running specialized front diagnosis
 */
export const useFrontDiagnosis = (options?: UseMutationOptions<
  ApiResponse<any>,
  Error,
  any
>) => {
  return useMutation<
    ApiResponse<any>,
    Error,
    any
  >({
    mutationFn: (params) => diagnosticsService.runFrontDiagnosis(params),
    ...options
  });
};
