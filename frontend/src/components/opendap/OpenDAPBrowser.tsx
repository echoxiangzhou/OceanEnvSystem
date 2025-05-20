import React, { useState } from 'react';
import { useOpenDAPData } from '../../hooks/useDataHooks';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface OpenDAPBrowserProps {
  onDatasetSelect?: (datasetPath: string, metadata: any) => void;
}

const OpenDAPBrowser: React.FC<OpenDAPBrowserProps> = ({ onDatasetSelect }) => {
  const [datasetPath, setDatasetPath] = useState<string>('');
  const [isExploring, setIsExploring] = useState<boolean>(false);

  // 使用钩子获取OPeNDAP数据
  const { data: openDAPData, isLoading, isError, error, refetch } = useOpenDAPData(datasetPath, {
    enabled: isExploring && !!datasetPath,
  });

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDatasetPath(e.target.value);
    setIsExploring(false);
  };

  // 处理浏览按钮点击
  const handleExplore = () => {
    if (!datasetPath) return;
    setIsExploring(true);
  };

  // 处理数据集选择
  const handleSelect = () => {
    if (openDAPData?.data && onDatasetSelect) {
      onDatasetSelect(datasetPath, openDAPData.data);
    }
  };

  // 示例数据集列表
  const exampleDatasets = [
    'thredds/dodsC/oceandata/temperature_2023.nc',
    'thredds/dodsC/oceandata/salinity_2023.nc',
    'thredds/dodsC/oceandata/ctd/station_01.nc',
  ];

  // 处理示例数据集点击
  const handleExampleClick = (example: string) => {
    setDatasetPath(example);
    setIsExploring(false);
  };

  // 基本的LoadingSpinner组件
  const LoadingSpinner = ({ size = 'md', text = '加载中...', fullScreen = false }) => {
    const sizeClasses = {
      sm: 'w-4 h-4',
      md: 'w-8 h-8',
      lg: 'w-12 h-12',
    };

    const spinner = (
      <div className="flex flex-col items-center justify-center space-y-2">
        <div className={`animate-spin rounded-full border-t-2 border-b-2 border-blue-500 ${sizeClasses[size]}`}></div>
        {text && <p className="text-sm text-gray-600 dark:text-gray-400">{text}</p>}
      </div>
    );

    if (fullScreen) {
      return (
        <div className="fixed inset-0 bg-white bg-opacity-75 dark:bg-gray-900 dark:bg-opacity-75 flex items-center justify-center z-50">
          {spinner}
        </div>
      );
    }

    return spinner;
  };

  // 基本的ErrorMessage组件
  const ErrorMessage = ({ message, retry }) => {
    return (
      <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4 my-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800 dark:text-red-200">发生错误</h3>
            <div className="mt-2 text-sm text-red-700 dark:text-red-300">
              <p>{message}</p>
            </div>
            {retry && (
              <div className="mt-4">
                <button
                  type="button"
                  onClick={retry}
                  className="rounded-md bg-red-50 dark:bg-red-900/30 px-3 py-2 text-sm font-medium text-red-800 dark:text-red-200 hover:bg-red-100 dark:hover:bg-red-900/50 focus:outline-none"
                >
                  重试
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div className="p-5">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">OPeNDAP数据浏览器</h3>
        
        <div className="mb-6">
          <label htmlFor="dataset-path" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            数据集路径
          </label>
          <div className="mt-1 flex rounded-md shadow-sm">
            <input
              type="text"
              id="dataset-path"
              value={datasetPath}
              onChange={handleInputChange}
              className="flex-1 min-w-0 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="例如：thredds/dodsC/oceandata/temperature.nc"
            />
            <button
              type="button"
              onClick={handleExplore}
              disabled={!datasetPath || isLoading}
              className="ml-3 inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 disabled:cursor-not-allowed"
            >
              浏览
            </button>
          </div>
        </div>

        {/* 示例数据集 */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">示例数据集</h4>
          <div className="space-y-2">
            {exampleDatasets.map((example, index) => (
              <button
                key={index}
                onClick={() => handleExampleClick(example)}
                className="block text-left w-full text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 truncate"
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        {/* 加载状态 */}
        {isLoading && (
          <div className="py-6">
            <LoadingSpinner text="连接OPeNDAP服务..." />
          </div>
        )}

        {/* 错误信息 */}
        {isError && (
          <ErrorMessage 
            message={`无法获取数据集信息: ${error?.message || '连接失败'}`} 
            retry={refetch}
          />
        )}

        {/* 数据集元数据 */}
        {!isLoading && !isError && openDAPData?.data && (
          <div className="mt-4">
            <h4 className="text-md font-medium text-gray-800 dark:text-gray-200 mb-3">数据集元数据</h4>
            
            {/* 变量信息 */}
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">变量</h5>
              <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
                <ul className="list-disc list-inside space-y-1">
                  {openDAPData.data.variables?.map((variable: string, idx: number) => (
                    <li key={idx} className="text-sm text-gray-600 dark:text-gray-300">{variable}</li>
                  ))}
                </ul>
                {(!openDAPData.data.variables || openDAPData.data.variables.length === 0) && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">没有变量信息</p>
                )}
              </div>
            </div>
            
            {/* 维度信息 */}
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">维度</h5>
              <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
                {openDAPData.data.dims && Object.keys(openDAPData.data.dims).length > 0 ? (
                  <ul className="space-y-1">
                    {Object.entries(openDAPData.data.dims).map(([name, size]) => (
                      <li key={name} className="text-sm text-gray-600 dark:text-gray-300">
                        <span className="font-medium">{name}</span>: {size}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500 dark:text-gray-400">没有维度信息</p>
                )}
              </div>
            </div>
            
            {/* 属性信息 */}
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">全局属性</h5>
              <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md max-h-60 overflow-y-auto">
                {openDAPData.data.attrs && Object.keys(openDAPData.data.attrs).length > 0 ? (
                  <dl className="grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-2">
                    {Object.entries(openDAPData.data.attrs).map(([name, value]) => (
                      <div key={name} className="col-span-1 sm:col-span-2">
                        <dt className="text-sm font-medium text-gray-700 dark:text-gray-300">{name}</dt>
                        <dd className="text-sm text-gray-500 dark:text-gray-400 break-words">{String(value)}</dd>
                      </div>
                    ))}
                  </dl>
                ) : (
                  <p className="text-sm text-gray-500 dark:text-gray-400">没有全局属性信息</p>
                )}
              </div>
            </div>
            
            {/* 选择按钮 */}
            {onDatasetSelect && (
              <div className="mt-6 flex justify-end">
                <button
                  type="button"
                  onClick={handleSelect}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  选择此数据集
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default OpenDAPBrowser;
