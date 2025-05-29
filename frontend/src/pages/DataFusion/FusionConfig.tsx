import React, { useState } from 'react';
import { useDatasets, useOpenDAPData } from '@/hooks/useDataHooks';
import { Dataset } from '@/types/api';
import { mockSubmitTask, mockGetTaskStatus, mockListTasks } from '@/mocks/fusionData';
import { Tab } from '@headlessui/react';

// 算法选项
const ALGORITHM_OPTIONS = [
  { label: '最优插值（Optimal Interpolation, OI）', value: 'optimal_interpolation' },
  { label: '卡尔曼滤波（Kalman Filter）', value: 'kalman_filter' },
];

// OI参数初始值
const OI_DEFAULTS = {
  obs_coords: '[[0,0],[1,0],[0,1]]', // [[x1,y1],[x2,y2],...]
  obs_values: '[1.0,2.0,1.5]', // [v1,v2,...]
  interp_coords: '[[0.5,0.5],[1,1]]', // [[x1,y1],[x2,y2],...]
  sigma2: 1.0,
  L: 1.0,
  noise: 1e-6,
};

// Kalman参数初始值
const KALMAN_DEFAULTS = {
  observations: '[[1.0],[2.0],[1.5]]', // [[v1],[v2],...]
  initial_state: '[1.0]', // [s1,...]
  initial_cov: '[[1.0]]', // [[c11,...],[...]]
  transition_matrix: '[[1.0]]', // [[...]]
  observation_matrix: '[[1.0]]', // [[...]]
  process_noise: '[[0.01]]', // [[...]]
  observation_noise: '[[0.1]]', // [[...]]
};

// 定义API响应类型
interface TaskResponse {
  task_id: string;
  status: string;
  result?: any;
  exc_info?: string;
}

interface TaskStatus {
  id: string;
  status: string;
  algorithm: string;
  result: any;
  created_at: string;
  finished_at: string | null;
  exc_info: string | null;
}

// 数据源类型
type DataSource = {
  type: 'local' | 'opendap';
  datasetId?: string; // 本地数据集ID
  opendapPath?: string; // OPeNDAP数据路径
  metadata?: any;
  selectedVariable?: string; // 选中的变量
  selectedDimensions?: {[key: string]: [number, number]}; // 维度切片范围
};

// 环境变量或配置，控制是否使用模拟数据
const USE_MOCK = true;

const FusionConfig: React.FC = () => {
  // 基础状态
  const [algorithm, setAlgorithm] = useState('optimal_interpolation');
  const [oiParams, setOiParams] = useState(OI_DEFAULTS);
  const [kalmanParams, setKalmanParams] = useState(KALMAN_DEFAULTS);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [history, setHistory] = useState<TaskStatus[]>([]);

  // 数据源选择状态
  const [dataSourceType, setDataSourceType] = useState<'dataset'>('dataset'); // 只使用数据集方式
  const [observationSource, setObservationSource] = useState<DataSource>({ type: 'local' });
  const [interpolationSource, setInterpolationSource] = useState<DataSource>({ type: 'local' });
  const [showDatasetSelector, setShowDatasetSelector] = useState(false);
  const [selectingFor, setSelectingFor] = useState<'observation' | 'interpolation'>('observation');

  // 获取数据集列表
  const { 
    data: datasetsResponse, 
    isLoading: isLoadingDatasets, 
    isError: isErrorDatasets,
  } = useDatasets();

  // 提取参数的替代函数 - 从数据集中提取
  const extractParamsFromDataset = (dataSource: DataSource) => {
    // 这里应该连接后端API，从选定的数据集中提取观测点坐标、值等参数
    // 目前使用模拟数据
    if (dataSource.type === 'local' && dataSource.datasetId) {
      return {
        coords: '[[1.0,2.0],[3.0,4.0],[5.0,6.0]]',
        values: '[10.5,12.3,9.8]'
      };
    } else if (dataSource.type === 'opendap' && dataSource.opendapPath) {
      return {
        coords: '[[1.5,2.5],[3.5,4.5],[5.5,6.5]]',
        values: '[11.2,13.1,9.2]'
      };
    }
    return { coords: '[]', values: '[]' };
  };

  // 处理参数输入
  const handleParamChange = (field: string, value: string) => {
    if (algorithm === 'optimal_interpolation') {
      setOiParams({ ...oiParams, [field]: value });
    } else {
      setKalmanParams({ ...kalmanParams, [field]: value });
    }
  };

  // 处理数据集选择
  const handleSelectDataset = (dataset: Dataset | null, forType: 'observation' | 'interpolation') => {
    if (forType === 'observation') {
      setObservationSource({ 
        ...observationSource, 
        type: 'local', 
        datasetId: dataset?.id
      });
      // 如果是OI算法，更新参数
      if (algorithm === 'optimal_interpolation' && dataset) {
        const params = extractParamsFromDataset({ type: 'local', datasetId: dataset.id });
        setOiParams({
          ...oiParams,
          obs_coords: params.coords,
          obs_values: params.values
        });
      }
    } else {
      setInterpolationSource({
        ...interpolationSource,
        type: 'local',
        datasetId: dataset?.id
      });
      // 如果是OI算法，更新参数
      if (algorithm === 'optimal_interpolation' && dataset) {
        const params = extractParamsFromDataset({ type: 'local', datasetId: dataset.id });
        setOiParams({
          ...oiParams,
          interp_coords: params.coords
        });
      }
    }
    setShowDatasetSelector(false);
  };

  // 处理OpenDAP数据集选择
  const handleSelectOpenDAP = (path: string, metadata: any, forType: 'observation' | 'interpolation') => {
    if (forType === 'observation') {
      setObservationSource({
        ...observationSource,
        type: 'opendap',
        opendapPath: path,
        metadata
      });
      // 如果是OI算法，更新参数
      if (algorithm === 'optimal_interpolation') {
        const params = extractParamsFromDataset({ type: 'opendap', opendapPath: path });
        setOiParams({
          ...oiParams,
          obs_coords: params.coords,
          obs_values: params.values
        });
      }
    } else {
      setInterpolationSource({
        ...interpolationSource,
        type: 'opendap',
        opendapPath: path,
        metadata
      });
      // 如果是OI算法，更新参数
      if (algorithm === 'optimal_interpolation') {
        const params = extractParamsFromDataset({ type: 'opendap', opendapPath: path });
        setOiParams({
          ...oiParams,
          interp_coords: params.coords
        });
      }
    }
    setShowDatasetSelector(false);
  };

  // 打开数据集选择器
  const openDatasetSelector = (forType: 'observation' | 'interpolation') => {
    setSelectingFor(forType);
    setShowDatasetSelector(true);
  };

  // 提交任务（异步）
  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setTaskId(null);
    setTaskStatus(null);
    try {
      let body: any = { algorithm };
      if (algorithm === 'optimal_interpolation') {
        body = {
          ...body,
          obs_coords: JSON.parse(oiParams.obs_coords),
          obs_values: JSON.parse(oiParams.obs_values),
          interp_coords: JSON.parse(oiParams.interp_coords),
          sigma2: Number(oiParams.sigma2),
          L: Number(oiParams.L),
          noise: Number(oiParams.noise),
        };
      } else {
        body = {
          ...body,
          observations: JSON.parse(kalmanParams.observations),
          initial_state: JSON.parse(kalmanParams.initial_state),
          initial_cov: JSON.parse(kalmanParams.initial_cov),
          transition_matrix: JSON.parse(kalmanParams.transition_matrix),
          observation_matrix: JSON.parse(kalmanParams.observation_matrix),
          process_noise: JSON.parse(kalmanParams.process_noise),
          observation_noise: JSON.parse(kalmanParams.observation_noise),
        };
      }
      
      let data: TaskResponse;
      if (USE_MOCK) {
        // 使用模拟数据
        data = mockSubmitTask(body);
      } else {
        // 使用真实API
        const resp = await fetch('/api/v1/fusion/run_async', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        data = await resp.json();
      }
      
      if (data.task_id) {
        setTaskId(data.task_id);
        pollTaskStatus(data.task_id);
      } else {
        setError('任务提交失败');
      }
    } catch (e: any) {
      setError(e.message || '任务提交异常');
    } finally {
      setLoading(false);
    }
  };

  // 轮询任务状态
  const pollTaskStatus = (id: string) => {
    const interval = setInterval(async () => {
      try {
        let data: TaskStatus;
        if (USE_MOCK) {
          // 使用模拟数据
          data = mockGetTaskStatus(id);
        } else {
          // 使用真实API
          const resp = await fetch(`/api/v1/fusion/task_status/${id}`);
          data = await resp.json();
        }
        
        setTaskStatus(data);
        if (data.status === 'finished' || data.status === 'failed' || data.status === 'cancelled') {
          clearInterval(interval);
          setResult(data.result);
          // 加入历史
          setHistory(h => [{ ...data }, ...h]);
        }
      } catch (e) {
        clearInterval(interval);
        setError('获取任务状态失败');
      }
    }, 1000);
  };

  // 历史任务列表刷新
  const fetchHistory = async () => {
    try {
      let data: TaskStatus[];
      if (USE_MOCK) {
        // 使用模拟数据
        data = mockListTasks(10);
      } else {
        // 使用真实API
        const resp = await fetch('/api/v1/fusion/tasks?limit=10');
        data = await resp.json();
      }
      setHistory(data);
    } catch (e) {
      console.error('获取历史任务失败', e);
    }
  };

  // 页面加载时拉取历史
  React.useEffect(() => {
    fetchHistory();
  }, []);

  // 参数表单渲染
  const renderParamsForm = () => {
    if (algorithm === 'optimal_interpolation') {
      return (
        <div className="space-y-4">
          {/* 数据集选择 */}
          <div className="space-y-2">
            <div className="flex justify-between items-center mb-1">
              <label className="block text-sm font-medium">观测数据</label>
              <button 
                onClick={() => openDatasetSelector('observation')}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                选择数据集
              </button>
            </div>
            {observationSource.datasetId ? (
              <div className="bg-gray-50 dark:bg-gray-700 p-2 rounded text-sm">
                已选择数据集ID: {observationSource.datasetId}
              </div>
            ) : observationSource.opendapPath ? (
              <div className="bg-gray-50 dark:bg-gray-700 p-2 rounded text-sm">
                已选择OPeNDAP路径: {observationSource.opendapPath}
              </div>
            ) : (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded text-sm text-yellow-700 dark:text-yellow-300">
                未选择观测数据, 请点击"选择数据集"
              </div>
            )}
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center mb-1">
              <label className="block text-sm font-medium">插值位置</label>
              <button 
                onClick={() => openDatasetSelector('interpolation')}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                选择数据集
              </button>
            </div>
                {interpolationSource.datasetId ? (
                  <div className="bg-gray-50 dark:bg-gray-700 p-2 rounded text-sm">
                    已选择数据集ID: {interpolationSource.datasetId}
                  </div>
                ) : interpolationSource.opendapPath ? (
                  <div className="bg-gray-50 dark:bg-gray-700 p-2 rounded text-sm">
                    已选择OPeNDAP路径: {interpolationSource.opendapPath}
                  </div>
                ) : (
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded text-sm text-yellow-700 dark:text-yellow-300">
                    未选择插值位置数据, 请点击"选择数据集"
                  </div>
                )}
              </div>
          
          <div className="space-y-2">
            <label className="block text-sm font-medium">信号方差 sigma2</label>
            <input 
              className="input"
              value={oiParams.sigma2} 
              onChange={e => handleParamChange('sigma2', e.target.value)}
              type="number"
              step="0.1"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium">相关长度 L</label>
            <input 
              className="input"
              value={oiParams.L} 
              onChange={e => handleParamChange('L', e.target.value)}
              type="number"
              step="0.1"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium">噪声 noise</label>
            <input 
              className="input"
              value={oiParams.noise} 
              onChange={e => handleParamChange('noise', e.target.value)}
              type="number"
              step="0.000001"
            />
          </div>
        </div>
      );
    } else {
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium">观测序列 observations (如 [[1.0],[2.0],[1.5]])</label>
            <input 
              className="input"
              value={kalmanParams.observations} 
              onChange={e => handleParamChange('observations', e.target.value)}
              placeholder="[[1.0],[2.0],[1.5]]"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium">初始状态 initial_state (如 [1.0])</label>
            <input 
              className="input"
              value={kalmanParams.initial_state} 
              onChange={e => handleParamChange('initial_state', e.target.value)}
              placeholder="[1.0]"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium">初始协方差 initial_cov (如 [[1.0]])</label>
            <input 
              className="input"
              value={kalmanParams.initial_cov} 
              onChange={e => handleParamChange('initial_cov', e.target.value)}
              placeholder="[[1.0]]"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium">转移矩阵 transition_matrix (如 [[1.0]])</label>
            <input 
              className="input"
              value={kalmanParams.transition_matrix} 
              onChange={e => handleParamChange('transition_matrix', e.target.value)}
              placeholder="[[1.0]]"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium">观测矩阵 observation_matrix (如 [[1.0]])</label>
            <input 
              className="input"
              value={kalmanParams.observation_matrix} 
              onChange={e => handleParamChange('observation_matrix', e.target.value)}
              placeholder="[[1.0]]"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium">过程噪声 process_noise (如 [[0.01]])</label>
            <input 
              className="input"
              value={kalmanParams.process_noise} 
              onChange={e => handleParamChange('process_noise', e.target.value)}
              placeholder="[[0.01]]"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium">观测噪声 observation_noise (如 [[0.1]])</label>
            <input 
              className="input"
              value={kalmanParams.observation_noise} 
              onChange={e => handleParamChange('observation_noise', e.target.value)}
              placeholder="[[0.1]]"
            />
          </div>
        </div>
      );
    }
  };

  // 结果可视化（简单表格/JSON）
  const renderResult = () => {
    if (!result) return null;
    return (
      <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded">
        <h3 className="font-bold mb-2">融合结果</h3>
        <pre className="text-xs whitespace-pre-wrap overflow-auto p-2 bg-white dark:bg-gray-800 rounded">{JSON.stringify(result, null, 2)}</pre>
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">数据融合任务配置</h1>
      
      <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm mb-6 card">
        <div className="mb-6">
          <label className="block mb-2 font-medium">融合算法选择</label>
          <select
            className="input"
            value={algorithm}
            onChange={e => setAlgorithm(e.target.value)}
          >
            {ALGORITHM_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        
        {algorithm === 'optimal_interpolation' && (
          <div className="mb-6">
            <label className="block mb-2 font-medium">数据输入方式</label>
            <div className="flex items-center space-x-4">
              <button
                type="button"
                onClick={() => openDatasetSelector('observation')}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
                </svg>
                选择数据集
              </button>
              {observationSource.datasetId && (
                <span className="text-sm text-gray-600">
                  已选择数据集ID: {observationSource.datasetId}
                </span>
              )}
            </div>
          </div>
        )}
        
        <div className="mb-6">
          <h2 className="text-lg font-medium mb-4">参数配置</h2>
          {renderParamsForm()}
        </div>
        
        <div className="flex items-center space-x-4">
          <button 
            onClick={handleSubmit}
            disabled={loading}
            className="btn btn-primary px-4 py-2"
          >
            {loading ? '提交中...' : '提交融合任务'}
          </button>
          
          {taskId && taskStatus && taskStatus.status === 'running' && (
            <div className="text-sm text-blue-600 dark:text-blue-400 flex items-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-600 dark:text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              处理中...
            </div>
          )}
          
          {error && (
            <div className="text-sm text-red-600 dark:text-red-400">
              错误: {error}
            </div>
          )}
        </div>
      </div>
      
      {renderResult()}
    </div>
  );
};

export default FusionConfig;
