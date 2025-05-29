// 模拟数据 - 融合任务

// 生成简单的随机ID
const generateId = () => {
  return Math.random().toString(36).substring(2, 15) + 
         Math.random().toString(36).substring(2, 15);
};

// 模拟任务列表
export const mockTasks = [
  {
    id: '12345-abcde-67890',
    status: 'finished',
    algorithm: 'optimal_interpolation',
    result: {
      interp_values: [1.25, 1.75],
      interp_vars: [0.12, 0.15]
    },
    created_at: '2023-08-15T10:30:00Z',
    finished_at: '2023-08-15T10:30:05Z',
    exc_info: null
  },
  {
    id: '54321-fghij-09876',
    status: 'failed',
    algorithm: 'kalman_filter',
    result: null,
    created_at: '2023-08-14T16:45:00Z',
    finished_at: '2023-08-14T16:45:10Z',
    exc_info: 'ValueError: Dimensions mismatch in observation_matrix'
  },
  {
    id: '98765-klmno-43210',
    status: 'finished',
    algorithm: 'optimal_interpolation',
    result: {
      interp_values: [0.8, 1.2, 1.5],
      interp_vars: [0.08, 0.11, 0.14]
    },
    created_at: '2023-08-13T09:15:00Z',
    finished_at: '2023-08-13T09:15:07Z',
    exc_info: null
  }
];

// 模拟任务状态
let runningTaskIds: {[key: string]: any} = {};

// 模拟提交任务
export const mockSubmitTask = (data: any) => {
  const taskId = generateId();
  runningTaskIds[taskId] = {
    id: taskId,
    status: 'running',
    algorithm: data.algorithm,
    result: null,
    created_at: new Date().toISOString(),
    finished_at: null,
    exc_info: null,
    data
  };
  
  // 模拟任务完成过程 (3秒后完成)
  setTimeout(() => {
    if (runningTaskIds[taskId]) {
      let result = null;
      let exc_info = null;
      const random = Math.random();
      
      if (random > 0.2) { // 80%概率成功
        if (data.algorithm === 'optimal_interpolation') {
          result = {
            interp_values: Array.from({length: data.interp_coords.length}, () => Math.random() * 3),
            interp_vars: Array.from({length: data.interp_coords.length}, () => Math.random() * 0.2)
          };
        } else if (data.algorithm === 'kalman_filter') {
          result = {
            filtered_states: Array.from({length: data.observations.length}, () => [Math.random() * 5]),
            filtered_covariances: Array.from({length: data.observations.length}, () => [[Math.random()]])
          };
        }
        runningTaskIds[taskId].status = 'finished';
      } else { // 20%概率失败
        runningTaskIds[taskId].status = 'failed';
        exc_info = 'Simulated error in task processing';
      }
      
      runningTaskIds[taskId].result = result;
      runningTaskIds[taskId].exc_info = exc_info;
      runningTaskIds[taskId].finished_at = new Date().toISOString();
    }
  }, 3000);
  
  return { task_id: taskId, status: 'queued' };
};

// 模拟获取任务状态
export const mockGetTaskStatus = (taskId: string) => {
  // 首先查找正在运行的任务
  if (runningTaskIds[taskId]) {
    return runningTaskIds[taskId];
  }
  
  // 然后查找历史任务
  const task = mockTasks.find(t => t.id === taskId);
  if (task) {
    return task;
  }
  
  throw new Error('Task not found');
};

// 模拟获取任务列表
export const mockListTasks = (limit: number = 10) => {
  // 合并正在运行的任务和历史任务
  const runningTasksList = Object.values(runningTaskIds);
  const allTasks = [...runningTasksList, ...mockTasks];
  
  // 按创建时间排序，限制返回数量
  return allTasks
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, limit);
};

// 模拟取消任务
export const mockCancelTask = (taskId: string) => {
  if (runningTaskIds[taskId]) {
    runningTaskIds[taskId].status = 'cancelled';
    runningTaskIds[taskId].finished_at = new Date().toISOString();
    return true;
  }
  return false;
}; 