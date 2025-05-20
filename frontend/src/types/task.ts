// 任务类型定义
export enum TaskType {
  FUSION = 'fusion',
  DIAGNOSTIC = 'diagnostic',
  PRODUCT = 'product',
  OTHER = 'other'
}

// 任务状态定义
export enum TaskStatus {
  PENDING = 'pending',
  QUEUED = 'queued',
  RUNNING = 'running',
  FINISHED = 'finished',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

// 任务对象接口
export interface Task {
  id: string;
  name: string;
  description?: string;
  type: TaskType;
  status: TaskStatus;
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  user_id: string;
  error_message?: string;
  result_id?: string;
  result_type?: string;
  parameters?: Record<string, any>;
}

// 任务过滤器接口
export interface TaskFilter {
  type?: TaskType;
  status?: TaskStatus;
  timeRange?: {
    start: string;
    end: string;
  };
  searchText?: string;
}

// 任务排序选项
export enum TaskSortField {
  CREATED_AT = 'created_at',
  STARTED_AT = 'started_at',
  COMPLETED_AT = 'completed_at',
  STATUS = 'status',
  PROGRESS = 'progress',
  NAME = 'name'
}

export enum SortDirection {
  ASC = 'asc',
  DESC = 'desc'
}

export interface TaskSort {
  field: TaskSortField;
  direction: SortDirection;
}

// 任务分页接口
export interface TaskPagination {
  page: number;
  limit: number;
  total: number;
}

// 任务操作类型
export enum TaskOperation {
  VIEW = 'view',
  CANCEL = 'cancel',
  DELETE = 'delete',
  DOWNLOAD = 'download',
  VISUALIZE = 'visualize'
}

// 任务操作权限
export interface TaskOperationPermissions {
  [TaskOperation.VIEW]: boolean;
  [TaskOperation.CANCEL]: boolean;
  [TaskOperation.DELETE]: boolean;
  [TaskOperation.DOWNLOAD]: boolean;
  [TaskOperation.VISUALIZE]: boolean;
}
