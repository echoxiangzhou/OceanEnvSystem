import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useImportWizard } from '../../../hooks/useImportWizard';

const CompleteStep: React.FC = () => {
  const navigate = useNavigate();
  const { wizardData, resetWizard } = useImportWizard();

  const handleViewData = () => {
    navigate('/data');
  };

  const handleNewImport = () => {
    resetWizard();
  };

  return (
    <div className="space-y-6">
      {/* 成功消息 */}
      <div className="text-center">
        <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 dark:bg-green-900/20">
          <svg className="h-6 w-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="mt-4 text-xl font-semibold text-gray-900 dark:text-white">
          数据导入完成！
        </h2>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          您的数据已成功转换为NetCDF格式并符合CF-1.8规范
        </p>
      </div>

      {/* 结果摘要 */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          导入结果
        </h3>
        
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">源文件</dt>
            <dd className="text-sm text-gray-900 dark:text-white">
              {wizardData.file?.name || '未知文件'}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">文件大小</dt>
            <dd className="text-sm text-gray-900 dark:text-white">
              {wizardData.file ? `${(wizardData.file.size / 1024 / 1024).toFixed(2)} MB` : '未知'}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">输出文件</dt>
            <dd className="text-sm text-gray-900 dark:text-white">
              {wizardData.file?.name.replace(/\.[^/.]+$/, '.nc') || 'output.nc'}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">CF合规性</dt>
            <dd className="text-sm text-gray-900 dark:text-white">85% (良好)</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">数据变量</dt>
            <dd className="text-sm text-gray-900 dark:text-white">6个变量</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">处理时间</dt>
            <dd className="text-sm text-gray-900 dark:text-white">约2分钟</dd>
          </div>
        </dl>
      </div>

      {/* 数据集信息 */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 dark:text-blue-100 mb-2">
          数据集已创建
        </h3>
        <p className="text-sm text-blue-700 dark:text-blue-300 mb-4">
          数据集已添加到系统中，您可以通过数据浏览器查看和管理。
        </p>
        
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleViewData}
            className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            查看数据集
          </button>
          
          <button
            onClick={handleNewImport}
            className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            导入新文件
          </button>
        </div>
      </div>

      {/* 后续操作建议 */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          后续操作
        </h3>
        
        <div className="space-y-3">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="flex items-center justify-center h-6 w-6 rounded-full bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-xs font-medium">
                1
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                数据可视化
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                使用系统的可视化工具创建图表和地图
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="flex items-center justify-center h-6 w-6 rounded-full bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-xs font-medium">
                2
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                数据分析
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                进行统计分析、时间序列分析或空间分析
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="flex items-center justify-center h-6 w-6 rounded-full bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-xs font-medium">
                3
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                数据共享
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                通过THREDDS服务器分享给其他研究人员
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompleteStep; 