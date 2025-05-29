import React, { useState, useEffect, ReactNode } from 'react';
import { useParams, Link } from 'react-router-dom';
import taskService from '@/services/taskService';
import { TaskStatus } from '@/types/api';

// 模拟数据，在真实API连接前使用
const MOCK_TASK_DETAIL: TaskStatus = {
  id: '1',
  status: 'finished',
  result: { 
    interp_values: [1.2, 2.3, 3.4, 2.8, 1.9, 3.1],
    interp_coords: [[0, 0], [1, 0], [0, 1], [1, 1], [0.5, 0.5], [1.5, 1.5]],
    interp_error: [0.1, 0.15, 0.12, 0.09, 0.2, 0.18],
    algorithm: 'optimal_interpolation',
    parameters: {
      sigma2: 1.0,
      L: 1.0,
      noise: 1e-6
    }
  },
  exc_info: null,
};

// 环境变量或配置，控制是否使用模拟数据
const USE_MOCK = true;

const TaskDetail: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const [task, setTask] = useState<TaskStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTaskDetails();
  }, [taskId]);

  const fetchTaskDetails = async () => {
    setLoading(true);
    setError(null);

    try {
      if (USE_MOCK) {
        // 使用模拟数据
        setTimeout(() => {
          setTask(MOCK_TASK_DETAIL);
          setLoading(false);
        }, 500);
      } else {
        const response = await taskService.getTaskDetails(taskId!);
        if (response.error) {
          throw new Error(response.error);
        }
        setTask(response.data || null);
        setLoading(false);
      }
    } catch (err) {
      console.error('获取任务详情失败', err);
      setError('获取任务详情失败，请重试');
      setLoading(false);
    }
  };

  // 渲染任务详情
  const renderTaskDetails = () => {
    if (loading) {
      return (
        <div className="flex justify-center items-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded relative" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      );
    }

    if (!task) {
      return (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          未找到任务数据
        </div>
      );
    }

    return (
      <div>
        <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
              任务详情
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
              任务ID: {task.id}
            </p>
          </div>
          <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-5 sm:p-0">
            <dl className="sm:divide-y sm:divide-gray-200 dark:sm:divide-gray-700">
              <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  状态
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-200 sm:mt-0 sm:col-span-2">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full
                    ${task.status === 'finished' ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400' : 
                      task.status === 'running' ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-400' : 
                      task.status === 'queued' ? 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-400' : 
                      'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-400'}`}
                  >
                    {task.status === 'finished' ? '已完成' : 
                     task.status === 'running' ? '运行中' : 
                     task.status === 'queued' ? '排队中' : 
                     task.status === 'cancelled' ? '已取消' : '失败'}
                  </span>
                </dd>
              </div>
              <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  任务类型
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-200 sm:mt-0 sm:col-span-2">
                  数据融合
                </dd>
              </div>
              <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  算法
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-200 sm:mt-0 sm:col-span-2">
                  {task.result?.algorithm === 'optimal_interpolation' 
                    ? '最优插值（Optimal Interpolation, OI）' 
                    : task.result?.algorithm === 'kalman_filter'
                    ? '卡尔曼滤波（Kalman Filter）'
                    : '未知算法'}
                </dd>
              </div>
              <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  创建时间
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-200 sm:mt-0 sm:col-span-2">
                  {new Date().toLocaleString()} {/* 实际应使用任务的创建时间 */}
                </dd>
              </div>
              <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  完成时间
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-200 sm:mt-0 sm:col-span-2">
                  {task.status === 'finished' ? new Date().toLocaleString() : '未完成'} {/* 实际应使用任务的完成时间 */}
                </dd>
              </div>
              {task.result?.parameters && (
                <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    参数
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-200 sm:mt-0 sm:col-span-2">
                    <ul className="border border-gray-200 dark:border-gray-700 rounded-md divide-y divide-gray-200 dark:divide-gray-700">
                      {Object.entries(task.result.parameters as Record<string, ReactNode>).map(([key, value]) => (
                        <li key={key} className="pl-3 pr-4 py-3 flex items-center justify-between text-sm">
                          <div className="w-0 flex-1 flex items-center">
                            <span className="ml-2 flex-1 w-0 truncate">
                              {key}: {value}
                            </span>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </dd>
                </div>
              )}
              {task.exc_info && (
                <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    错误信息
                  </dt>
                  <dd className="mt-1 text-sm text-red-600 dark:text-red-400 sm:mt-0 sm:col-span-2">
                    {task.exc_info}
                  </dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        {/* 任务结果 */}
        {task.status === 'finished' && task.result && (
          <div className="mt-6 bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                任务结果
              </h3>
            </div>
            <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-5 sm:px-6">
              {/* 结果表格 */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        坐标
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        插值结果
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        误差
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {task.result.interp_values && task.result.interp_values.map((value: number, index: number) => (
                      <tr key={index} className={index % 2 === 0 ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-700'}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {task.result.interp_coords && task.result.interp_coords[index] 
                            ? `(${task.result.interp_coords[index][0]}, ${task.result.interp_coords[index][1]})` 
                            : `点 ${index + 1}`}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-200">
                          {value.toFixed(4)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {task.result.interp_error && task.result.interp_error[index] 
                            ? `±${task.result.interp_error[index].toFixed(4)}` 
                            : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* 可视化结果 */}
              <div className="mt-6">
                <h4 className="text-base font-medium text-gray-700 dark:text-gray-300 mb-4">
                  可视化结果
                </h4>
                <div className="bg-gray-100 dark:bg-gray-700 h-64 rounded-lg flex items-center justify-center">
                  <p className="text-gray-500 dark:text-gray-400">
                    图表可视化将在此显示
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="mt-6 flex justify-end">
          <Link
            to="/fusion/task"
            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            返回任务列表
          </Link>
          {task.status === 'finished' && (
            <button
              type="button"
              className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              导出结果
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 dark:text-white sm:text-3xl sm:truncate">
            任务详情
          </h2>
        </div>
      </div>

      {/* 任务详情 */}
      {renderTaskDetails()}
    </div>
  );
};

export default TaskDetail; 