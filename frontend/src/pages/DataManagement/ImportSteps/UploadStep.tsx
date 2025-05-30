import React from 'react';
import { useImportWizard } from '../../../hooks/useImportWizard';
import FileUploader from '../../../components/common/FileUploader';

const UploadStep: React.FC = () => {
  const { updateWizardData, wizardData } = useImportWizard();

  const handleFileSelect = (file: File) => {
    updateWizardData({ file });
    // TODO: 实际的文件上传逻辑
    console.log('Selected file:', file);
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

      <FileUploader
        onFileSelect={handleFileSelect}
        uploading={false}
        uploadProgress={0}
      />

      {wizardData.file && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="flex">
            <svg className="h-5 w-5 text-green-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800 dark:text-green-200">
                文件已选择
              </h3>
              <p className="text-sm text-green-700 dark:text-green-300">
                {wizardData.file.name} ({(wizardData.file.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadStep; 