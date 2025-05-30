import React, { useState, useEffect } from 'react';
import { useImportWizard } from '../../../hooks/useImportWizard';
import importService, { DataPreview } from '../../../services/importService';
import LoadingSpinner from '../../../components/common/LoadingSpinner';
import ErrorMessage from '../../../components/common/ErrorMessage';

const PreviewStep: React.FC = () => {
  const { updateWizardData, wizardData } = useImportWizard();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<DataPreview | null>(null);

  // 加载数据预览
  useEffect(() => {
    const loadPreview = async () => {
      if (!wizardData.tempId) {
        setError('未找到临时文件ID，请重新上传文件');
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        const data = await importService.getDataPreview(wizardData.tempId);
        setPreviewData(data);
        
        // 更新向导数据
        updateWizardData({ previewData: data });
        
      } catch (error: any) {
        console.error('获取数据预览失败:', error);
        setError(
          error.response?.data?.detail || 
          error.message || 
          '获取数据预览失败，请重试'
        );
      } finally {
        setLoading(false);
      }
    };

    loadPreview();
  }, [wizardData.tempId, updateWizardData]);

  const handleRetry = () => {
    if (wizardData.tempId) {
      setError(null);
      // 重新触发useEffect
      updateWizardData({ previewData: undefined });
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            数据预览
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            正在解析文件内容，请稍候...
          </p>
        </div>
        
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-gray-600 dark:text-gray-400">
            正在加载数据预览...
          </span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            数据预览
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            预览数据内容并检查解析结果。
          </p>
        </div>
        
        <ErrorMessage message={error} retry={handleRetry} />
      </div>
    );
  }

  if (!previewData) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            数据预览
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            未找到数据预览信息。
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          数据预览
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          预览数据内容并检查解析结果。检查变量名称、数据类型和建议的CF标准映射。
        </p>
      </div>

      {/* 文件基本信息 */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">文件信息</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">数据行数</dt>
            <dd className="mt-1 text-sm text-gray-900 dark:text-white">{previewData.row_count.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">变量数量</dt>
            <dd className="mt-1 text-sm text-gray-900 dark:text-white">{previewData.column_count}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">文件格式</dt>
            <dd className="mt-1 text-sm text-gray-900 dark:text-white">{previewData.parsing_config?.file_format?.toUpperCase() || '未知'}</dd>
          </div>
          {previewData.parsing_config?.instrument_type && (
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">仪器类型</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">{previewData.parsing_config.instrument_type?.toUpperCase() || '未知'}</dd>
            </div>
          )}
        </div>
      </div>

      {/* 变量信息 */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">变量信息</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            系统已自动识别变量类型并建议CF标准映射
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  变量名
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  数据类型
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  建议CF名称
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  建议单位
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  置信度
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  示例值
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {previewData.columns.map((column, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    {column.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {column.data_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {column.suggested_cf_name ? (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300">
                        {column.suggested_cf_name}
                      </span>
                    ) : (
                      <span className="text-gray-400">未识别</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {column.suggested_units || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    <div className="flex items-center">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${(column.confidence * 100)}%` }}
                        />
                      </div>
                      <span className="text-xs">{Math.round(column.confidence * 100)}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                    <div className="max-w-xs overflow-hidden">
                      {column.sample_values.slice(0, 3).join(', ')}
                      {column.sample_values.length > 3 && '...'}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 数据预览表格 */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">数据预览</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            前 {previewData.preview_data.length} 行数据
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                {previewData.columns.map((column, index) => (
                  <th key={index} className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {column.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {previewData.preview_data.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {previewData.columns.map((column, colIndex) => (
                    <td key={colIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {row[column.name] ?? '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 质量报告 */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">数据质量报告</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">缺失数据</h4>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {previewData.quality_report.missing_data_percentage.toFixed(1)}%
            </p>
          </div>
          {Object.keys(previewData.quality_report.anomalies).length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">发现的异常</h4>
              <div className="space-y-1">
                {Object.entries(previewData.quality_report.anomalies).map(([type, messages]) => (
                  <div key={type} className="text-sm text-yellow-600 dark:text-yellow-400">
                    {type}: {messages.length} 个问题
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PreviewStep; 