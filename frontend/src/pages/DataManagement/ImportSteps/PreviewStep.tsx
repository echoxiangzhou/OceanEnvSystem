import React from 'react';
import { useImportWizard } from '../../../hooks/useImportWizard';

const PreviewStep: React.FC = () => {
  const { wizardData } = useImportWizard();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          数据预览
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          预览和验证上传的数据内容，确认数据格式正确。
        </p>
      </div>

      {wizardData.file ? (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            文件信息
          </h3>
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">文件名</dt>
              <dd className="text-sm text-gray-900 dark:text-white">{wizardData.file.name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">文件大小</dt>
              <dd className="text-sm text-gray-900 dark:text-white">
                {(wizardData.file.size / 1024 / 1024).toFixed(2)} MB
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">文件类型</dt>
              <dd className="text-sm text-gray-900 dark:text-white">{wizardData.file.type || 'unknown'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">最后修改</dt>
              <dd className="text-sm text-gray-900 dark:text-white">
                {new Date(wizardData.file.lastModified).toLocaleString()}
              </dd>
            </div>
          </dl>
          
          <div className="mt-6">
            <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
              数据预览
            </h4>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                正在加载数据预览...
              </p>
              {/* TODO: 实际的数据预览组件 */}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">未选择文件</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            请先在上一步选择要预览的文件
          </p>
        </div>
      )}
    </div>
  );
};

export default PreviewStep; 