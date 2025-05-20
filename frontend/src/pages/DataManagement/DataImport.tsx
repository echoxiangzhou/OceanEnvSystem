import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDataConversion, useRegisterDataset } from '../../hooks/useDataHooks';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';

const DataImport: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<'csv' | 'xlsx' | 'cnv'>('csv');
  const [isConverting, setIsConverting] = useState(false);
  const [netcdfPath, setNetcdfPath] = useState<string>('');
  const [registrationForm, setRegistrationForm] = useState({
    name: '',
    description: '',
    source_type: 'BUOY' as const,
    data_type: 'OBSERVATIONS' as const,
    spatial_coverage: {
      type: 'Polygon',
      coordinates: [[[120, 30], [121, 30], [121, 31], [120, 31], [120, 30]]]
    },
    temporal_coverage: {
      start: new Date().toISOString(),
      end: new Date().toISOString()
    },
    variables: [] as { name: string; unit: string; description: string }[]
  });
  
  // 文件转换mutation
  const { 
    mutate: convertData, 
    isPending: isConversionPending, 
    isError: isConversionError, 
    error: conversionError,
    isSuccess: isConversionSuccess,
    data: conversionData
  } = useDataConversion({
    onSuccess: (data) => {
      setIsConverting(false);
      setNetcdfPath(data.data.netcdf_path);
      
      // 更新注册表单的文件路径
      setRegistrationForm(prev => ({
        ...prev,
        file_format: 'nc',
        file_location: data.data.netcdf_path,
        name: file ? file.name.replace(/\.[^/.]+$/, "") : prev.name
      }));
    }
  });
  
  // 数据集注册mutation
  const {
    mutate: registerDataset,
    isPending: isRegistrationPending,
    isError: isRegistrationError,
    error: registrationError,
    isSuccess: isRegistrationSuccess
  } = useRegisterDataset({
    onSuccess: () => {
      // 注册成功后导航到数据浏览页面
      navigate('/data');
    }
  });

  // 处理文件选择
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      
      // 从文件名判断文件类型
      const fileName = selectedFile.name.toLowerCase();
      if (fileName.endsWith('.csv')) {
        setFileType('csv');
      } else if (fileName.endsWith('.xlsx')) {
        setFileType('xlsx');
      } else if (fileName.endsWith('.cnv')) {
        setFileType('cnv');
      }
    }
  };

  // 处理文件类型选择
  const handleFileTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFileType(e.target.value as 'csv' | 'xlsx' | 'cnv');
  };

  // 处理文件上传和转换
  const handleConvert = () => {
    if (!file) return;
    setIsConverting(true);
    convertData({ file, fileType });
  };

  // 处理表单输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setRegistrationForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // 处理变量输入变化
  const handleVariableChange = (idx: number, field: string, value: string) => {
    setRegistrationForm(prev => {
      const updatedVariables = [...prev.variables];
      updatedVariables[idx] = { ...updatedVariables[idx], [field]: value };
      return { ...prev, variables: updatedVariables };
    });
  };

  // 添加新变量
  const handleAddVariable = () => {
    setRegistrationForm(prev => ({
      ...prev,
      variables: [...prev.variables, { name: '', unit: '', description: '' }]
    }));
  };

  // 删除变量
  const handleRemoveVariable = (idx: number) => {
    setRegistrationForm(prev => ({
      ...prev,
      variables: prev.variables.filter((_, i) => i !== idx)
    }));
  };

  // 处理日期输入变化
  const handleDateChange = (field: 'start' | 'end', value: string) => {
    setRegistrationForm(prev => ({
      ...prev,
      temporal_coverage: {
        ...prev.temporal_coverage,
        [field]: new Date(value).toISOString()
      }
    }));
  };

  // 处理表单提交
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    registerDataset(registrationForm);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">数据导入</h1>
        <button
          onClick={() => navigate('/data')}
          className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800"
        >
          返回数据浏览
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 文件上传区域 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="p-5">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">文件上传与转换</h2>

            {/* 转换错误 */}
            {isConversionError && (
              <ErrorMessage 
                message={`文件转换失败: ${conversionError?.message || '未知错误'}`}
              />
            )}

            {/* 转换成功 */}
            {isConversionSuccess && (
              <div className="mb-4 rounded-md bg-green-50 dark:bg-green-900/20 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-green-800 dark:text-green-200">
                      文件转换成功！NetCDF文件已创建，请填写下方表单完成数据集注册。
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-4">
              {/* 文件选择 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  选择数据文件
                </label>
                <div className="mt-1 flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-3">
                  <div className="flex-grow">
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileChange}
                      className="sr-only"
                      accept=".csv,.xlsx,.cnv"
                    />
                    <div 
                      onClick={() => fileInputRef.current?.click()}
                      className="w-full flex items-center justify-center px-6 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-md cursor-pointer hover:border-blue-500 dark:hover:border-blue-400 transition-colors"
                    >
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {file ? file.name : '点击选择文件 (.csv, .xlsx, .cnv)'}
                      </span>
                    </div>
                  </div>
                  <select
                    value={fileType}
                    onChange={handleFileTypeChange}
                    className="block w-full sm:w-auto border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 sm:text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="csv">CSV</option>
                    <option value="xlsx">Excel</option>
                    <option value="cnv">CNV (海鸟CTD)</option>
                  </select>
                </div>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  支持Excel (.xlsx), CSV (.csv), 和海鸟CTD (.cnv) 文件格式
                </p>
              </div>

              {/* 文件信息 */}
              {file && (
                <div className="border border-gray-200 dark:border-gray-700 rounded-md p-3 bg-gray-50 dark:bg-gray-700/30">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">文件信息</h3>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">文件名:</span>
                      <span className="ml-1 text-gray-900 dark:text-gray-100">{file.name}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">大小:</span>
                      <span className="ml-1 text-gray-900 dark:text-gray-100">
                        {(file.size / 1024).toFixed(2)} KB
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">类型:</span>
                      <span className="ml-1 text-gray-900 dark:text-gray-100">{file.type || fileType}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">修改时间:</span>
                      <span className="ml-1 text-gray-900 dark:text-gray-100">
                        {new Date(file.lastModified).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* 转换按钮 */}
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={handleConvert}
                  disabled={!file || isConversionPending}
                  className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
                    !file || isConversionPending ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
                  } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors`}
                >
                  {isConversionPending ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      转换中...
                    </>
                  ) : (
                    '转换为NetCDF'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 数据集注册表单 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="p-5">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">数据集注册</h2>

            {isRegistrationError && (
              <ErrorMessage 
                message={`数据集注册失败: ${registrationError?.message || '未知错误'}`}
              />
            )}

            {isRegistrationSuccess && (
              <div className="mb-4 rounded-md bg-green-50 dark:bg-green-900/20 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-green-800 dark:text-green-200">
                      数据集注册成功！
                    </p>
                  </div>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                {/* 基本信息 */}
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    数据集名称 *
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={registrationForm.name}
                    onChange={handleInputChange}
                    required
                    className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    描述 *
                  </label>
                  <textarea
                    id="description"
                    name="description"
                    value={registrationForm.description}
                    onChange={handleInputChange}
                    required
                    rows={3}
                    className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>

                {/* 数据类型 */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="source_type" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      源类型 *
                    </label>
                    <select
                      id="source_type"
                      name="source_type"
                      value={registrationForm.source_type}
                      onChange={handleInputChange}
                      required
                      className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      <option value="BUOY">浮标</option>
                      <option value="SURVEY">调查</option>
                      <option value="SATELLITE">卫星</option>
                      <option value="MODEL">模型</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="data_type" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      数据类型 *
                    </label>
                    <select
                      id="data_type"
                      name="data_type"
                      value={registrationForm.data_type}
                      onChange={handleInputChange}
                      required
                      className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      <option value="OBSERVATIONS">观测</option>
                      <option value="FORECAST">预报</option>
                      <option value="REANALYSIS">再分析</option>
                    </select>
                  </div>
                </div>

                {/* 时间范围 */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">时间范围 *</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="start_time" className="block text-xs text-gray-500 dark:text-gray-400">
                        开始时间
                      </label>
                      <input
                        type="datetime-local"
                        id="start_time"
                        value={new Date(registrationForm.temporal_coverage.start).toISOString().slice(0, 16)}
                        onChange={(e) => handleDateChange('start', e.target.value)}
                        required
                        className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                    </div>
                    <div>
                      <label htmlFor="end_time" className="block text-xs text-gray-500 dark:text-gray-400">
                        结束时间
                      </label>
                      <input
                        type="datetime-local"
                        id="end_time"
                        value={new Date(registrationForm.temporal_coverage.end).toISOString().slice(0, 16)}
                        onChange={(e) => handleDateChange('end', e.target.value)}
                        required
                        className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* 变量信息 */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">变量信息</h3>
                    <button
                      type="button"
                      onClick={handleAddVariable}
                      className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      添加变量
                    </button>
                  </div>
                  
                  {registrationForm.variables.length === 0 ? (
                    <div className="text-center py-4 border border-dashed border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700/30">
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {isConversionSuccess ? 
                          "请添加至少一个变量" : 
                          "转换文件后添加变量信息"
                        }
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {registrationForm.variables.map((variable, idx) => (
                        <div key={idx} className="grid grid-cols-12 gap-2 items-start">
                          <div className="col-span-4">
                            <input
                              type="text"
                              placeholder="变量名"
                              value={variable.name}
                              onChange={(e) => handleVariableChange(idx, 'name', e.target.value)}
                              required
                              className="block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-1 px-2 text-xs bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            />
                          </div>
                          <div className="col-span-3">
                            <input
                              type="text"
                              placeholder="单位"
                              value={variable.unit}
                              onChange={(e) => handleVariableChange(idx, 'unit', e.target.value)}
                              className="block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-1 px-2 text-xs bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            />
                          </div>
                          <div className="col-span-4">
                            <input
                              type="text"
                              placeholder="描述"
                              value={variable.description}
                              onChange={(e) => handleVariableChange(idx, 'description', e.target.value)}
                              className="block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-1 px-2 text-xs bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            />
                          </div>
                          <div className="col-span-1">
                            <button
                              type="button"
                              onClick={() => handleRemoveVariable(idx)}
                              className="inline-flex items-center justify-center w-6 h-6 border border-transparent rounded-full text-red-500 hover:bg-red-100 dark:hover:bg-red-900/20 focus:outline-none"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 空间范围提示 */}
                <div className="border border-gray-200 dark:border-gray-700 rounded-md p-3 bg-gray-50 dark:bg-gray-700/30">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">空间范围</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    系统将使用默认的南海北部海域空间范围(120-121°E, 30-31°N)，如需自定义，请在注册后编辑数据集。
                  </p>
                </div>

                {/* 提交按钮 */}
                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={isRegistrationPending || !isConversionSuccess || registrationForm.variables.length === 0}
                    className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
                      isRegistrationPending || !isConversionSuccess || registrationForm.variables.length === 0
                        ? 'bg-blue-400 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700'
                    } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors`}
                  >
                    {isRegistrationPending ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        注册中...
                      </>
                    ) : (
                      '注册数据集'
                    )}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataImport;