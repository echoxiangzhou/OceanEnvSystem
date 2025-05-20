import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { productService } from '../services';
import { 
  ApiResponse,
  ProductGenerationRequest,
  ProductGenerationResponse
} from '../types/api';

/**
 * Custom hook for generating reports
 */
export const useGenerateReport = (options?: UseMutationOptions<
  ApiResponse<ProductGenerationResponse>,
  Error,
  ProductGenerationRequest['config']
>) => {
  const queryClient = useQueryClient();
  
  return useMutation<
    ApiResponse<ProductGenerationResponse>,
    Error,
    ProductGenerationRequest['config']
  >({
    mutationFn: (config) => productService.generateReport(config),
    onSuccess: () => {
      // Invalidate reports query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
    ...options
  });
};

/**
 * Custom hook for fetching report templates
 */
export const useReportTemplates = (options?: UseQueryOptions<ApiResponse<{ id: string, name: string, description: string }[]>, Error>) => {
  return useQuery<ApiResponse<{ id: string, name: string, description: string }[]>, Error>({
    queryKey: ['reportTemplates'],
    queryFn: () => productService.getReportTemplates(),
    ...options
  });
};

/**
 * Custom hook for creating reports
 */
export const useCreateReport = (options?: UseMutationOptions<
  ApiResponse<{ id: string, file_location: string }>,
  Error,
  { templateId: string, parameters: any, sourceResults: string[] }
>) => {
  const queryClient = useQueryClient();
  
  return useMutation<
    ApiResponse<{ id: string, file_location: string }>,
    Error,
    { templateId: string, parameters: any, sourceResults: string[] }
  >({
    mutationFn: ({ templateId, parameters, sourceResults }) => 
      productService.createReport(templateId, parameters, sourceResults),
    onSuccess: () => {
      // Invalidate reports query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
    ...options
  });
};

/**
 * Custom hook for fetching reports
 */
export const useReports = (options?: UseQueryOptions<ApiResponse<{ id: string, name: string, description: string, file_location: string, created_at: string }[]>, Error>) => {
  return useQuery<ApiResponse<{ id: string, name: string, description: string, file_location: string, created_at: string }[]>, Error>({
    queryKey: ['reports'],
    queryFn: () => productService.getReports(),
    ...options
  });
};

/**
 * Custom hook for fetching report details
 */
export const useReportDetails = (id: string, options?: UseQueryOptions<ApiResponse<{ id: string, name: string, description: string, file_location: string, created_at: string }>, Error>) => {
  return useQuery<ApiResponse<{ id: string, name: string, description: string, file_location: string, created_at: string }>, Error>({
    queryKey: ['reportDetails', id],
    queryFn: () => productService.getReportDetails(id),
    enabled: !!id,
    ...options
  });
};

/**
 * Custom hook for downloading reports
 */
export const useDownloadReport = (options?: UseMutationOptions<
  string | null,
  Error,
  { id: string, filename: string }
>) => {
  return useMutation<
    string | null,
    Error,
    { id: string, filename: string }
  >({
    mutationFn: ({ id, filename }) => productService.downloadReport(id, filename),
    ...options
  });
};

/**
 * Custom hook for creating visualizations
 */
export const useCreateVisualization = (options?: UseMutationOptions<
  ApiResponse<{ id: string, image_location: string }>,
  Error,
  { type: string, datasetId: string, parameters: any }
>) => {
  const queryClient = useQueryClient();
  
  return useMutation<
    ApiResponse<{ id: string, image_location: string }>,
    Error,
    { type: string, datasetId: string, parameters: any }
  >({
    mutationFn: ({ type, datasetId, parameters }) => 
      productService.createVisualization(type, datasetId, parameters),
    onSuccess: () => {
      // Invalidate visualizations query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['visualizations'] });
    },
    ...options
  });
};

/**
 * Custom hook for fetching visualizations
 */
export const useVisualizations = (options?: UseQueryOptions<ApiResponse<{ id: string, name: string, description: string, type: string, image_location: string }[]>, Error>) => {
  return useQuery<ApiResponse<{ id: string, name: string, description: string, type: string, image_location: string }[]>, Error>({
    queryKey: ['visualizations'],
    queryFn: () => productService.getVisualizations(),
    ...options
  });
};

/**
 * Custom hook for fetching visualization details
 */
export const useVisualizationDetails = (id: string, options?: UseQueryOptions<ApiResponse<{ id: string, name: string, description: string, type: string, image_location: string }>, Error>) => {
  return useQuery<ApiResponse<{ id: string, name: string, description: string, type: string, image_location: string }>, Error>({
    queryKey: ['visualizationDetails', id],
    queryFn: () => productService.getVisualizationDetails(id),
    enabled: !!id,
    ...options
  });
};

/**
 * Custom hook for exporting visualizations
 */
export const useExportVisualization = (options?: UseMutationOptions<
  string | null,
  Error,
  { id: string, format: 'png' | 'jpg' | 'svg' | 'pdf' }
>) => {
  return useMutation<
    string | null,
    Error,
    { id: string, format: 'png' | 'jpg' | 'svg' | 'pdf' }
  >({
    mutationFn: ({ id, format }) => productService.exportVisualization(id, format),
    ...options
  });
};
