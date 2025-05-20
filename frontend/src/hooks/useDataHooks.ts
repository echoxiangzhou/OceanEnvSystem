import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { dataService } from '../services';
import { ApiResponse, Dataset, DatasetMetadata } from '../types/api';

/**
 * Custom hook for fetching datasets list
 */
export const useDatasets = (options?: UseQueryOptions<ApiResponse<Dataset[]>, Error>) => {
  return useQuery<ApiResponse<Dataset[]>, Error>({
    queryKey: ['datasets'],
    queryFn: () => dataService.getAllDatasets(),
    ...options
  });
};

/**
 * Custom hook for fetching a specific dataset
 */
export const useDatasetDetail = (id: string, options?: UseQueryOptions<ApiResponse<Dataset>, Error>) => {
  return useQuery<ApiResponse<Dataset>, Error>({
    queryKey: ['dataset', id],
    queryFn: () => dataService.getDataset(id),
    enabled: !!id,
    ...options
  });
};

/**
 * Custom hook for fetching data files list
 */
export const useDataFiles = (ext?: string, options?: UseQueryOptions<ApiResponse<string[]>, Error>) => {
  return useQuery<ApiResponse<string[]>, Error>({
    queryKey: ['dataFiles', ext],
    queryFn: () => dataService.getDataList(ext),
    ...options
  });
};

/**
 * Custom hook for fetching file metadata
 */
export const useFileMetadata = (relpath: string, options?: UseQueryOptions<ApiResponse<DatasetMetadata>, Error>) => {
  return useQuery<ApiResponse<DatasetMetadata>, Error>({
    queryKey: ['fileMetadata', relpath],
    queryFn: () => dataService.getDataMetadata(relpath),
    enabled: !!relpath,
    ...options
  });
};

/**
 * Custom hook for uploading and converting data files
 */
export const useDataConversion = (options?: UseMutationOptions<
  ApiResponse<any>,
  Error,
  { file: File, fileType: 'csv' | 'xlsx' | 'cnv' }
>) => {
  return useMutation<
    ApiResponse<any>,
    Error,
    { file: File, fileType: 'csv' | 'xlsx' | 'cnv' }
  >({
    mutationFn: ({ file, fileType }) => dataService.convertData(file, fileType),
    ...options
  });
};

/**
 * Custom hook for registering a dataset
 */
export const useRegisterDataset = (options?: UseMutationOptions<
  ApiResponse<{ id: string, message: string }>,
  Error,
  Omit<Dataset, 'id' | 'created_at' | 'updated_at'>
>) => {
  const queryClient = useQueryClient();
  
  return useMutation<
    ApiResponse<{ id: string, message: string }>,
    Error,
    Omit<Dataset, 'id' | 'created_at' | 'updated_at'>
  >({
    mutationFn: (dataset) => dataService.registerDataset(dataset),
    onSuccess: () => {
      // Invalidate datasets query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
    ...options
  });
};

/**
 * Custom hook for deleting a dataset
 */
export const useDeleteDataset = (options?: UseMutationOptions<
  ApiResponse<{ id: string, message: string }>,
  Error,
  string
>) => {
  const queryClient = useQueryClient();
  
  return useMutation<
    ApiResponse<{ id: string, message: string }>,
    Error,
    string
  >({
    mutationFn: (id) => dataService.deleteDataset(id),
    onSuccess: (_, id) => {
      // Invalidate datasets query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      // Remove the specific dataset from cache
      queryClient.removeQueries({ queryKey: ['dataset', id] });
    },
    ...options
  });
};

/**
 * Custom hook for querying a data subset
 */
export const useDataSubsetQuery = (options?: UseMutationOptions<
  ApiResponse<{ data: any[] }>,
  Error,
  {
    dataset_id: string;
    variables?: string[];
    spatial_range?: { lat: [number, number]; lon: [number, number] };
    time_range?: { start: string; end: string };
  }
>) => {
  return useMutation<
    ApiResponse<{ data: any[] }>,
    Error,
    {
      dataset_id: string;
      variables?: string[];
      spatial_range?: { lat: [number, number]; lon: [number, number] };
      time_range?: { start: string; end: string };
    }
  >({
    mutationFn: (query) => dataService.queryDataSubset(query),
    ...options
  });
};

/**
 * Custom hook for fetching OPeNDAP data
 */
export const useOpenDAPData = (datasetPath: string, options?: UseQueryOptions<ApiResponse<DatasetMetadata>, Error>) => {
  return useQuery<ApiResponse<DatasetMetadata>, Error>({
    queryKey: ['opendap', datasetPath],
    queryFn: () => dataService.getOpenDAPData(datasetPath),
    enabled: !!datasetPath,
    ...options
  });
};
