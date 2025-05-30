import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { metadataService, MetadataItem, MetadataListParams } from '../../services/metadataService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';

interface FilterOptions {
  searchText: string;
  processingStatus: string;
  isCfCompliant: string;
  institution: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

const MetadataBrowser: React.FC = () => {
  // 状态管理
  const [metadataList, setMetadataList] = useState<MetadataItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  
  // 过滤器状态
  const [filters, setFilters] = useState<FilterOptions>({
    searchText: '',
    processingStatus: 'ALL',
    isCfCompliant: 'ALL',
    institution: '',
    sortBy: 'updated_at',
    sortOrder: 'desc'
  });

  // 机构列表
  const [institutions, setInstitutions] = useState<string[]>([]);

  // 获取元数据列表
  const fetchMetadataList = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params: MetadataListParams = {
        page: currentPage,
        size: pageSize,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder
      };

      if (filters.searchText) {
        params.search = filters.searchText;
      }
      if (filters.processingStatus !== 'ALL') {
        params.processing_status = filters.processingStatus;
      }
      if (filters.isCfCompliant !== 'ALL') {
        params.is_cf_compliant = filters.isCfCompliant === 'true';
      }
      if (filters.institution) {
        params.institution = filters.institution;
      }

      const response = await metadataService.getMetadataList(params);
      setMetadataList(response.items);
      setTotal(response.total);
    } catch (err) {
      setError('获取元数据列表失败');
      console.error('获取元数据列表失败:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // 获取机构列表
  const fetchInstitutions = async () => {
    try {
      const institutionList = await metadataService.getUniqueInstitutions();
      setInstitutions(institutionList);
    } catch (err) {
      console.error('获取机构列表失败:', err);
    }
  };

  // 初始化数据
  useEffect(() => {
    fetchMetadataList();
    fetchInstitutions();
  }, [currentPage, filters]);

  // 处理过滤器变化
  const handleFilterChange = (newFilters: Partial<FilterOptions>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setCurrentPage(1); // 重置到第一页
  };

  // 处理页码变化
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // 格式化文件大小
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'N/A';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  // 格式化日期
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('zh-CN');
  };

  // 计算总页数
  const totalPages = Math.ceil(total / pageSize);

  if (isLoading && metadataList.length === 0) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage message={error} retry={fetchMetadataList} />;
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">数据元数据浏览</h1>
        <p className="text-gray-600">浏览和管理NetCDF文件的元数据信息</p>
      </div>

      {/* 过滤器 */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* 搜索框 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              搜索
            </label>
            <input
              type="text"
              value={filters.searchText}
              onChange={(e) => handleFilterChange({ searchText: e.target.value })}
              placeholder="搜索文件名或标题..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* 处理状态过滤 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              处理状态
            </label>
            <select
              value={filters.processingStatus}
              onChange={(e) => handleFilterChange({ processingStatus: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">全部</option>
              <option value="RAW">原始数据</option>
              <option value="PROCESSING">处理中</option>
              <option value="STANDARD">标准数据</option>
            </select>
          </div>

          {/* CF规范符合性过滤 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              CF规范符合性
            </label>
            <select
              value={filters.isCfCompliant}
              onChange={(e) => handleFilterChange({ isCfCompliant: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">全部</option>
              <option value="true">符合</option>
              <option value="false">不符合</option>
            </select>
          </div>

          {/* 机构过滤 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              机构
            </label>
            <select
              value={filters.institution}
              onChange={(e) => handleFilterChange({ institution: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">全部机构</option>
              {institutions.map(institution => (
                <option key={institution} value={institution}>
                  {institution}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 排序选项 */}
        <div className="mt-4 flex gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              排序字段
            </label>
            <select
              value={filters.sortBy}
              onChange={(e) => handleFilterChange({ sortBy: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="updated_at">更新时间</option>
              <option value="created_at">创建时间</option>
              <option value="file_name">文件名</option>
              <option value="file_size">文件大小</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              排序顺序
            </label>
            <select
              value={filters.sortOrder}
              onChange={(e) => handleFilterChange({ sortOrder: e.target.value as 'asc' | 'desc' })}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="desc">降序</option>
              <option value="asc">升序</option>
            </select>
          </div>
        </div>
      </div>

      {/* 统计信息 */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">
            共找到 {total} 个文件，当前显示第 {currentPage} 页
          </span>
          {isLoading && (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-2"></div>
              <span className="text-sm text-gray-500">加载中...</span>
            </div>
          )}
        </div>
      </div>

      {/* 数据列表 */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  文件信息
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  元数据
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  时空范围
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {metadataList.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col">
                      <div className="text-sm font-medium text-gray-900">
                        {item.file_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        大小: {formatFileSize(item.file_size)}
                      </div>
                      <div className="text-sm text-gray-500">
                        更新: {formatDate(item.updated_at)}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <div className="text-sm font-medium text-gray-900">
                        {item.title || '无标题'}
                      </div>
                      <div className="text-sm text-gray-500">
                        机构: {item.institution || 'N/A'}
                      </div>
                      <div className="text-sm text-gray-500">
                        来源: {item.source || 'N/A'}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col text-sm text-gray-500">
                      {item.time_coverage_start && item.time_coverage_end && (
                        <div>
                          时间: {formatDate(item.time_coverage_start)} - {formatDate(item.time_coverage_end)}
                        </div>
                      )}
                      {item.geospatial_lat_min !== undefined && item.geospatial_lat_max !== undefined && (
                        <div>
                          纬度: {item.geospatial_lat_min.toFixed(2)}° - {item.geospatial_lat_max.toFixed(2)}°
                        </div>
                      )}
                      {item.geospatial_lon_min !== undefined && item.geospatial_lon_max !== undefined && (
                        <div>
                          经度: {item.geospatial_lon_min.toFixed(2)}° - {item.geospatial_lon_max.toFixed(2)}°
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        item.processing_status === 'standard' 
                          ? 'bg-green-100 text-green-800'
                          : item.processing_status === 'processing'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {item.processing_status === 'standard' ? '标准数据' :
                         item.processing_status === 'processing' ? '处理中' : '原始数据'}
                      </span>
                      <span className={`mt-1 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        item.is_cf_compliant 
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {item.is_cf_compliant ? 'CF规范' : '非CF规范'}
                      </span>
                      {item.cf_version && (
                        <span className="mt-1 text-xs text-gray-500">
                          {item.cf_version}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <Link
                      to={`/data/metadata/${item.id}`}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      查看详情
                    </Link>
                    <button
                      onClick={() => {
                        // 这里可以添加下载功能
                        console.log('下载文件:', item.file_path);
                      }}
                      className="text-green-600 hover:text-green-900"
                    >
                      下载
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 分页 */}
        {totalPages > 1 && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                上一页
              </button>
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
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
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
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
                        onClick={() => handlePageChange(pageNum)}
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
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    下一页
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 空状态 */}
      {metadataList.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg">暂无数据</div>
          <p className="text-gray-400 mt-2">请尝试调整过滤条件或稍后再试</p>
        </div>
      )}
    </div>
  );
};

export default MetadataBrowser; 