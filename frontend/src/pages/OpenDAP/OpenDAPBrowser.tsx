import React, { useState } from 'react';
import OpenDAPBrowser from '../../components/opendap/OpenDAPBrowser';
import { DatasetMetadata } from '../../types/api';
import { useRegisterDataset } from '../../hooks/useDataHooks';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';

const OpenDAPPage: React.FC = () => {
  const [selectedDataset, setSelectedDataset] = useState<{ path: string; metadata: DatasetMetadata } | null>(null);
  const [isRegistering, setIsRegistering] = useState(false);
  const [registrationForm, setRegistrationForm] = useState({
    name: '',
    description: '',
    source_type: 'MODEL' as const,
    data_type: 'OBSERVATIONS' as const,
    spatial_coverage: {
      type: 'Polygon',
      coordinates: [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
    },
    temporal_coverage: {
      start: new Date().toISOString(),
      end: new Date().toISOString()
    }
  });

  // 使用注册数据集的钩子
  const { mutate: registerDataset, isPending, isSuccess, error } = useRegisterDataset({
    onSuccess: () => {
      setIsRegistering(false);
      // 重置表单
      setRegistrationForm({
        name: '',
        description: '',
        source_type: 'MODEL',
        data_type: 'OBSERVATIONS',
        spatial_coverage: {
          type: 'Polygon',
          coordinates: [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
        },
        temporal_coverage: {
          start: new Date().toISOString(),
          end: new Date().toISOString()
        }
      });
      setSelectedDataset(null);
    }
  });

  // 处理数据集选择
  const handleDatasetSelect = (path: string, metadata: DatasetMetadata) => {
    setSelectedDataset({ path, metadata });
    
    // 自动填充表单
    const pathParts = path.split('/');
    const fileName = pathParts[pathParts.length - 1];
    const name = fileName.replace(/\.[^/.]+$/, ""); // 去除文件扩展名

    setRegistrationForm(prev => ({
      ...prev,
      name,
      description: `通过OPeNDAP远程访问的数据集：${path}`
    }));
  };

  // 处理表单输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setRegistrationForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // 处理日期输入变化
  const handleDateChange = (field: 'start' | 'end', value: string) => {
    setRegistrationForm(prev => ({
      ...prev,
      temporal_coverage: {
        ...prev.temporal_coverage,
        [field]: new Date(value).toISOString()
      }
    }));
  };

  // 处理表单提交
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDataset) return;

    const variables = selectedDataset.metadata.variables.map(name => ({
      name,
      unit: '未知',
      description: `变量：${name}`
    }));

    registerDataset({
      ...registrationForm,
      variables,
      file_format: 'nc',
      file_location: selectedDataset.path
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">OPeNDAP远程数据浏览</h1>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* OPeNDAP浏览器 */}
        <div>
          <OpenDAPBrowser onDatasetSelect={handleDatasetSelect} />
        </div>
        
        {/* 数据集注册表单 */}
        <div>
          {selectedDataset ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
              <div className="p-5">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  注册远程数据集
                </h3>

                {isPending && (
                  <div className="mb-4">
                    <LoadingSpinner text="注册中..." />
                  </div>
                )}

                {isSuccess && (
                  <div className="mb-4 rounded-md bg-green-50 dark:bg-green-900/20 p-4">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-green-800 dark:text-green-200">
                          数据集注册成功！
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {error && (
                  <ErrorMessage message={`注册失败: ${error?.message || '未知错误'}`} />
                )}

                <form onSubmit={handleSubmit}>
                  <div className="space-y-4">
                    {/* 数据集名称 */}
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        数据集名称 *
                      </label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        required
                        value={registrationForm.name}
                        onChange={handleInputChange}
                        className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                    </div>

                    {/* 数据集描述 */}
                    <div>
                      <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        描述 *
                      </label>
                      <textarea
                        id="description"
                        name="description"
                        rows={3}
                        required
                        value={registrationForm.description}
                        onChange={handleInputChange}
                        className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                    </div>

                    {/* 源类型和数据类型 */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="source_type" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                          源类型 *
                        </label>
                        <select
                          id="source_type"
                          name="source_type"
                          required
                          value={registrationForm.source_type}
                          onChange={handleInputChange}
                          className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        >
                          <option value="BUOY">浮标</option>
                          <option value="SURVEY">调查</option>
                          <option value="SATELLITE">卫星</option>
                          <option value="MODEL">模型</option>
                        </select>
                      </div>
                      <div>
                        <label htmlFor="data_type" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                          数据类型 *
                        </label>
                        <select
                          id="data_type"
                          name="data_type"
                          required
                          value={registrationForm.data_type}
                          onChange={handleInputChange}
                          className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        >
                          <option value="OBSERVATIONS">观测</option>
                          <option value="FORECAST">预报</option>
                          <option value="REANALYSIS">再分析</option>
                        </select>
                      </div>
                    </div>

                    {/* 时间范围 */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">时间范围 *</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label htmlFor="start_time" className="block text-xs text-gray-500 dark:text-gray-400">
                            开始时间
                          </label>
                          <input
                            type="datetime-local"
                            id="start_time"
                            required
                            value={new Date(registrationForm.temporal_coverage.start).toISOString().slice(0, 16)}
                            onChange={(e) => handleDateChange('start', e.target.value)}
                            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          />
                        </div>
                        <div>
                          <label htmlFor="end_time" className="block text-xs text-gray-500 dark:text-gray-400">
                            结束时间
                          </label>
                          <input
                            type="datetime-local"
                            id="end_time"
                            required
                            value={new Date(registrationForm.temporal_coverage.end).toISOString().slice(0, 16)}
                            onChange={(e) => handleDateChange('end', e.target.value)}
                            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          />
                        </div>
                      </div>
                    </div>

                    {/* 变量信息 */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">变量信息</h4>
                      <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md max-h-48 overflow-y-auto">
                        {selectedDataset.metadata.variables?.length > 0 ? (
                          <ul className="list-disc list-inside space-y-1">
                            {selectedDataset.metadata.variables.map((variable, idx) => (
                              <li key={idx} className="text-sm text-gray-600 dark:text-gray-300">{variable}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-sm text-gray-500 dark:text-gray-400">没有变量信息</p>
                        )}
                      </div>
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        注册后将自动创建这些变量的基本信息
                      </p>
                    </div>

                    {/* 提交按钮 */}
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={isPending}
                        className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
                          isPending ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'
                        } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
                      >
                        {isPending ? '注册中...' : '注册数据集'}
                      </button>
                    </div>
                  </div>
                </form>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">选择数据集</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                请在左侧使用OPeNDAP浏览器浏览并选择一个远程数据集。
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OpenDAPPage;
