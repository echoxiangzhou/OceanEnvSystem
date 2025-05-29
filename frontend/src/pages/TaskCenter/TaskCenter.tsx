import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import taskService from '@/services/taskService';
import fusionService from '@/services/fusionService';
import { TaskStatus } from '@/types/api';

// 模拟数据，在真实API连接前使用
const MOCK_TASKS: TaskStatus[] = [
  {
    id: '1',
    status: 'finished',
    result: { interp_values: [1.2, 2.3, 3.4] },
    exc_info: null,
  },
  {
    id: '2',
    status: 'running',
    exc_info: null,
  },
  {
    id: '3',
    status: 'queued',
    exc_info: null,
  },
  {
    id: '4',
    status: 'failed',
    exc_info: '计算出错：输入数据格式不正确',
  },
];

// 环境变量或配置，控制是否使用模拟数据
const USE_MOCK = true;

const TaskCenter: React.FC = () => {
  // 状态定义
  const [tasks, setTasks] = useState<TaskStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [taskType, setTaskType] = useState<string>('all'); // all, fusion, diagnostics, product
  const navigate = useNavigate();

  // 获取任务列表
  useEffect(() => {
    fetchTasks();
  }, [filter, taskType]);

  const fetchTasks = async () => {
    setLoading(true);
    setError(null);

    try {
      if (USE_MOCK) {
        // 使用模拟数据
        setTimeout(() => {
          let filteredTasks = [...MOCK_TASKS];
          
          // 应用状态过滤
          if (filter !== 'all') {
            filteredTasks = filteredTasks.filter(task => task.status === filter);
          }
          
          // 应用搜索条件
          if (searchTerm) {
            filteredTasks = filteredTasks.filter(task => 
              task.id.includes(searchTerm) || 
              (task.exc_info && task.exc_info.includes(searchTerm))
            );
          }
          
          setTasks(filteredTasks);
          setLoading(false);
        }, 500);
      } else {
        // 调用真实API
        const response = await taskService.getTasks({
          status: filter !== 'all' ? filter : undefined,
          type: taskType !== 'all' ? taskType : undefined,
        });

        if (response.error) {
          throw new Error(response.error);
        }

        if (response.data) {
          let filteredTasks = response.data;
          
          // 应用搜索条件
          if (searchTerm) {
            filteredTasks = filteredTasks.filter(task => 
              task.id.includes(searchTerm) || 
              (task.exc_info && task.exc_info.includes(searchTerm))
            );
          }
          
          setTasks(filteredTasks);
        }
        setLoading(false);
      }
    } catch (err) {
      console.error('获取任务列表失败', err);
      setError('获取任务列表失败，请重试');
      setLoading(false);
    }
  };

  // 取消任务
  const handleCancelTask = async (taskId: string) => {
    try {
      if (USE_MOCK) {
        // 模拟任务取消
        setTasks(prevTasks => 
          prevTasks.map(task => 
            task.id === taskId ? { ...task, status: 'cancelled' as any } : task
          )
        );
      } else {
        const response = await taskService.cancelTask(taskId);
        if (response.error) {
          throw new Error(response.error);
        }
        // 更新任务列表
        fetchTasks();
      }
    } catch (err) {
      console.error('取消任务失败', err);
      setError('取消任务失败，请重试');
    }
  };

  // 删除任务
  const handleDeleteTask = async (taskId: string) => {
    try {
      if (USE_MOCK) {
        // 模拟任务删除
        setTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
      } else {
        const response = await fusionService.cancelFusionTask(taskId);
        if (response.error) {
          throw new Error(response.error);
        }
        // 更新任务列表
        fetchTasks();
      }
    } catch (err) {
      console.error('删除任务失败', err);
      setError('删除任务失败，请重试');
    }
  };

  // 查看任务详情
  const handleViewTaskDetails = (taskId: string) => {
    // 导航到任务详情页
    navigate(`/fusion/task/${taskId}`);
  };

  // 重新运行任务
  const handleRerunTask = (taskId: string) => {
    console.log(`重新运行任务${taskId}`);
    // 后续可以添加重新运行任务的逻辑
  };

  // 渲染任务列表
  const renderTaskList = () => {
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

    if (tasks.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          没有找到任务数据
        </div>
      );
    }

    return (
      <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200 dark:divide-gray-700">
          {tasks.map(task => (
            <li key={task.id} className="px-4 py-4 sm:px-6">
              <div className="grid grid-cols-12 gap-4">
                <div className="col-span-12 lg:col-span-4">
                  <div className="font-medium text-blue-600 dark:text-blue-400">
                    任务ID: {task.id}
                  </div>
                  <div className="mt-1 flex items-center text-sm text-gray-500 dark:text-gray-400">
                    类型: 数据融合
                  </div>
                </div>
                <div className="col-span-6 lg:col-span-3">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-200">状态</div>
                  <div className="mt-1">
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
                  </div>
                </div>
                <div className="col-span-6 lg:col-span-3">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-200">创建时间</div>
                  <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    {new Date().toLocaleString()} {/* 实际应使用任务的创建时间 */}
                  </div>
                </div>
                <div className="col-span-12 lg:col-span-2 flex justify-end items-center">
                  <div className="flex space-x-2">
                    {task.status === 'finished' && (
                      <button 
                        onClick={() => handleViewTaskDetails(task.id)}
                        className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-blue-700 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/20 hover:bg-blue-200 dark:hover:bg-blue-800/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        详情
                      </button>
                    )}
                    {task.status === 'failed' && (
                      <button 
                        onClick={() => handleRerunTask(task.id)}
                        className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-green-700 dark:text-green-400 bg-green-100 dark:bg-green-900/20 hover:bg-green-200 dark:hover:bg-green-800/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                      >
                        重试
                      </button>
                    )}
                    {(task.status === 'running' || task.status === 'queued') && (
                      <button 
                        onClick={() => handleCancelTask(task.id)}
                        className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-yellow-700 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/20 hover:bg-yellow-200 dark:hover:bg-yellow-800/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
                      >
                        取消
                      </button>
                    )}
                    <button 
                      onClick={() => handleDeleteTask(task.id)}
                      className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 dark:text-red-400 bg-red-100 dark:bg-red-900/20 hover:bg-red-200 dark:hover:bg-red-800/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    >
                      删除
                    </button>
                  </div>
                </div>
                {task.exc_info && (
                  <div className="col-span-12 mt-2">
                    <div className="text-sm text-red-600 dark:text-red-400">
                      错误信息: {task.exc_info}
                    </div>
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 dark:text-white sm:text-3xl sm:truncate">
            任务中心
          </h2>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <Link
            to="/fusion/new"
            className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            创建融合任务
          </Link>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 shadow px-4 py-5 sm:px-6 sm:rounded-lg mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="col-span-1">
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              状态
            </label>
            <select
              id="status"
              name="status"
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md dark:bg-gray-700 dark:text-white"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">全部</option>
              <option value="queued">排队中</option>
              <option value="running">运行中</option>
              <option value="finished">已完成</option>
              <option value="failed">失败</option>
              <option value="cancelled">已取消</option>
            </select>
          </div>
          <div className="col-span-1">
            <label htmlFor="type" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              任务类型
            </label>
            <select
              id="type"
              name="type"
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md dark:bg-gray-700 dark:text-white"
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
            >
              <option value="all">全部</option>
              <option value="fusion">数据融合</option>
              <option value="diagnostics">诊断分析</option>
              <option value="product">产品生成</option>
            </select>
          </div>
          <div className="col-span-2">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              搜索
            </label>
            <div className="mt-1 relative rounded-md shadow-sm">
              <input
                type="text"
                name="search"
                id="search"
                className="focus:ring-blue-500 focus:border-blue-500 block w-full pr-10 sm:text-sm border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                placeholder="输入任务ID或关键字"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={fetchTasks}
            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            搜索
          </button>
        </div>
      </div>

      {/* 任务列表 */}
      <div className="mt-4">
        {renderTaskList()}
      </div>
    </div>
  );
};

export default TaskCenter; 