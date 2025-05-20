import React, { useState } from 'react';
import { Dataset } from '../../types/api';

interface DatasetDetailModalProps {
  dataset: Dataset | null;
  isOpen: boolean;
  onClose: () => void;
  onDownload: (dataset: Dataset) => void;
}

const DatasetDetailModal: React.FC<DatasetDetailModalProps> = ({ 
  dataset, 
  isOpen, 
  onClose, 
  onDownload 
}) => {
  const [activeTab, setActiveTab] = useState<'basic' | 'variables' | 'spatial' | 'temporal'>('basic');

  if (!isOpen || !dataset) return null;

  // 格式化日期显示
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  // 绘制变量表格
  const renderVariablesTable = () => (
    <div className="overflow-x-auto mt-4">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">名称</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">标准名称</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">单位</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">描述</th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
          {dataset.variables.map((variable, index) => (
            <tr key={`${variable.name}-${index}`} className={index % 2 === 0 ? 'bg-white dark:bg-gray-900' : 'bg-gray-50 dark:bg-gray-800'}>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{variable.name}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{variable.standard_name || '-'}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{variable.unit}</td>
              <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{variable.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  // 渲染基本信息标签页
  const renderBasicInfoTab = () => (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">数据集名称</h3>
        <p className="mt-1 text-sm text-gray-900 dark:text-white">{dataset.name}</p>
      </div>
      <div>
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">描述</h3>
        <p className="mt-1 text-sm text-gray-900 dark:text-white">{dataset.description}</p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">源类型</h3>
          <p className="mt-1 text-sm text-gray-900 dark:text-white">{dataset.source_type}</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">数据类型</h3>
          <p className="mt-1 text-sm text-gray-900 dark:text-white">{dataset.data_type}</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">文件格式</h3>
          <p className="mt-1 text-sm text-gray-900 dark:text-white">{dataset.file_format.toUpperCase()}</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">文件路径</h3>
          <p className="mt-1 text-sm text-gray-900 dark:text-white truncate">{dataset.file_location}</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">创建时间</h3>
          <p className="mt-1 text-sm text-gray-900 dark:text-white">{formatDate(dataset.created_at)}</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">更新时间</h3>
          <p className="mt-1 text-sm text-gray-900 dark:text-white">{formatDate(dataset.updated_at)}</p>
        </div>
      </div>
    </div>
  );

  // 渲染时间范围标签页
  const renderTemporalTab = () => (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">起始时间</h3>
        <p className="mt-1 text-sm text-gray-900 dark:text-white">{formatDate(dataset.temporal_coverage.start)}</p>
      </div>
      <div>
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">结束时间</h3>
        <p className="mt-1 text-sm text-gray-900 dark:text-white">{formatDate(dataset.temporal_coverage.end)}</p>
      </div>
      <div>
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">时间范围</h3>
        <p className="mt-1 text-sm text-gray-900 dark:text-white">
          {Math.round((new Date(dataset.temporal_coverage.end).getTime() - new Date(dataset.temporal_coverage.start).getTime()) / (1000 * 60 * 60 * 24))} 天
        </p>
      </div>
    </div>
  );

  // 渲染空间范围标签页
  const renderSpatialTab = () => {
    // 简单显示坐标范围，实际应用中可能需要地图可视化
    const coordinates = dataset.spatial_coverage.coordinates[0];
    
    // 计算经纬度范围
    let minLon = Infinity, maxLon = -Infinity, minLat = Infinity, maxLat = -Infinity;
    
    coordinates.forEach(([lon, lat]) => {
      minLon = Math.min(minLon, lon);
      maxLon = Math.max(maxLon, lon);
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
    });

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">最小经度</h3>
            <p className="mt-1 text-sm text-gray-900 dark:text-white">{minLon.toFixed(4)}°</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">最大经度</h3>
            <p className="mt-1 text-sm text-gray-900 dark:text-white">{maxLon.toFixed(4)}°</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">最小纬度</h3>
            <p className="mt-1 text-sm text-gray-900 dark:text-white">{minLat.toFixed(4)}°</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">最大纬度</h3>
            <p className="mt-1 text-sm text-gray-900 dark:text-white">{maxLat.toFixed(4)}°</p>
          </div>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">空间类型</h3>
          <p className="mt-1 text-sm text-gray-900 dark:text-white">{dataset.spatial_coverage.type}</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">坐标点数</h3>
          <p className="mt-1 text-sm text-gray-900 dark:text-white">{coordinates.length}</p>
        </div>
      </div>
    );
  };

  // 渲染当前活动标签页内容
  const renderActiveTabContent = () => {
    switch (activeTab) {
      case 'basic':
        return renderBasicInfoTab();
      case 'variables':
        return renderVariablesTable();
      case 'temporal':
        return renderTemporalTab();
      case 'spatial':
        return renderSpatialTab();
      default:
        return null;
    }
  };

  return (
    <div className="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* 背景遮罩 */}
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 dark:bg-gray-900 dark:bg-opacity-75 transition-opacity" aria-hidden="true" onClick={onClose}></div>

        {/* 使模态框居中 */}
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        {/* 模态框内容 */}
        <div className="relative inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
          <div className="px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="sm:flex sm:items-start">
              <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white" id="modal-title">
                  数据集详情
                </h3>
                
                {/* 标签页导航 */}
                <div className="mt-4 border-b border-gray-200 dark:border-gray-700">
                  <nav className="flex -mb-px space-x-8" aria-label="Tabs">
                    <button
                      onClick={() => setActiveTab('basic')}
                      className={`${
                        activeTab === 'basic'
                          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                          : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                      } whitespace-nowrap pb-3 px-1 border-b-2 font-medium text-sm`}
                    >
                      基本信息
                    </button>
                    <button
                      onClick={() => setActiveTab('variables')}
                      className={`${
                        activeTab === 'variables'
                          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                          : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                      } whitespace-nowrap pb-3 px-1 border-b-2 font-medium text-sm`}
                    >
                      变量列表
                    </button>
                    <button
                      onClick={() => setActiveTab('temporal')}
                      className={`${
                        activeTab === 'temporal'
                          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                          : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                      } whitespace-nowrap pb-3 px-1 border-b-2 font-medium text-sm`}
                    >
                      时间范围
                    </button>
                    <button
                      onClick={() => setActiveTab('spatial')}
                      className={`${
                        activeTab === 'spatial'
                          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                          : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                      } whitespace-nowrap pb-3 px-1 border-b-2 font-medium text-sm`}
                    >
                      空间范围
                    </button>
                  </nav>
                </div>

                {/* 标签页内容 */}
                <div className="mt-4">
                  {renderActiveTabContent()}
                </div>
              </div>
            </div>
          </div>
          
          {/* 底部按钮 */}
          <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={() => onDownload(dataset)}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              下载数据文件
            </button>
            <button
              type="button"
              onClick={onClose}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-gray-600 shadow-sm px-4 py-2 bg-white dark:bg-gray-800 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DatasetDetailModal;
