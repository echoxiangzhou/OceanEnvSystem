import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Dataset, Variable } from '../../types/api';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import DatasetListItem from '../../components/data/DatasetListItem';
import ThreddsDetailModal from '../../components/data/ThreddsDetailModal';
import DatasetFilter, { FilterOptions } from '../../components/data/DatasetFilter';
import { metadataService, MetadataItem } from '../../services/metadataService';

const DataBrowser: React.FC = () => {
  // 选中的数据集状态
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  
  // 开发者模式状态
  const [developerMode, setDeveloperMode] = useState(false);
  
  // 过滤器状态
  const [filters, setFilters] = useState<FilterOptions>({
    searchText: '',
    sourceType: 'ALL',
    dataType: 'ALL',
    sortBy: 'updated_at',
    sortOrder: 'desc'
  });

  // 元数据列表状态
  const [metadataList, setMetadataList] = useState<MetadataItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(50); // 增加每页显示数量

  // 增强元数据状态
  const [enhancedMetadata, setEnhancedMetadata] = useState<any>(null);
  const [isLoadingEnhanced, setIsLoadingEnhanced] = useState(false);
  const [enhancedError, setEnhancedError] = useState<string | null>(null);

  // 获取元数据列表
  const fetchMetadataList = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params: any = {
        page: currentPage,
        size: pageSize,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder
      };

      // 根据过滤器设置参数
      if (filters.searchText) {
        params.search = filters.searchText;
      }
      
      // 处理状态过滤：如果不是开发者模式，只显示标准数据
      if (!developerMode) {
        params.processing_status = 'standard';
      } else if (filters.sourceType !== 'ALL') {
        // 在开发者模式下，允许按处理状态过滤
        switch (filters.sourceType) {
          case 'MODEL':
            params.processing_status = 'standard';
            break;
          case 'SATELLITE':
            params.processing_status = 'standard';
            break;
          case 'BUOY':
            params.processing_status = 'processing';
            break;
          case 'SURVEY':
            params.processing_status = 'raw';
            break;
        }
      }

      const response = await metadataService.getMetadataList(params);
      setMetadataList(response.items);
      setTotal(response.total);
    } catch (err) {
      setError('获取数据集失败');
      console.error('获取数据集失败:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // 初始化和筛选条件变化时重新获取数据
  useEffect(() => {
    fetchMetadataList();
  }, [currentPage, filters, developerMode]);

  // 将元数据项转换为Dataset格式
  const convertMetadataToDataset = (metadata: MetadataItem): Dataset => {
    // 根据处理状态推断数据类型
    let sourceType: Dataset['source_type'] = 'MODEL';
    let dataType: Dataset['data_type'] = 'OBSERVATIONS';
    
    // 从文件路径或机构信息推断数据源类型
    const filePath = metadata.file_path?.toLowerCase() || '';
    const institution = metadata.institution?.toLowerCase() || '';
    
    if (filePath.includes('satellite') || institution.includes('satellite')) {
      sourceType = 'SATELLITE';
      dataType = 'OBSERVATIONS';
    } else if (filePath.includes('buoy') || institution.includes('buoy')) {
      sourceType = 'BUOY';
      dataType = 'OBSERVATIONS';
    } else if (filePath.includes('survey') || filePath.includes('ctd') || institution.includes('survey')) {
      sourceType = 'SURVEY';
      dataType = 'OBSERVATIONS';
    } else if (filePath.includes('model') || institution.includes('model')) {
      sourceType = 'MODEL';
      if (filePath.includes('forecast')) {
        dataType = 'FORECAST';
      } else {
        dataType = 'REANALYSIS';
      }
    }

    // 构造变量数组
    const variables: Variable[] = [];
    if (metadata.variables && typeof metadata.variables === 'object') {
      Object.entries(metadata.variables).forEach(([name, info]: [string, any]) => {
        variables.push({
          name,
          standard_name: info?.standard_name || '',
          unit: info?.units || info?.unit || '',
          description: info?.long_name || info?.description || ''
        });
      });
    }

    return {
      id: metadata.id.toString(),
      name: metadata.file_name,
      description: metadata.summary || `NetCDF数据文件: ${metadata.file_name}`,
      source_type: sourceType,
      data_type: dataType,
      spatial_coverage: (
        metadata.geospatial_lat_min !== undefined && 
        metadata.geospatial_lat_max !== undefined &&
        metadata.geospatial_lon_min !== undefined && 
        metadata.geospatial_lon_max !== undefined
      ) ? {
        type: 'Polygon',
        coordinates: [[
          [metadata.geospatial_lon_min, metadata.geospatial_lat_min],
          [metadata.geospatial_lon_max, metadata.geospatial_lat_min],
          [metadata.geospatial_lon_max, metadata.geospatial_lat_max],
          [metadata.geospatial_lon_min, metadata.geospatial_lat_max],
          [metadata.geospatial_lon_min, metadata.geospatial_lat_min]
        ]]
      } : undefined,
      temporal_coverage: (metadata.time_coverage_start && metadata.time_coverage_end) ? {
        start: metadata.time_coverage_start,
        end: metadata.time_coverage_end
      } : undefined,
      variables,
      file_format: 'nc',
      file_location: metadata.file_path,
      created_at: metadata.created_at,
      updated_at: metadata.updated_at,
      // 扩展属性
      urlPath: metadata.file_path.replace(/^.*\/data\/oceanenv\//, 'oceanenv/'),
      opendapUrl: `http://localhost:8080/thredds/dodsC/${metadata.file_path.replace(/^.*\/data\//, '')}`,
      httpUrl: `http://localhost:8080/thredds/fileServer/${metadata.file_path.replace(/^.*\/data\//, '')}`,
      threddsId: metadata.id.toString()
    };
  };

  // 处理后的数据集列表
  const processedDatasets = useMemo(() => {
    return metadataList.map(convertMetadataToDataset);
  }, [metadataList]);

  // 处理查看数据集详情
  const handleViewDataset = (dataset: Dataset) => {
    setSelectedDataset(dataset);
    setIsDetailModalOpen(true);
  };

  // 获取增强元数据（模态框中使用）
  useEffect(() => {
    const fetchEnhanced = async () => {
      if (selectedDataset && selectedDataset.urlPath) {
        setIsLoadingEnhanced(true);
        setEnhancedError(null);
        setEnhancedMetadata(null);
        
        try {
          // 从元数据列表中获取对应的详细信息
          const metadataItem = metadataList.find(item => 
            item.id.toString() === selectedDataset.id
          );
          
          if (metadataItem) {
            // 构造增强元数据
            const enhanced = {
              title: metadataItem.title || metadataItem.file_name,
              description: metadataItem.summary || '无描述信息',
              time_range: metadataItem.time_coverage_start && metadataItem.time_coverage_end ? {
                start: metadataItem.time_coverage_start,
                end: metadataItem.time_coverage_end
              } : null,
              spatial_range: (
                metadataItem.geospatial_lat_min !== undefined && 
                metadataItem.geospatial_lat_max !== undefined &&
                metadataItem.geospatial_lon_min !== undefined && 
                metadataItem.geospatial_lon_max !== undefined
              ) ? {
                latitude: {
                  min: metadataItem.geospatial_lat_min,
                  max: metadataItem.geospatial_lat_max,
                  units: 'degrees_north'
                },
                longitude: {
                  min: metadataItem.geospatial_lon_min,
                  max: metadataItem.geospatial_lon_max,
                  units: 'degrees_east'
                }
              } : null,
              variables: metadataItem.variables || {},
              dimensions: metadataItem.dimensions || {},
              source_information: {
                institution: metadataItem.institution,
                source: metadataItem.source
              },
              global_attributes: {
                Conventions: metadataItem.cf_version,
                institution: metadataItem.institution,
                source: metadataItem.source,
                title: metadataItem.title
              },
              cf_compliant: metadataItem.is_cf_compliant,
              processing_status: metadataItem.processing_status
            };
            
            setEnhancedMetadata(enhanced);
          }
        } catch (err) {
          setEnhancedError('获取增强元数据失败');
          console.error('获取增强元数据失败:', err);
        } finally {
          setIsLoadingEnhanced(false);
        }
      } else {
        setEnhancedMetadata(null);
      }
    };

    if (isDetailModalOpen) {
      fetchEnhanced();
    }
  }, [selectedDataset, isDetailModalOpen, metadataList]);

  // 处理下载数据集
  const handleDownloadDataset = async (dataset: Dataset) => {
    try {
      // 构造下载链接
      const fileName = dataset.file_location?.split('/').pop() || `dataset-${dataset.id}.nc`;
      const downloadUrl = `http://localhost:8080/thredds/fileServer/${dataset.file_location?.replace(/^.*\/data\//, '')}`;
      
      // 创建下载链接
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = fileName;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error('下载文件失败:', err);
      alert('下载失败: ' + (err instanceof Error ? err.message : String(err)));
    }
  };

  // 处理筛选条件更改
  const handleFilterChange = (newFilters: FilterOptions) => {
    setFilters(newFilters);
    setCurrentPage(1); // 重置到第一页
  };

  // 切换开发者模式
  const toggleDeveloperMode = () => {
    setDeveloperMode(!developerMode);
    setCurrentPage(1); // 重置到第一页
  };

  // 计算总页数
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* 页面标题 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">数据浏览</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          浏览海洋环境数据文件元数据信息
        </p>
        <div className="mt-2 py-1 px-2 bg-blue-50 dark:bg-blue-900/20 rounded-md text-xs text-blue-800 dark:text-blue-300">
          注意：当前页面显示存储在MySQL数据库中的文件元数据信息。
          <button 
            onClick={toggleDeveloperMode}
            className="ml-2 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 underline"
          >
            {developerMode ? '仅显示标准数据' : '显示全部数据（开发模式）'}
          </button>
        </div>
      </div>

      {/* 筛选组件 */}
      <DatasetFilter onFilterChange={handleFilterChange} />

      {/* 加载状态 */}
      {isLoading && (
        <div className="flex justify-center py-10">
          <LoadingSpinner />
        </div>
      )}

      {/* 错误状态 */}
      {error && (
        <ErrorMessage 
          message={error} 
          retry={fetchMetadataList}
        />
      )}

      {/* 数据集列表 */}
      {!isLoading && !error && (
        <div className="mt-6">
          {processedDatasets.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
              <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">没有找到数据集</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {total === 0 ? '数据库中没有数据文件。' : '没有符合当前筛选条件的数据集。'}
              </p>
              {total > 0 && (
                <div className="mt-4">
                  <button
                    onClick={() => setFilters({
                      searchText: '',
                      sourceType: 'ALL',
                      dataType: 'ALL',
                      sortBy: 'updated_at',
                      sortOrder: 'desc'
                    })}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800"
                  >
                    清除筛选
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div>
              <div className="mb-4 flex justify-between items-center">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  找到 {total} 个数据文件，当前显示第 {currentPage} 页
                  <span className="ml-1 text-xs text-blue-500">
                    （每页显示 {pageSize} 个，共 {totalPages} 页）
                  </span>
                </p>
              </div>
              
              <div className="space-y-4">
                {processedDatasets.map(dataset => (
                  <DatasetListItem
                    key={dataset.id}
                    dataset={dataset}
                    onView={() => handleViewDataset(dataset)}
                    onDelete={null} // 不允许在此页面删除数据集
                    enhancedMetadata={null} // 不在列表页面显示增强元数据
                    isLoadingEnhanced={false}
                  />
                ))}
              </div>

              {/* 分页控件 */}
              {totalPages > 1 && (
                <div className="mt-6 flex items-center justify-between">
                  <div className="flex-1 flex justify-between sm:hidden">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      上一页
                    </button>
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      下一页
                    </button>
                  </div>
                  <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm text-gray-700">
                        显示第 <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> 到{' '}
                        <span className="font-medium">
                          {Math.min(currentPage * pageSize, total)}
                        </span>{' '}
                        条，共 <span className="font-medium">{total}</span> 条记录
                      </p>
                    </div>
                    <div>
                      <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                        <button
                          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                          disabled={currentPage === 1}
                          className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          上一页
                        </button>
                        
                        {/* 页码按钮 */}
                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                          let pageNum;
                          if (totalPages <= 5) {
                            pageNum = i + 1;
                          } else if (currentPage <= 3) {
                            pageNum = i + 1;
                          } else if (currentPage >= totalPages - 2) {
                            pageNum = totalPages - 4 + i;
                          } else {
                            pageNum = currentPage - 2 + i;
                          }
                          
                          return (
                            <button
                              key={pageNum}
                              onClick={() => setCurrentPage(pageNum)}
                              className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                currentPage === pageNum
                                  ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                  : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                              }`}
                            >
                              {pageNum}
                            </button>
                          );
                        })}
                        
                        <button
                          onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                          disabled={currentPage === totalPages}
                          className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          下一页
                        </button>
                      </nav>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 数据集详情对话框 */}
      <ThreddsDetailModal
        dataset={selectedDataset}
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        onDownload={handleDownloadDataset}
        enhancedMetadata={enhancedMetadata}
        isLoadingEnhanced={isLoadingEnhanced}
        enhancedError={enhancedError}
      />
    </div>
  );
};

export default DataBrowser;