// 通用API响应类型
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// 数据相关类型定义
export interface Dataset {
  id: string;
  name: string;
  description: string;
  source_type: 'BUOY' | 'SURVEY' | 'SATELLITE' | 'MODEL';
  data_type: 'OBSERVATIONS' | 'FORECAST' | 'REANALYSIS';
  spatial_coverage?: {
    type: string;
    coordinates: number[][][];
  };
  temporal_coverage?: {
    start: string;
    end: string;
  };
  variables: Variable[];
  file_format: string;
  file_location: string;
  created_at: string;
  updated_at: string;
  institution?: string; // 机构/生产者信息
  urlPath?: string; // Thredds数据集特有的路径
  opendapUrl?: string; // OPeNDAP访问URL
  httpUrl?: string; // HTTP直接下载URL
  threddsId?: string; // Thredds服务器上的ID
}

export interface Variable {
  name: string;
  standard_name?: string;
  unit: string;
  description: string;
  dimensions?: Dimension[];
  attributes?: Record<string, any>;
}

export interface Dimension {
  name: string;
  size: number;
  values?: number[];
}

export interface DatasetMetadata {
  variables: string[];
  dims: Record<string, number>;
  attrs: Record<string, any>;
}

export interface DataConversionResponse {
  netcdf_path: string;
  message: string;
}

// 融合相关类型定义
export interface FusionTask {
  id: string;
  name: string;
  description: string;
  algorithm_id: string;
  parameters: Record<string, any>;
  source_datasets: string[];
  result_dataset: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  user_id: string;
  error_message?: string;
}

export interface OptimalInterpolationParams {
  obs_coords: number[][];
  obs_values: number[];
  interp_coords: number[][];
  sigma2: number;
  L: number;
  noise?: number;
}

export interface OptimalInterpolationResult {
  interp_values: number[];
  interp_error: number[];
}

export interface KalmanFilterParams {
  observations: number[][];
  initial_state: number[];
  initial_cov: number[][];
  transition_matrix: number[][];
  observation_matrix: number[][];
  process_noise: number[][];
  observation_noise: number[][];
}

export interface KalmanFilterResult {
  state_estimates: number[][];
  covariances: number[][][];
}

export interface FusionTaskRequest {
  algorithm: 'optimal_interpolation' | 'kalman_filter';
  [key: string]: any;
}

export interface FusionTaskResponse {
  task_id: string;
  status: string;
}

export interface TaskStatus {
  id: string;
  status: 'queued' | 'running' | 'finished' | 'failed' | 'cancelled';
  result?: any;
  exc_info?: string | null;
}

// 诊断相关类型定义
export interface ClineDetectionParams {
  depth: number[];
  profile: number[];
  cline_type: 'temperature' | 'density' | 'sound_speed';
  window_size?: number;
}

export interface ClineDetectionResult {
  cline_depth: number;
  max_gradient: number;
  upper_value: number;
  lower_value: number;
}

export interface EddyDetectionParams {
  ssh: number[][];
  lat: number[];
  lon: number[];
  threshold: number;
}

export interface EddyDetectionResult {
  centers: { lat: number; lon: number }[];
  indices: number[][];
}

export interface FrontDetectionParams {
  sst: number[][];
  lat: number[];
  lon: number[];
  gradient_threshold: number;
}

export interface FrontDetectionResult {
  centers: { lat: number; lon: number }[];
  indices: number[][];
}

// 产品生成相关类型定义
export interface ProductGenerationRequest {
  config: {
    title: string;
    datasets: string[];
    diagnostics?: string[];
    fusion?: string[];
    user: string;
  };
}

export interface ProductGenerationResponse {
  report_path: string;
  message: string;
}

// 文件上传相关类型
export interface FileUploadResponse {
  filename: string;
  size: number;
  content_type: string;
}
