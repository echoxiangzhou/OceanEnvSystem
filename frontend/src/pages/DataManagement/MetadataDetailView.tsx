import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { metadataService, MetadataItem } from '../../services/metadataService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';

const MetadataDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [metadata, setMetadata] = useState<MetadataItem | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 获取元数据详情
  const fetchMetadataDetail = async () => {
    if (!id) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await metadataService.getMetadataDetail(parseInt(id));
      setMetadata(data);
    } catch (err) {
      setError('获取元数据详情失败');
      console.error('获取元数据详情失败:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMetadataDetail();
  }, [id]);

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

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage message={error} retry={fetchMetadataDetail} />;
  }

  if (!metadata) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg">未找到元数据记录</div>
          <button
            onClick={() => navigate('/data/metadata')}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            返回列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      {/* 头部 */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">元数据详情</h1>
            <p className="text-gray-600">{metadata.file_name}</p>
          </div>
          <button
            onClick={() => navigate('/data/metadata')}
            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
          >
            返回列表
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 基本信息 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">基本信息</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">文件名:</span>
              <span className="font-medium">{metadata.file_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">文件路径:</span>
              <span className="font-medium text-sm break-all">{metadata.file_path}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">文件大小:</span>
              <span className="font-medium">{formatFileSize(metadata.file_size)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">创建时间:</span>
              <span className="font-medium">{formatDate(metadata.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">更新时间:</span>
              <span className="font-medium">{formatDate(metadata.updated_at)}</span>
            </div>
          </div>
        </div>

        {/* CF规范信息 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">CF规范信息</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">CF版本:</span>
              <span className="font-medium">{metadata.cf_version || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">CF规范符合性:</span>
              <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                metadata.is_cf_compliant 
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}>
                {metadata.is_cf_compliant ? '符合' : '不符合'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">处理状态:</span>
              <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                metadata.processing_status === 'standard' 
                  ? 'bg-green-100 text-green-800'
                  : metadata.processing_status === 'processing'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {metadata.processing_status === 'standard' ? '标准数据' :
                 metadata.processing_status === 'processing' ? '处理中' : '原始数据'}
              </span>
            </div>
          </div>
        </div>

        {/* 数据集元数据 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">数据集元数据</h2>
          <div className="space-y-3">
            <div>
              <span className="text-gray-600 block mb-1">标题:</span>
              <span className="font-medium">{metadata.title || 'N/A'}</span>
            </div>
            <div>
              <span className="text-gray-600 block mb-1">摘要:</span>
              <span className="font-medium">{metadata.summary || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">机构:</span>
              <span className="font-medium">{metadata.institution || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">数据来源:</span>
              <span className="font-medium">{metadata.source || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* 时空范围 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">时空范围</h2>
          <div className="space-y-3">
            <div>
              <span className="text-gray-600 block mb-1">时间范围:</span>
              {metadata.time_coverage_start && metadata.time_coverage_end ? (
                <div className="font-medium">
                  <div>开始: {formatDate(metadata.time_coverage_start)}</div>
                  <div>结束: {formatDate(metadata.time_coverage_end)}</div>
                </div>
              ) : (
                <span className="font-medium">N/A</span>
              )}
            </div>
            <div>
              <span className="text-gray-600 block mb-1">地理范围:</span>
              {metadata.geospatial_lat_min !== undefined && metadata.geospatial_lat_max !== undefined &&
               metadata.geospatial_lon_min !== undefined && metadata.geospatial_lon_max !== undefined ? (
                <div className="font-medium">
                  <div>纬度: {metadata.geospatial_lat_min.toFixed(4)}° - {metadata.geospatial_lat_max.toFixed(4)}°</div>
                  <div>经度: {metadata.geospatial_lon_min.toFixed(4)}° - {metadata.geospatial_lon_max.toFixed(4)}°</div>
                </div>
              ) : (
                <span className="font-medium">N/A</span>
              )}
            </div>
            <div>
              <span className="text-gray-600 block mb-1">垂直范围:</span>
              {metadata.geospatial_vertical_min !== undefined && metadata.geospatial_vertical_max !== undefined ? (
                <div className="font-medium">
                  {metadata.geospatial_vertical_min.toFixed(2)} - {metadata.geospatial_vertical_max.toFixed(2)} m
                </div>
              ) : (
                <span className="font-medium">N/A</span>
              )}
            </div>
          </div>
        </div>

        {/* 变量信息 */}
        {metadata.variables && Object.keys(metadata.variables).length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">变量信息</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      变量名
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      数据类型
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      形状
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      维度
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      属性
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(metadata.variables).map(([varName, varInfo]: [string, any]) => (
                    <tr key={varName} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {varName}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {varInfo.dtype || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {varInfo.shape ? `[${varInfo.shape.join(', ')}]` : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {varInfo.dimensions ? varInfo.dimensions.join(', ') : 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {varInfo.attributes && Object.keys(varInfo.attributes).length > 0 ? (
                          <div className="max-w-xs">
                            {Object.entries(varInfo.attributes).slice(0, 3).map(([attrName, attrValue]: [string, any]) => (
                              <div key={attrName} className="text-xs">
                                <span className="font-medium">{attrName}:</span> {String(attrValue).substring(0, 50)}
                                {String(attrValue).length > 50 && '...'}
                              </div>
                            ))}
                            {Object.keys(varInfo.attributes).length > 3 && (
                              <div className="text-xs text-gray-400">
                                +{Object.keys(varInfo.attributes).length - 3} 更多...
                              </div>
                            )}
                          </div>
                        ) : (
                          'N/A'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 维度信息 */}
        {metadata.dimensions && Object.keys(metadata.dimensions).length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">维度信息</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(metadata.dimensions).map(([dimName, dimInfo]: [string, any]) => (
                <div key={dimName} className="bg-gray-50 rounded-lg p-4">
                  <div className="font-medium text-gray-900">{dimName}</div>
                  <div className="text-sm text-gray-600">大小: {dimInfo.size || 'N/A'}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="mt-6 flex gap-4">
        <button
          onClick={() => {
            // 这里可以添加下载功能
            console.log('下载文件:', metadata.file_path);
          }}
          className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
        >
          下载文件
        </button>
        <button
          onClick={() => {
            // 这里可以添加编辑功能
            console.log('编辑元数据:', metadata.id);
          }}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
        >
          编辑元数据
        </button>
      </div>
    </div>
  );
};

export default MetadataDetailView; 