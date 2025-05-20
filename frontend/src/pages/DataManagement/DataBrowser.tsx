import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useDatasets, useDeleteDataset } from '../../hooks/useDataHooks';
import { Dataset } from '../../types/api';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import DatasetListItem from '../../components/data/DatasetListItem';
import DatasetDetailModal from '../../components/data/DatasetDetailModal';
import DeleteConfirmModal from '../../components/data/DeleteConfirmModal';
import DatasetFilter, { FilterOptions } from '../../components/data/DatasetFilter';
import { dataService } from '../../services';
import OpenDAPBrowser from '../../components/opendap/OpenDAPBrowser';

const DataBrowser: React.FC = () => {
  // Tab切换：local为本地，opendap为远程
  const [activeTab, setActiveTab] = useState<'local' | 'opendap'>('local');
  const [opendapSelected, setOpendapSelected] = useState<any>(null);

  // 状态管理
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [filters, setFilters] = useState<FilterOptions>({
    searchText: '',
    sourceType: 'ALL',
    dataType: 'ALL',
    sortBy: 'created_at',
    sortOrder: 'desc'
  });

  // 获取数据集列表
  const { 
    data: datasetsResponse, 
    isLoading, 
    isError, 
    error, 
    refetch: refetchDatasets 
  } = useDatasets();

  // 删除数据集的mutation
  const { 
    mutate: deleteDataset, 
    isPending: isDeleting, 
    isSuccess: isDeleteSuccess,
    error: deleteError
  } = useDeleteDataset();

  // 如果删除成功，关闭删除确认对话框
  useEffect(() => {
    if (isDeleteSuccess) {
      setIsDeleteModalOpen(false);
    }
  }, [isDeleteSuccess]);

  // 处理数据集过滤和排序逻辑
  const filteredDatasets = useMemo(() => {
    if (!datasetsResponse?.data) return [];

    let result = [...datasetsResponse.data];

    // 按搜索文本筛选
    if (filters.searchText) {
      const searchLower = filters.searchText.toLowerCase();
      result = result.filter(dataset => 
        dataset.name.toLowerCase().includes(searchLower) || 
        dataset.description.toLowerCase().includes(searchLower)
      );
    }

    // 按源类型筛选
    if (filters.sourceType !== 'ALL') {
      result = result.filter(dataset => dataset.source_type === filters.sourceType);
    }

    // 按数据类型筛选
    if (filters.dataType !== 'ALL') {
      result = result.filter(dataset => dataset.data_type === filters.dataType);
    }

    // 排序
    result.sort((a, b) => {
      let valueA, valueB;
      switch (filters.sortBy) {
        case 'name':
          valueA = a.name;
          valueB = b.name;
          break;
        case 'created_at':
          valueA = new Date(a.created_at).getTime();
          valueB = new Date(b.created_at).getTime();
          break;
        case 'updated_at':
          valueA = new Date(a.updated_at).getTime();
          valueB = new Date(b.updated_at).getTime();
          break;
        default:
          valueA = a.name;
          valueB = b.name;
      }

      if (filters.sortOrder === 'asc') {
        return valueA > valueB ? 1 : -1;
      } else {
        return valueA < valueB ? 1 : -1;
      }
    });

    return result;
  }, [datasetsResponse?.data, filters]);

  // 处理查看数据集详情
  const handleViewDataset = (dataset: Dataset) => {
    setSelectedDataset(dataset);
    setIsDetailModalOpen(true);
  };

  // 处理删除数据集按钮点击
  const handleDeleteClick = (dataset: Dataset) => {
    setSelectedDataset(dataset);
    setIsDeleteModalOpen(true);
  };

  // 确认删除数据集
  const handleConfirmDelete = () => {
    if (selectedDataset) {
      deleteDataset(selectedDataset.id);
    }
  };

  // 处理下载数据集
  const handleDownloadDataset = async (dataset: Dataset) => {
    try {
      // 从文件路径中提取文件名
      const fileName = dataset.file_location.split('/').pop() || `dataset-${dataset.id}.${dataset.file_format}`;
      await dataService.downloadDataFile(dataset.file_location, fileName);
    } catch (err) {
      console.error('下载文件失败:', err);
      // 可以在这里添加提示用户下载失败的逻辑
    }
  };

  // 处理筛选条件更改
  const handleFilterChange = (newFilters: FilterOptions) => {
    setFilters(newFilters);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex space-x-4 mb-6">
        <button
          className={`px-4 py-2 rounded-t ${activeTab === 'local' ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
          onClick={() => setActiveTab('local')}
        >
          本地数据集
        </button>
        <button
          className={`px-4 py-2 rounded-t ${activeTab === 'opendap' ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
          onClick={() => setActiveTab('opendap')}
        >
          OPeNDAP远程数据
        </button>
      </div>

      {activeTab === 'local' && (
        <>
          {/* 筛选组件 */}
          <DatasetFilter onFilterChange={handleFilterChange} />

          {/* 删除错误提示 */}
          {deleteError && (
            <ErrorMessage message={`删除数据集失败: ${deleteError?.message || '未知错误'}`} />
          )}

          {/* 数据集列表 */}
          <div className="mt-6">
            {filteredDatasets.length === 0 ? (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">没有找到数据集</h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {datasetsResponse?.data?.length ? '没有符合当前筛选条件的数据集。' : '还没有添加任何数据集，点击"导入数据"开始添加。'}
                </p>
                {datasetsResponse?.data?.length > 0 && (
                  <div className="mt-4">
                    <button
                      onClick={() => setFilters({
                        searchText: '',
                        sourceType: 'ALL',
                        dataType: 'ALL',
                        sortBy: 'created_at',
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
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                  找到 {filteredDatasets.length} 个数据集
                  {datasetsResponse?.data && filteredDatasets.length !== datasetsResponse.data.length && 
                    `（共 ${datasetsResponse.data.length} 个）`}
                </p>
                <div>
                  {filteredDatasets.map(dataset => (
                    <DatasetListItem
                      key={dataset.id}
                      dataset={dataset}
                      onView={() => handleViewDataset(dataset)}
                      onDelete={() => handleDeleteClick(dataset)}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 数据集详情对话框 */}
          <DatasetDetailModal
            dataset={selectedDataset}
            isOpen={isDetailModalOpen}
            onClose={() => setIsDetailModalOpen(false)}
            onDownload={handleDownloadDataset}
          />

          {/* 删除确认对话框 */}
          <DeleteConfirmModal
            dataset={selectedDataset}
            isOpen={isDeleteModalOpen}
            onCancel={() => setIsDeleteModalOpen(false)}
            onConfirm={handleConfirmDelete}
            isDeleting={isDeleting}
          />
        </>
      )}

      {activeTab === 'opendap' && (
        <div className="mt-6">
          <OpenDAPBrowser onDatasetSelect={setOpendapSelected} />
          {/* 可选：展示OPeNDAP选择结果详情，可根据需要扩展 */}
        </div>
      )}
    </div>
  );
};

export default DataBrowser;
