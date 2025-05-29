import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { dataService } from '../../services';

const DatasetDetailView: React.FC = () => {
  const { datasetPath } = useParams<{ datasetPath: string }>();
  const navigate = useNavigate();
  const [metadata, setMetadata] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetadata = async () => {
      setIsLoading(true);
      setError(null);

      if (!datasetPath) {
        setError('数据集路径不能为空');
        setIsLoading(false);
        return;
      }

      try {
        // 解码URL路径
        const decodedPath = decodeURIComponent(datasetPath);
        
        // 使用API获取元数据
        const res = await dataService.getOpendapMetadataByPath(decodedPath);
        
        if (res && !res.error) {
          setMetadata(res);
        } else {
          setError(res?.error || '获取元数据失败');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取元数据时发生未知错误');
      } finally {
        setIsLoading(false);
      }
    };

    fetchMetadata();
  }, [datasetPath]);

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

  // 下载数据集
  const handleDownload = async () => {
    if (!datasetPath) return;
    try {
      const decodedPath = decodeURIComponent(datasetPath);
      const fileName = decodedPath.split('/').pop() || 'dataset.nc';
      await dataService.downloadThreddsFile(decodedPath, fileName);
    } catch (err) {
      console.error('下载数据集失败:', err);
      // 可以添加提示
      alert('下载失败: ' + (err instanceof Error ? err.message : String(err)));
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* 头部导航 */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400 mb-3">
          <Link to="/data" className="hover:text-blue-500 dark:hover:text-blue-400">数据浏览</Link>
          <span>/</span>
          <span className="text-gray-900 dark:text-white font-medium">数据集详情</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {isLoading ? '加载中...' : metadata?.title || '数据集详情'}
        </h1>
        {datasetPath && (
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            数据集路径: {decodeURIComponent(datasetPath)}
          </p>
        )}
      </div>

      {/* 加载状态 */}
      {isLoading && (
        <div className="flex justify-center py-10">
          <LoadingSpinner />
        </div>
      )}

      {/* 错误状态 */}
      {!isLoading && error && (
        <ErrorMessage 
          message={`获取数据集详情失败: ${error}`} 
          retry={() => navigate(0)} // 刷新页面
        />
      )}

      {/* 详情内容 */}
      {!isLoading && !error && metadata && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
          {/* 主信息 */}
          <div className="p-6">
            <div className="mb-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                {metadata.title || '未命名数据集'}
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                {metadata.description || '无描述信息'}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 基本信息 */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">基本信息</h3>
                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-md">
                    {/* 时间范围 */}
                    {metadata.time_range && !metadata.time_range.error && (
                      <div className="mb-3">
                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">时间范围:</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {formatDate(metadata.time_range.start)} ~ {formatDate(metadata.time_range.end)}
                          {metadata.time_range.count ? ` (共${metadata.time_range.count}步)` : ''}
                        </p>
                      </div>
                    )}

                    {/* 显示时间范围错误信息 */}
                    {metadata.time_range?.error && (
                      <div className="mb-3">
                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">时间范围:</p>
                        <p className="text-sm text-red-500">{metadata.time_range.error}</p>
                      </div>
                    )}

                    {/* 空间范围 */}
                    {metadata.spatial_range && !metadata.spatial_range.error && (
                      <div className="mb-3">
                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">空间范围:</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          经度: {metadata.spatial_range.longitude.min.toFixed(2)} ~ {metadata.spatial_range.longitude.max.toFixed(2)} 
                          {metadata.spatial_range.longitude.units ? ` (${metadata.spatial_range.longitude.units})` : ''}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          纬度: {metadata.spatial_range.latitude.min.toFixed(2)} ~ {metadata.spatial_range.latitude.max.toFixed(2)}
                          {metadata.spatial_range.latitude.units ? ` (${metadata.spatial_range.latitude.units})` : ''}
                        </p>
                      </div>
                    )}

                    {/* 显示空间范围错误信息 */}
                    {metadata.spatial_range?.error && (
                      <div className="mb-3">
                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">空间范围:</p>
                        <p className="text-sm text-red-500">{metadata.spatial_range.error}</p>
                      </div>
                    )}

                    {/* 生产者/来源信息 */}
                    {metadata.source_information && Object.keys(metadata.source_information).length > 0 && (
                      <div className="mb-3">
                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">生产者/来源:</p>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {Object.entries(metadata.source_information).map(([key, value]: [string, any]) => (
                            <p key={key}>{key}: {value}</p>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 创建日期 */}
                    {metadata.creation_date && (
                      <div className="mb-3">
                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">创建日期:</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{formatDate(metadata.creation_date)}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* 维度信息 */}
                {metadata.dimensions && Object.keys(metadata.dimensions).length > 0 && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">维度信息</h3>
                    <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-md">
                      <div className="grid grid-cols-2 gap-3">
                        {Object.entries(metadata.dimensions).map(([name, size]) => (
                          <div key={name} className="flex items-baseline">
                            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 mr-2">{name}:</span>
                            <span className="text-sm text-gray-600 dark:text-gray-400">{String(size)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* 变量信息 */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">变量信息</h3>
                {metadata.variables && Array.isArray(metadata.variables) && metadata.variables.length > 0 ? (
                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-md max-h-96 overflow-y-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
                      <thead className="bg-gray-50 dark:bg-gray-700">
                        <tr>
                          <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            名称
                          </th>
                          <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            单位
                          </th>
                          <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            描述
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                        {metadata.variables.map((variable: any, index: number) => (
                          <tr key={index} className={index % 2 === 0 ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-700'}>
                            <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                              {variable.name}
                            </td>
                            <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                              {variable.units || '-'}
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
                              {variable.long_name || variable.standard_name || '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-md">
                    <p className="text-gray-500 dark:text-gray-400">无变量信息</p>
                  </div>
                )}
              </div>
            </div>

            {/* 全局属性 */}
            {metadata.global_attributes && Object.keys(metadata.global_attributes).length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">全局属性</h3>
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-md max-h-96 overflow-y-auto">
                  <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
                    {Object.entries(metadata.global_attributes).map(([name, value]: [string, any]) => (
                      <div key={name} className="border-b border-gray-200 dark:border-gray-600 pb-2 mb-2">
                        <dt className="text-sm font-medium text-gray-700 dark:text-gray-300">{name}</dt>
                        <dd className="mt-1 text-sm text-gray-500 dark:text-gray-400 break-words">{String(value)}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </div>
            )}
          </div>

          {/* 操作按钮 */}
          <div className="bg-gray-50 dark:bg-gray-700 px-6 py-4 flex justify-between items-center">
            <Link
              to="/data"
              className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              返回
            </Link>
            <div className="flex space-x-3">
              <button
                onClick={handleDownload}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                下载数据集
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatasetDetailView;