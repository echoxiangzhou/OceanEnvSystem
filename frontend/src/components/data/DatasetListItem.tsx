import React from 'react';
import { Dataset } from '../../types/api';

interface DatasetListItemProps {
  dataset: Dataset;
  onView: (dataset: Dataset) => void;
  onDelete: (dataset: Dataset) => void;
}

const DatasetListItem: React.FC<DatasetListItemProps> = ({ dataset, onView, onDelete }) => {
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

  // 获取数据类型的中文显示
  const getSourceTypeLabel = (type: Dataset['source_type']) => {
    const labels = {
      'BUOY': '浮标',
      'SURVEY': '调查',
      'SATELLITE': '卫星',
      'MODEL': '模型'
    };
    return labels[type] || type;
  };

  // 获取数据种类的中文显示
  const getDataTypeLabel = (type: Dataset['data_type']) => {
    const labels = {
      'OBSERVATIONS': '观测',
      'FORECAST': '预报',
      'REANALYSIS': '再分析'
    };
    return labels[type] || type;
  };

  // 变量列表显示
  const variablesList = dataset.variables.map(v => v.name).join(', ');

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden mb-4 transition-all hover:shadow-md">
      <div className="p-5">
        <div className="flex justify-between items-start">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">{dataset.name}</h3>
          <div className="flex space-x-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
              {getSourceTypeLabel(dataset.source_type)}
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
              {getDataTypeLabel(dataset.data_type)}
            </span>
          </div>
        </div>
        
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">{dataset.description}</p>
        
        <div className="mt-3 grid grid-cols-2 gap-4 text-xs text-gray-500 dark:text-gray-400">
          <div>
            <p className="font-medium text-gray-700 dark:text-gray-300">文件格式</p>
            <p>{dataset.file_format.toUpperCase()}</p>
          </div>
          <div>
            <p className="font-medium text-gray-700 dark:text-gray-300">文件路径</p>
            <p className="truncate">{dataset.file_location}</p>
          </div>
          <div>
            <p className="font-medium text-gray-700 dark:text-gray-300">创建时间</p>
            <p>{formatDate(dataset.created_at)}</p>
          </div>
          <div>
            <p className="font-medium text-gray-700 dark:text-gray-300">更新时间</p>
            <p>{formatDate(dataset.updated_at)}</p>
          </div>
        </div>
        
        <div className="mt-3">
          <p className="text-xs font-medium text-gray-700 dark:text-gray-300">变量</p>
          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{variablesList || '无变量信息'}</p>
        </div>
        
        <div className="mt-4 flex justify-end space-x-3">
          <button
            onClick={() => onView(dataset)}
            className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800 transition-colors"
          >
            查看详情
          </button>
          <button
            onClick={() => onDelete(dataset)}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-xs font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:focus:ring-offset-gray-800 transition-colors"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  );
};

export default DatasetListItem;
