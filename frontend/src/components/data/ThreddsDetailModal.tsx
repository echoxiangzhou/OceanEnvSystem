import React from 'react';
import { Dataset } from '../../types/api';
import { useThreddsMetadataById } from '../../hooks/useDataHooks';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import { Link } from 'react-router-dom';

interface ThreddsDetailModalProps {
  dataset: Dataset | null;
  isOpen: boolean;
  onClose: () => void;
  onDownload: (dataset: Dataset) => void;
  enhancedMetadata?: any;
  isLoadingEnhanced?: boolean;
  enhancedError?: string | null;
}

const ThreddsDetailModal: React.FC<ThreddsDetailModalProps> = ({ 
  dataset, 
  isOpen, 
  onClose, 
  onDownload, 
  enhancedMetadata, 
  isLoadingEnhanced, 
  enhancedError 
}) => {
  // 如果对话框未打开或没有选中数据集，不渲染任何内容
  if (!isOpen || !dataset) return null;

  // 获取数据集元数据
  const { 
    data: metadataResponse, 
    isLoading, 
    isError, 
    error 
  } = useThreddsMetadataById(dataset.id, {
    queryKey: ['threddsMetadata', dataset.id],
    enabled: isOpen && !!dataset,
    retry: (failureCount, error) => {
      // 针对特定错误类型减少重试次数
      if (error?.message?.includes('JSON')) {
        return failureCount < 1; // 只重试一次JSON相关错误
      }
      return failureCount < 3; // 默认重试3次
    }
  });
  
  // 处理元数据响应中可能的错误
  const processedMetadata = React.useMemo(() => {
    if (!metadataResponse?.data) return null;
    
    try {
      const { data } = metadataResponse;
      return {
        variables: data.variables,
        dims: data.dims,
        attrs: data.attrs
      };
    } catch (e) {
      console.error('Error processing metadata:', e);
      return null;
    }
  }, [metadataResponse]);

  // 格式化日期显示
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  // 详情页面路径
  const detailPageUrl = dataset.urlPath ? 
    `/data/detail/${encodeURIComponent(dataset.urlPath)}` : 
    null;

  // 渲染增强元数据内容
  const renderEnhanced = () => {
    if (isLoadingEnhanced) {
      return <div className="py-4 flex justify-center"><LoadingSpinner /></div>;
    }
    if (enhancedError) {
      return <ErrorMessage message={`获取增强元数据失败: ${enhancedError}`} />;
    }
    if (!enhancedMetadata) return null;
    
    // 处理可能的JSON序列化问题
    let meta = enhancedMetadata;
    try {
      // 处理可能的元数据序列化问题
      if (typeof meta === 'string') {
        try {
          meta = JSON.parse(meta);
        } catch (e) {
          console.error('Error parsing enhanced metadata string:', e);
        }
      }
      
      // 确保关键属性存在且格式正确
      if (meta.variables && typeof meta.variables === 'string') {
        try {
          meta.variables = JSON.parse(meta.variables);
        } catch (e) {
          console.error('Error parsing variables string:', e);
        }
      }
      
      if (meta.dimensions && typeof meta.dimensions === 'string') {
        try {
          meta.dimensions = JSON.parse(meta.dimensions);
        } catch (e) {
          console.error('Error parsing dimensions string:', e);
        }
      }
    } catch (e) {
      console.error('Error preprocessing enhanced metadata:', e);
    }
    
    return (
      <>
        {/* 标题与描述 */}
        <div className="mb-2">
          <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-1">{meta.title || dataset.name}</h4>
          <p className="text-sm text-gray-500 dark:text-gray-400">{meta.description || dataset.description || '无描述信息'}</p>
        </div>
        
        {/* 时间范围 */}
        {meta.time_range && !meta.time_range.error && (
          <div className="mb-2">
            <span className="font-medium text-gray-700 dark:text-gray-300">时间范围：</span>
            <span className="text-gray-600 dark:text-gray-400">
              {formatDate(meta.time_range.start)} ~ {formatDate(meta.time_range.end)}
              {meta.time_range.count ? ` (共${meta.time_range.count}步)` : ''}
            </span>
          </div>
        )}
        
        {/* 显示时间范围错误信息 */}
        {meta.time_range?.error && (
          <div className="mb-2">
            <span className="font-medium text-gray-700 dark:text-gray-300">时间范围：</span>
            <span className="text-red-500 text-xs">{meta.time_range.error}</span>
          </div>
        )}
        
        {/* 空间范围 */}
        {meta.spatial_range && !meta.spatial_range.error && (
          <div className="mb-2">
            <span className="font-medium text-gray-700 dark:text-gray-300">空间范围：</span>
            <span className="text-gray-600 dark:text-gray-400">
              经度: {meta.spatial_range.longitude.min.toFixed(2)} ~ {meta.spatial_range.longitude.max.toFixed(2)} {meta.spatial_range.longitude.units ? `(${meta.spatial_range.longitude.units})` : ''}, 
              纬度: {meta.spatial_range.latitude.min.toFixed(2)} ~ {meta.spatial_range.latitude.max.toFixed(2)} {meta.spatial_range.latitude.units ? `(${meta.spatial_range.latitude.units})` : ''}
            </span>
          </div>
        )}
        
        {/* 显示空间范围错误信息 */}
        {meta.spatial_range?.error && (
          <div className="mb-2">
            <span className="font-medium text-gray-700 dark:text-gray-300">空间范围：</span>
            <span className="text-red-500 text-xs">{meta.spatial_range.error}</span>
          </div>
        )}
        
        {/* 生产者/来源信息 */}
        {meta.source_information && Object.keys(meta.source_information).length > 0 && (
          <div className="mb-2">
            <span className="font-medium text-gray-700 dark:text-gray-300">生产者/来源：</span>
            <span className="text-gray-600 dark:text-gray-400">
              {Object.entries(meta.source_information)
                .filter(([k, v]) => k !== 'info' || Object.keys(meta.source_information).length === 1) // 只在没有其他信息时才显示'info'字段
                .map(([k, v]) => `${k}: ${v}`)
                .join(' | ')}
            </span>
          </div>
        )}
        
        {/* 创建日期 */}
        {meta.creation_date && (
          <div className="mb-2">
            <span className="font-medium text-gray-700 dark:text-gray-300">创建日期：</span>
            <span className="text-gray-600 dark:text-gray-400">{formatDate(meta.creation_date)}</span>
          </div>
        )}
        
        {/* 变量信息 */}
        <div className="mb-4">
          <span className="font-medium text-gray-700 dark:text-gray-300">变量：</span>
          {meta.variables && Array.isArray(meta.variables) && meta.variables.length > 0 ? (
            <div className="mt-2 bg-gray-50 dark:bg-gray-700 p-3 rounded-md max-h-48 overflow-y-auto">
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-300">
                {meta.variables.map((v: any, idx: number) => (
                  <li key={idx} className="border-b border-gray-200 dark:border-gray-600 pb-1">
                    <span className="font-medium">{v.name}</span> 
                    {v.units ? <span className="text-gray-500"> ({v.units})</span> : ''}
                    {v.long_name && v.long_name !== v.name ? 
                      <div className="text-gray-500 truncate">{v.long_name}</div> : 
                      v.standard_name ? <div className="text-gray-500 truncate">{v.standard_name}</div> : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : <span className="text-gray-400">无变量信息</span>}
        </div>
        
        {/* 维度信息 */}
        {meta.dimensions && Object.keys(meta.dimensions).length > 0 && (
          <div className="mb-2">
            <span className="font-medium text-gray-700 dark:text-gray-300">维度：</span>
            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md mt-1">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm">
                {Object.entries(meta.dimensions).map(([name, size]) => {
                  // 安全地处理维度大小，确保不直接渲染对象
                  let displaySize: string;
                  if (typeof size === 'object' && size !== null) {
                    try {
                      // 如果是对象，尝试提取size属性或name属性
                      const sizeObj = size as any;
                      if ('size' in sizeObj) {
                        displaySize = String(sizeObj.size);
                      } else if ('name' in sizeObj) {
                        displaySize = String(sizeObj.name);
                      } else {
                        displaySize = JSON.stringify(size);
                      }
                    } catch (e) {
                      console.error(`Error formatting dimension ${name}:`, e);
                      displaySize = '[格式化错误]';
                    }
                  } else {
                    displaySize = String(size);
                  }
                  
                  return (
                    <div key={name}>
                      <span className="font-medium text-gray-700 dark:text-gray-300">{name}:</span> 
                      <span className="text-gray-600 dark:text-gray-400"> {displaySize}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* 全局属性信息 */}
        {meta.global_attributes && Object.keys(meta.global_attributes).length > 0 && (
          <div className="mb-2">
            <span className="font-medium text-gray-700 dark:text-gray-300">全局属性：</span>
            <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md mt-1 max-h-64 overflow-y-auto">
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {Object.entries(meta.global_attributes).map(([name, value]) => (
                  <div key={name} className="mb-2">
                    <dt className="font-medium text-gray-700 dark:text-gray-300">{name}</dt>
                    <dd className="text-gray-600 dark:text-gray-400">{String(value)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        )}
      </>
    );
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* 背景遮罩 */}
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onClick={onClose}></div>

        {/* 使内容居中 */}
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        {/* 对话框内容 */}
        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full md:max-w-2xl lg:max-w-4xl">
          <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="sm:flex sm:items-start">
              <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white" id="modal-title">
                  {dataset.name}
                </h3>
                <div className="mt-2">
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{dataset.description}</p>
                  {/* 优先展示增强元数据 */}
                  {renderEnhanced() || null}
                  
                  {/* 基本信息 */}
                  <div className="grid grid-cols-2 gap-4 text-sm mb-6">
                    <div>
                      <p className="font-medium text-gray-700 dark:text-gray-300">数据类型</p>
                      <p className="text-gray-500 dark:text-gray-400">{dataset.data_type}</p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700 dark:text-gray-300">数据来源</p>
                      <p className="text-gray-500 dark:text-gray-400">{dataset.source_type}</p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700 dark:text-gray-300">文件格式</p>
                      <p className="text-gray-500 dark:text-gray-400">{dataset.file_format}</p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700 dark:text-gray-300">文件路径</p>
                      <p className="text-gray-500 dark:text-gray-400 truncate">{dataset.file_location}</p>
                    </div>
                    {dataset.created_at && (
                      <div>
                        <p className="font-medium text-gray-700 dark:text-gray-300">创建时间</p>
                        <p className="text-gray-500 dark:text-gray-400">{formatDate(dataset.created_at)}</p>
                      </div>
                    )}
                    {dataset.updated_at && (
                      <div>
                        <p className="font-medium text-gray-700 dark:text-gray-300">更新时间</p>
                        <p className="text-gray-500 dark:text-gray-400">{formatDate(dataset.updated_at)}</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Thredds访问链接 */}
                  {dataset.opendapUrl && (
                    <div className="mb-4">
                      <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">OPeNDAP访问</p>
                      <p className="text-sm text-blue-600 dark:text-blue-400 break-all hover:underline">
                        <a href={dataset.opendapUrl} target="_blank" rel="noopener noreferrer">
                          {dataset.opendapUrl}
                        </a>
                      </p>
                    </div>
                  )}
                  
                  {dataset.httpUrl && (
                    <div className="mb-4">
                      <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">HTTP访问</p>
                      <p className="text-sm text-blue-600 dark:text-blue-400 break-all hover:underline">
                        <a href={dataset.httpUrl} target="_blank" rel="noopener noreferrer">
                          {dataset.httpUrl}
                        </a>
                      </p>
                    </div>
                  )}
                  
                  {/* 元数据内容 */}
                  {!isLoading && !isError && metadataResponse?.data && !enhancedMetadata && (
                    <>
                      {/* 变量信息 */}
                      <div className="mt-4">
                        <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">变量</h4>
                        <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md max-h-32 overflow-y-auto">
                          {metadataResponse.data.variables ? (
                            <ul className="grid grid-cols-2 sm:grid-cols-3 gap-1">
                              {/* 确保变量是数组，如果不是则尝试将它转换为数组 */}
                              {(Array.isArray(metadataResponse.data.variables) ? 
                                metadataResponse.data.variables : 
                                Object.keys(metadataResponse.data.variables || {})
                              ).map((variable, index) => {
                                let displayVariable = variable;
                                
                                // 如果变量是对象，则尝试提取名称
                                if (typeof variable === 'object' && variable !== null) {
                                  try {
                                    const varObj = variable as any;
                                    displayVariable = varObj.name || JSON.stringify(variable);
                                  } catch (e) {
                                    console.error(`Error formatting variable at index ${index}:`, e);
                                    displayVariable = '[格式化错误]';
                                  }
                                }
                                
                                return (
                                  <li key={index} className="text-sm text-gray-600 dark:text-gray-300 truncate">{displayVariable}</li>
                                );
                              })}
                            </ul>
                          ) : (
                            <p className="text-sm text-gray-500 dark:text-gray-400">没有变量信息</p>
                          )}
                        </div>
                      </div>
                      
                      {/* 维度信息 */}
                      <div className="mt-4">
                        <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">维度</h4>
                        <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md max-h-32 overflow-y-auto">
                          {metadataResponse.data.dims && Object.keys(metadataResponse.data.dims).length > 0 ? (
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                              {Object.entries(metadataResponse.data.dims).map(([name, size]) => {
                                // 处理维度大小可能是数字或其他类型
                                let displaySize: string;
                                if (typeof size === 'object' && size !== null) {
                                  try {
                                    displaySize = JSON.stringify(size);
                                  } catch (e) {
                                    console.error(`Error formatting dimension ${name}:`, e);
                                    displaySize = '[格式化错误]';
                                  }
                                } else {
                                  displaySize = String(size);
                                }
                                
                                return (
                                  <div key={name} className="text-sm">
                                    <span className="font-medium text-gray-700 dark:text-gray-300">{name}:</span> 
                                    <span className="text-gray-600 dark:text-gray-400"> {displaySize}</span>
                                  </div>
                                );
                              })}
                            </div>
                          ) : (
                            <p className="text-sm text-gray-500 dark:text-gray-400">没有维度信息</p>
                          )}
                        </div>
                      </div>
                      
                      {/* 全局属性信息 */}
                      <div className="mt-4">
                        <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">全局属性</h4>
                        <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md max-h-64 overflow-y-auto">
                          {metadataResponse.data.attrs && Object.keys(metadataResponse.data.attrs).length > 0 ? (
                            <dl className="grid grid-cols-1 gap-x-4 gap-y-2">
                              {Object.entries(metadataResponse.data.attrs).map(([name, value]) => {
                                // 处理可能是数组或其他复杂类型的值
                                let displayValue = value;
                                
                                // 检查值是否是对象（可能是序列化后的NumPy数组）
                                if (typeof value === 'object' && value !== null) {
                                  try {
                                    // 尝试将对象转换为字符串
                                    if (Array.isArray(value)) {
                                      // 如果是数组，转换为有限长度的字符串表示
                                      if (value.length > 10) {
                                        displayValue = `[${value.slice(0, 10).join(', ')}, ... (共${value.length}项)]`;
                                      } else {
                                        displayValue = `[${value.join(', ')}]`;
                                      }
                                    } else {
                                      // 对象但不是数组，使用JSON.stringify
                                      displayValue = JSON.stringify(value, null, 2);
                                    }
                                  } catch (e) {
                                    console.error(`Error formatting attribute ${name}:`, e);
                                    displayValue = '[格式化错误]';
                                  }
                                }
                                
                                return (
                                  <div key={name} className="col-span-1 border-b border-gray-200 dark:border-gray-600 pb-2 mb-2 last:border-0 last:mb-0 last:pb-0">
                                    <dt className="text-sm font-medium text-gray-700 dark:text-gray-300">{name}</dt>
                                    <dd className="text-sm text-gray-500 dark:text-gray-400 break-words">{String(displayValue)}</dd>
                                  </div>
                                );
                              })}
                            </dl>
                          ) : (
                            <p className="text-sm text-gray-500 dark:text-gray-400">没有全局属性信息</p>
                          )}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            {/* 详情页链接 */}
            {detailPageUrl && (
              <Link
                to={detailPageUrl}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
              >
                查看详情
              </Link>
            )}

            <button
              type="button"
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:ml-3 sm:w-auto sm:text-sm"
              onClick={() => onDownload(dataset)}
            >
              下载
            </button>
            <button
              type="button"
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-gray-600 shadow-sm px-4 py-2 bg-white dark:bg-gray-800 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              onClick={onClose}
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThreddsDetailModal;