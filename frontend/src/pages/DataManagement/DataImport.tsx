import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ImportWizardProvider, useImportWizard } from '../../hooks/useImportWizard.tsx';
import StepIndicator from '../../components/common/StepIndicator';
import { 
  UploadStep, 
  PreviewStep, 
  MetadataStep, 
  ValidateStep, 
  CompleteStep 
} from './ImportSteps';

const DataImportContent: React.FC = () => {
  const navigate = useNavigate();
  const {
    steps,
    currentStepId,
    wizardData,
    isFirstStep,
    isLastStep,
    nextStep,
    previousStep,
    resetWizard,
    canProceed
  } = useImportWizard();

  // 渲染当前步骤内容
  const renderCurrentStep = () => {
    switch (currentStepId) {
      case 'upload':
        return <UploadStep />;
      case 'preview':
        return <PreviewStep />;
      case 'metadata':
        return <MetadataStep />;
      case 'validate':
        return <ValidateStep />;
      case 'complete':
        return <CompleteStep />;
      default:
        return <UploadStep />;
    }
  };

  // 实时检查canProceed结果
  const currentCanProceed = canProceed(currentStepId);
  const isDisabled = isLastStep || !currentCanProceed;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* 页面头部 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">数据导入向导</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            按照步骤完成数据文件的导入和转换
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={resetWizard}
            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800"
          >
            重新开始
          </button>
          <button
            onClick={() => navigate('/data')}
            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800"
          >
            返回数据浏览
          </button>
        </div>
      </div>

      {/* 步骤指示器 */}
      <StepIndicator steps={steps as any} currentStep={currentStepId} />

      {/* 主要内容区域 */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div className="px-6 py-8">
          {renderCurrentStep()}
        </div>

        {/* 底部导航按钮 */}
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700 flex justify-between">
          <button
            onClick={previousStep}
            disabled={isFirstStep}
            className={`inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-sm font-medium rounded-md ${
              isFirstStep
                ? 'text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-gray-700 cursor-not-allowed'
                : 'text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800'
            }`}
          >
            <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            上一步
          </button>

          <button
            onClick={nextStep}
            disabled={isDisabled}
            className={`inline-flex items-center px-4 py-2 border shadow-sm text-sm font-medium rounded-md ${
              isDisabled
                ? 'text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 cursor-not-allowed'
                : 'text-white bg-blue-600 border-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800'
            }`}
          >
            {isLastStep ? '已完成' : '下一步'}
            {!isLastStep && (
              <svg className="ml-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

const DataImport: React.FC = () => {
  return (
    <ImportWizardProvider>
      <DataImportContent />
    </ImportWizardProvider>
  );
};

export default DataImport;