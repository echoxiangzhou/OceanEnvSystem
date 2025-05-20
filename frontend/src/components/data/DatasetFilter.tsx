import React, { useState } from 'react';
import { Dataset } from '../../types/api';

interface DatasetFilterProps {
  onFilterChange: (filters: FilterOptions) => void;
}

export interface FilterOptions {
  searchText: string;
  sourceType: Dataset['source_type'] | 'ALL';
  dataType: Dataset['data_type'] | 'ALL';
  sortBy: 'name' | 'created_at' | 'updated_at';
  sortOrder: 'asc' | 'desc';
}

const DatasetFilter: React.FC<DatasetFilterProps> = ({ onFilterChange }) => {
  const [filters, setFilters] = useState<FilterOptions>({
    searchText: '',
    sourceType: 'ALL',
    dataType: 'ALL',
    sortBy: 'created_at',
    sortOrder: 'desc'
  });

  // 处理搜索文本变化
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newFilters = { ...filters, searchText: e.target.value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  // 处理源类型筛选变化
  const handleSourceTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newFilters = { ...filters, sourceType: e.target.value as Dataset['source_type'] | 'ALL' };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  // 处理数据类型筛选变化
  const handleDataTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newFilters = { ...filters, dataType: e.target.value as Dataset['data_type'] | 'ALL' };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  // 处理排序变化
  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const [sortBy, sortOrder] = e.target.value.split('-') as ['name' | 'created_at' | 'updated_at', 'asc' | 'desc'];
    const newFilters = { ...filters, sortBy, sortOrder };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  // 清空所有筛选
  const clearFilters = () => {
    const newFilters = {
      searchText: '',
      sourceType: 'ALL',
      dataType: 'ALL',
      sortBy: 'created_at',
      sortOrder: 'desc'
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4 mb-6">
      <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">搜索与筛选</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 搜索框 */}
        <div>
          <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">搜索</label>
          <div className="relative rounded-md shadow-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
              </svg>
            </div>
            <input
              type="text"
              id="search"
              value={filters.searchText}
              onChange={handleSearchChange}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="搜索数据集名称..."
            />
          </div>
        </div>

        {/* 源类型筛选 */}
        <div>
          <label htmlFor="source-type" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">源类型</label>
          <select
            id="source-type"
            value={filters.sourceType}
            onChange={handleSourceTypeChange}
            className="block w-full py-2 pl-3 pr-10 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-gray-900 dark:text-white sm:text-sm"
          >
            <option value="ALL">全部类型</option>
            <option value="BUOY">浮标</option>
            <option value="SURVEY">调查</option>
            <option value="SATELLITE">卫星</option>
            <option value="MODEL">模型</option>
          </select>
        </div>

        {/* 数据类型筛选 */}
        <div>
          <label htmlFor="data-type" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">数据类型</label>
          <select
            id="data-type"
            value={filters.dataType}
            onChange={handleDataTypeChange}
            className="block w-full py-2 pl-3 pr-10 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-gray-900 dark:text-white sm:text-sm"
          >
            <option value="ALL">全部类型</option>
            <option value="OBSERVATIONS">观测</option>
            <option value="FORECAST">预报</option>
            <option value="REANALYSIS">再分析</option>
          </select>
        </div>

        {/* 排序选项 */}
        <div>
          <label htmlFor="sort-by" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">排序方式</label>
          <select
            id="sort-by"
            value={`${filters.sortBy}-${filters.sortOrder}`}
            onChange={handleSortChange}
            className="block w-full py-2 pl-3 pr-10 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-gray-900 dark:text-white sm:text-sm"
          >
            <option value="name-asc">名称 (A-Z)</option>
            <option value="name-desc">名称 (Z-A)</option>
            <option value="created_at-desc">创建时间 (新-旧)</option>
            <option value="created_at-asc">创建时间 (旧-新)</option>
            <option value="updated_at-desc">更新时间 (新-旧)</option>
            <option value="updated_at-asc">更新时间 (旧-新)</option>
          </select>
        </div>
      </div>

      {/* 清空筛选按钮 */}
      <div className="mt-4 flex justify-end">
        <button
          type="button"
          onClick={clearFilters}
          className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800"
        >
          <svg className="-ml-0.5 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          清空筛选
        </button>
      </div>
    </div>
  );
};

export default DatasetFilter;
