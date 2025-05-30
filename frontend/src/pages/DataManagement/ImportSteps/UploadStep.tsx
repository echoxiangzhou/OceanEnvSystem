import React, { useState } from 'react';
import { useImportWizard } from '../../../hooks/useImportWizard.tsx';
import FileUploader from '../../../components/common/FileUploader';
import importService, { FileUploadResponse } from '../../../services/importService';
import LoadingSpinner from '../../../components/common/LoadingSpinner';
import ErrorMessage from '../../../components/common/ErrorMessage';

const UploadStep: React.FC = () => {
  const { updateWizardData, wizardData } = useImportWizard();
  
  // 上传状态
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResponse, setUploadResponse] = useState<FileUploadResponse | null>(null);

  const handleFileSelect = async (file: File) => {
    let progressInterval: NodeJS.Timeout | null = null;
    
    try {
      setUploading(true);
      setUploadError(null);
      setUploadProgress(0);
      
      // 模拟上传进度（因为axios不支持原生的上传进度，这里做简单模拟）
      progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            if (progressInterval) clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      // 调用上传API
      const response = await importService.uploadFile(file);
      
      // 清除进度定时器
      if (progressInterval) clearInterval(progressInterval);
      setUploadProgress(100);
      
      // 保存上传响应
      setUploadResponse(response);
      
      // 一次性更新所有向导数据，避免竞争条件
      const wizardUpdate = {
        tempId: response.temp_id,
        file,
        fileType: response.file_type,
        uploadResponse: response
      };
      updateWizardData(wizardUpdate);
      
    } catch (error: any) {
      console.error('文件上传失败:', error);
      
      // 清除进度定时器
      if (progressInterval) clearInterval(progressInterval);
      
      setUploadError(
        error.response?.data?.detail || 
        error.message || 
        '文件上传失败，请重试'
      );
    } finally {
      setUploading(false);
    }
  };

  const handleRetryUpload = () => {
    if (wizardData.file) {
      handleFileSelect(wizardData.file);
    }
  };

  const handleRemoveFile = () => {
    // 一次性清除所有相关状态
    updateWizardData({ 
      file: undefined, 
      tempId: undefined,
      fileType: undefined,
      uploadResponse: undefined
    });
    setUploadResponse(null);
    setUploadError(null);
    setUploadProgress(0);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          上传数据文件
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          选择要导入的数据文件。支持 CSV、Excel、CNV 和 NetCDF 格式。
        </p>
      </div>

      {/* 文件上传器 */}
      <FileUploader
        onFileSelect={handleFileSelect}
        uploading={uploading}
        uploadProgress={uploadProgress}
      />

      {/* 上传错误信息 */}
      {uploadError && (
        <ErrorMessage 
          message={uploadError}
          retry={handleRetryUpload}
        />
      )}

      {/* 上传成功信息 */}
      {uploadResponse && !uploading && (
        <div className="space-y-4">
          {/* 文件信息 */}
          <div className={`border rounded-lg p-4 ${
            uploadResponse.parse_status === 'success' 
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
              : uploadResponse.parse_status === 'warning'
              ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
              : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
          }`}>
            <div className="flex items-start">
              <div className="flex-shrink-0">
                {uploadResponse.parse_status === 'success' ? (
                  <svg className="h-5 w-5 text-green-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                ) : uploadResponse.parse_status === 'warning' ? (
                  <svg className="h-5 w-5 text-yellow-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5 text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <div className="ml-3 flex-1">
                <h3 className={`text-sm font-medium ${
                  uploadResponse.parse_status === 'success' 
                    ? 'text-green-800 dark:text-green-200'
                    : uploadResponse.parse_status === 'warning'
                    ? 'text-yellow-800 dark:text-yellow-200'
                    : 'text-red-800 dark:text-red-200'
                }`}>
                  {uploadResponse.parse_status === 'success' ? '文件上传成功' :
                   uploadResponse.parse_status === 'warning' ? '文件上传成功（有警告）' :
                   '文件上传失败'}
                </h3>
                <div className={`mt-1 text-sm ${
                  uploadResponse.parse_status === 'success' 
                    ? 'text-green-700 dark:text-green-300'
                    : uploadResponse.parse_status === 'warning'
                    ? 'text-yellow-700 dark:text-yellow-300'
                    : 'text-red-700 dark:text-red-300'
                }`}>
                  <p><strong>文件名：</strong>{uploadResponse.filename}</p>
                  <p><strong>文件大小：</strong>{(uploadResponse.file_size / 1024 / 1024).toFixed(2)} MB</p>
                  <p><strong>文件类型：</strong>{uploadResponse.file_type.toUpperCase()}</p>
                  <p><strong>临时ID：</strong>{uploadResponse.temp_id}</p>
                  {uploadResponse.parse_message && (
                    <p><strong>状态：</strong>{uploadResponse.parse_message}</p>
                  )}
                </div>
              </div>
              <button
                type="button"
                onClick={handleRemoveFile}
                className="ml-4 text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                title="移除文件"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>

          {/* 下一步提示 */}
          {uploadResponse.parse_status === 'success' && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex">
                <svg className="h-5 w-5 text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800 dark:text-blue-200">
                    准备就绪
                  </h3>
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    文件已成功上传并通过初步检查。点击"下一步"进入数据预览阶段。
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 上传中状态 */}
      {uploading && (
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-gray-600 dark:text-gray-400">
            正在上传文件，请稍候...
          </span>
        </div>
      )}
    </div>
  );
};

export default UploadStep; 