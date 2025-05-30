import { useState, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export interface ImportStep {
  id: string;
  name: string;
  description: string;
  path: string;
  status: 'complete' | 'current' | 'upcoming';
}

export interface ImportWizardData {
  tempId?: string;
  file?: File;
  fileType?: string;
  previewData?: any;
  metadataConfig?: any;
  validationResult?: any;
  conversionResult?: any;
}

const IMPORT_STEPS: ImportStep[] = [
  {
    id: 'upload',
    name: '文件上传',
    description: '选择并上传数据文件',
    path: '/data/import/upload',
    status: 'upcoming'
  },
  {
    id: 'preview',
    name: '数据预览',
    description: '查看和验证数据内容',
    path: '/data/import/preview',
    status: 'upcoming'
  },
  {
    id: 'metadata',
    name: '元数据配置',
    description: '配置数据集元数据',
    path: '/data/import/metadata',
    status: 'upcoming'
  },
  {
    id: 'validate',
    name: '验证确认',
    description: 'CF规范验证和确认',
    path: '/data/import/validate',
    status: 'upcoming'
  },
  {
    id: 'complete',
    name: '导入完成',
    description: '完成数据导入过程',
    path: '/data/import/complete',
    status: 'upcoming'
  }
];

export const useImportWizard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const [wizardData, setWizardData] = useState<ImportWizardData>({});
  const [currentStepId, setCurrentStepId] = useState<string>('upload');

  // 获取当前步骤索引
  const getCurrentStepIndex = useCallback((stepId: string) => {
    return IMPORT_STEPS.findIndex(step => step.id === stepId);
  }, []);

  // 更新步骤状态
  const updateStepStatuses = useCallback((currentId: string) => {
    const currentIndex = getCurrentStepIndex(currentId);
    return IMPORT_STEPS.map((step, index) => ({
      ...step,
      status: index < currentIndex ? 'complete' : 
              index === currentIndex ? 'current' : 'upcoming'
    }));
  }, [getCurrentStepIndex]);

  // 根据URL路径确定当前步骤
  const getCurrentStepFromPath = useCallback(() => {
    const path = location.pathname;
    const step = IMPORT_STEPS.find(s => s.path === path);
    return step?.id || 'upload';
  }, [location.pathname]);

  // 获取步骤列表（带状态）
  const getSteps = useCallback(() => {
    const currentId = getCurrentStepFromPath();
    return updateStepStatuses(currentId);
  }, [getCurrentStepFromPath, updateStepStatuses]);

  // 导航到特定步骤
  const goToStep = useCallback((stepId: string) => {
    const step = IMPORT_STEPS.find(s => s.id === stepId);
    if (step) {
      setCurrentStepId(stepId);
      navigate(step.path);
    }
  }, [navigate]);

  // 下一步
  const nextStep = useCallback(() => {
    const currentId = getCurrentStepFromPath();
    const currentIndex = getCurrentStepIndex(currentId);
    const nextIndex = currentIndex + 1;
    
    if (nextIndex < IMPORT_STEPS.length) {
      const nextStep = IMPORT_STEPS[nextIndex];
      goToStep(nextStep.id);
    }
  }, [getCurrentStepFromPath, getCurrentStepIndex, goToStep]);

  // 上一步
  const previousStep = useCallback(() => {
    const currentId = getCurrentStepFromPath();
    const currentIndex = getCurrentStepIndex(currentId);
    const prevIndex = currentIndex - 1;
    
    if (prevIndex >= 0) {
      const prevStep = IMPORT_STEPS[prevIndex];
      goToStep(prevStep.id);
    }
  }, [getCurrentStepFromPath, getCurrentStepIndex, goToStep]);

  // 更新向导数据
  const updateWizardData = useCallback((data: Partial<ImportWizardData>) => {
    setWizardData(prev => ({ ...prev, ...data }));
  }, []);

  // 重置向导
  const resetWizard = useCallback(() => {
    setWizardData({});
    setCurrentStepId('upload');
    navigate('/data/import/upload');
  }, [navigate]);

  // 检查是否可以进入下一步
  const canProceed = useCallback((stepId: string) => {
    switch (stepId) {
      case 'upload':
        return !!wizardData.tempId && !!wizardData.file;
      case 'preview':
        return !!wizardData.previewData;
      case 'metadata':
        return !!wizardData.metadataConfig;
      case 'validate':
        return !!wizardData.validationResult;
      case 'complete':
        return !!wizardData.conversionResult;
      default:
        return false;
    }
  }, [wizardData]);

  // 检查是否为第一步/最后一步
  const isFirstStep = getCurrentStepFromPath() === 'upload';
  const isLastStep = getCurrentStepFromPath() === 'complete';

  return {
    // 状态
    steps: getSteps(),
    currentStepId: getCurrentStepFromPath(),
    wizardData,
    isFirstStep,
    isLastStep,
    
    // 方法
    goToStep,
    nextStep,
    previousStep,
    updateWizardData,
    resetWizard,
    canProceed
  };
};

export default useImportWizard; 