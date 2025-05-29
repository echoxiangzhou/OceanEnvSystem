import React from 'react';
import { Dataset } from '../../types/api';
import { Link } from 'react-router-dom';

interface DatasetListItemProps {
  dataset: Dataset;
  onView: (dataset: Dataset) => void;
  onDelete: ((dataset: Dataset) => void) | null;
  enhancedMetadata?: any;
  isLoadingEnhanced?: boolean;
}

const DatasetListItem: React.FC<DatasetListItemProps> = ({ dataset, onView, onDelete, enhancedMetadata, isLoadingEnhanced }) => {
  // 格式化日期显示
  const formatDate = (dateString?: string) => {
    if (!dateString) return '无日期信息';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return '日期格式无效';
      }
      return new Intl.DateTimeFormat('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }).format(date);
    } catch (e) {
      console.error('Date formatting error:', e, dateString);
      return '日期格式错误';
    }
  };

  // 从文件名中提取元数据（用于错误处理情况）
  const extractMetadataFromFilename = (filename: string) => {
    // 处理类似 cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m_thetao_104.33E-132.92E_12.25N-42.17N_0.49-5274.78m_2024-07-11-2024-07-30.nc 的文件名
    let meta: any = {
      title: filename,
      description: "从文件名解析的基本信息",
      time_range: { start: null, end: null },
      spatial_range: {
        longitude: { min: null, max: null, units: "degrees_east" },
        latitude: { min: null, max: null, units: "degrees_north" }
      },
      source_information: { institution: "未知" }
    };

    try {
      // 尝试提取时间范围
      const timeMatch = filename.match(/(\d{4}-\d{2}-\d{2})-(\d{4}-\d{2}-\d{2})/);
      if (timeMatch && timeMatch.length >= 3) {
        meta.time_range.start = timeMatch[1] + "T00:00:00Z";
        meta.time_range.end = timeMatch[2] + "T00:00:00Z";
      }

      // 尝试提取空间范围（经度）
      const lonMatch = filename.match(/(\d+\.\d+)E-(\d+\.\d+)E/);
      if (lonMatch && lonMatch.length >= 3) {
        meta.spatial_range.longitude.min = parseFloat(lonMatch[1]);
        meta.spatial_range.longitude.max = parseFloat(lonMatch[2]);
      }

      // 尝试提取空间范围（纬度）
      const latMatch = filename.match(/(\d+\.\d+)N-(\d+\.\d+)N/);
      if (latMatch && latMatch.length >= 3) {
        meta.spatial_range.latitude.min = parseFloat(latMatch[1]);
        meta.spatial_range.latitude.max = parseFloat(latMatch[2]);
      }

      // 尝试提取深度范围
      const depthMatch = filename.match(/(\d+\.\d+)-(\d+\.\d+)m/);
      if (depthMatch && depthMatch.length >= 3) {
        meta.depth_range = {
          min: parseFloat(depthMatch[1]),
          max: parseFloat(depthMatch[2]),
          units: "m"
        };
      }

      // 尝试提取变量名
      const varMatch = filename.match(/phy-([a-zA-Z0-9_]+)_/);
      if (varMatch && varMatch.length >= 2) {
        meta.variables = [{
          name: varMatch[1],
          long_name: varMatch[1]
        }];
      }

      // 尝试从文件名生成更友好的标题
      try {
        // 提取主要组件以创建更清晰的标题
        if (filename.includes('_anfc_')) {
          // 提取主要表示的变量
          let variable = '';
          let region = '';
          
          // 尝试获取变量名
          const varNames = {
            'thetao': 'Temperature',
            'so': 'Salinity',
            'uo': 'Eastward Velocity',
            'vo': 'Northward Velocity',
            'ssh': 'Sea Surface Height',
            'zos': 'Sea Surface Height',
            'cur': 'Currents'
          };
          
          // 查找最后一个下划线之前的变量名
          const specificVarMatch = filename.match(/_([a-zA-Z0-9_-]+)_\d+\.\d+E/);
          if (specificVarMatch && specificVarMatch.length >= 2) {
            const specificVarKey = specificVarMatch[1];
            variable = varNames[specificVarKey] || specificVarKey;
          }
          
          // 提取区域
          if (lonMatch && latMatch) {
            region = `${lonMatch[1]}°E-${lonMatch[2]}°E, ${latMatch[1]}°N-${latMatch[2]}°N`;
          }
          
          // 创建有意义的标题
          if (variable && region) {
            meta.title = `Global Ocean ${variable} Forecast (${region})`;
          } else if (variable) {
            meta.title = `Global Ocean ${variable} Forecast`;
          } else {
            meta.title = 'Global Ocean Forecast';
          }
          
          // 添加时间范围
          if (timeMatch) {
            meta.title += ` ${timeMatch[1]} to ${timeMatch[2]}`;
          }
        }
      } catch (e) {
        console.error("Error creating friendly title:", e);
      }

      // 尝试提取数据来源
      if (filename.startsWith('cmems_')) {
        meta.source_information.institution = "Copernicus Marine Service";
        meta.source_information.source = filename.split('_')[0] + "_" + filename.split('_')[1];
      }
    } catch (e) {
      console.error("Error extracting metadata from filename:", e);
    }

    return meta;
  };

  // 获取数据类型的中文显示
  const getSourceTypeLabel = (type: Dataset['source_type']) => {
    if (!type) return '未知类型';
    
    const labels: Record<string, string> = {
      'BUOY': '浮标',
      'SURVEY': '调查',
      'SATELLITE': '卫星',
      'MODEL': '模型'
    };
    return labels[type] || type;
  };

  // 获取数据种类的中文显示
  const getDataTypeLabel = (type: Dataset['data_type']) => {
    if (!type) return '未知种类';
    
    const labels: Record<string, string> = {
      'OBSERVATIONS': '观测',
      'FORECAST': '预报',
      'REANALYSIS': '再分析'
    };
    return labels[type] || type;
  };

  // 加载状态
  if (isLoadingEnhanced) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden mb-4 p-5 flex items-center justify-center min-h-[150px]">
        <span className="text-xs text-gray-400 animate-pulse">正在加载元数据...</span>
      </div>
    );
  }

  // 从URL或文件名中提取显示名称
  const getDisplayName = () => {
    const fileName = dataset.name || 
                    dataset.urlPath?.split('/').pop() || 
                    dataset.file_location?.split('/').pop() || 
                    '未知数据集';
    return fileName;
  };
  
  // 尝试从文件名解析基本信息
  const fileName = getDisplayName();
  const extractedMeta = extractMetadataFromFilename(fileName);

  // 增强元数据错误处理
  let errorMessage: string | null = null;
  let usingExtractedData = false;
  
  if (enhancedMetadata) {
    if (typeof enhancedMetadata.error === 'string') {
      errorMessage = enhancedMetadata.error;
      usingExtractedData = true;
    } else if (typeof enhancedMetadata.detail === 'string') { // 常见 FastAPI 错误
      errorMessage = enhancedMetadata.detail;
      usingExtractedData = true;
    } else if (Array.isArray(enhancedMetadata.detail) && enhancedMetadata.detail[0] && typeof enhancedMetadata.detail[0].msg === 'string') { // Pydantic 详细错误
      errorMessage = `输入验证错误: ${enhancedMetadata.detail[0].msg} (字段: ${enhancedMetadata.detail[0].loc.join(' -> ')})`;
      usingExtractedData = true;
    } else if (enhancedMetadata.hasOwnProperty('type') && enhancedMetadata.hasOwnProperty('loc') && enhancedMetadata.hasOwnProperty('msg') && enhancedMetadata.hasOwnProperty('input')) {
      // 针对特定错误对象 {type, loc, msg, input} 的启发式检查
      errorMessage = `处理请求时发生错误: ${enhancedMetadata.msg || '未知错误详情'}`;
      usingExtractedData = true;
    } else if (typeof enhancedMetadata === 'object' && enhancedMetadata !== null && !isLoadingEnhanced && !enhancedMetadata.title && !enhancedMetadata.global_attributes?.title) {
      // 如果 enhancedMetadata 是一个非空对象，当前不处于加载状态，并且它没有 title 属性，
      // 那么我们认为它可能是一个无法直接显示的错误对象或无效的元数据格式。
      errorMessage = '';
      usingExtractedData = true;
      console.debug('无效的元数据格式:', enhancedMetadata);
    }
  }

  // 尝试使用有效数据：
  // 1. 优先使用增强元数据中的 title
  // 2. 如果增强元数据没有 title，但有 global_attributes.title，则使用它
  // 3. 如果有错误则回退到从文件名解析的数据
  const meta = usingExtractedData ? extractedMeta : enhancedMetadata;

  // 标题处理 - 优先使用后端返回的title
  const title = (!usingExtractedData && enhancedMetadata) ? 
                (enhancedMetadata.title || 
                 enhancedMetadata.global_attributes?.title || 
                 extractedMeta.title || 
                 fileName) :
                (extractedMeta.title || fileName);
  
  // 时间范围
  let timeRange = '-';
  if (meta?.time_range?.start && meta?.time_range?.end) {
    // 如果有计数值，显示步数
    const countInfo = meta.time_range.count ? ` (共${meta.time_range.count}步)` : '';
    timeRange = `${formatDate(meta.time_range.start)} ~ ${formatDate(meta.time_range.end)}${countInfo}`;
  } else if (dataset.temporal_coverage?.start && dataset.temporal_coverage?.end) {
    timeRange = `${formatDate(dataset.temporal_coverage.start)} ~ ${formatDate(dataset.temporal_coverage.end)}`;
  }

  // 空间范围
  let spatialRange = '-';
  if (meta?.spatial_range?.longitude && meta?.spatial_range?.latitude) {
    spatialRange = `经: ${meta.spatial_range.longitude.min?.toFixed(2)}~${meta.spatial_range.longitude.max?.toFixed(2)}, 纬: ${meta.spatial_range.latitude.min?.toFixed(2)}~${meta.spatial_range.latitude.max?.toFixed(2)}`;
  } else if (dataset.spatial_coverage?.coordinates?.[0]) {
    const coordinates = dataset.spatial_coverage.coordinates[0];
    let minLon = Infinity, maxLon = -Infinity, minLat = Infinity, maxLat = -Infinity;
    coordinates.forEach(([lon, lat]) => {
      minLon = Math.min(minLon, lon);
      maxLon = Math.max(maxLon, lon);
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
    });
    spatialRange = `经: ${minLon.toFixed(2)}~${maxLon.toFixed(2)}, 纬: ${minLat.toFixed(2)}~${maxLat.toFixed(2)}`;
  }

  // 生产者/创建者
  let producer = '-';
  if (meta?.source_information) {
    if (typeof meta.source_information === 'object' && meta.source_information !== null) {
      if (typeof meta.source_information.institution === 'string' && meta.source_information.institution) {
        producer = meta.source_information.institution;
      } else if (typeof meta.source_information.creator === 'string' && meta.source_information.creator) {
        producer = meta.source_information.creator;
      } else {
        const firstVal = Object.values(meta.source_information).find(v => typeof v === 'string' && v);
        producer = typeof firstVal === 'string' ? firstVal : '-';
      }
    } else if (typeof meta.source_information === 'string') {
      producer = meta.source_information;
    }
  } else if (meta?.global_attributes?.institution) {
    producer = meta.global_attributes.institution;
  }

  // 创建时间
  const creationDate = meta?.creation_date ? formatDate(meta.creation_date) : formatDate(dataset.created_at);

  // 变量
  let variablesList = '-';
  if (meta?.variables && Array.isArray(meta.variables) && meta.variables.length > 0) {
    variablesList = meta.variables.map((v: any) => v.name || '未命名变量').join(', ');
  } else if (dataset.variables && Array.isArray(dataset.variables) && dataset.variables.length > 0) {
    variablesList = dataset.variables.map(v => v.name || '未命名变量').filter(Boolean).join(', ');
  }

  // 准备详情页URL
  const detailUrl = dataset.urlPath ? 
    `/data/detail/${encodeURIComponent(dataset.urlPath)}` : 
    null;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden mb-4 transition-all hover:shadow-md">
      <div className="p-5">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 cursor-pointer" onClick={() => onView(dataset)}>{title}</h3>
          <div className="flex-shrink-0 flex space-x-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">
              {getSourceTypeLabel(dataset.source_type)}
            </span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300">
              {getDataTypeLabel(dataset.data_type)}
            </span>
          </div>
        </div>
        
        {/* 错误信息显示 */}
        {errorMessage && (
          <div className="mb-2 py-1 px-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-md">
            <p className="text-xs text-yellow-700 dark:text-yellow-500">
              {errorMessage}
              {extractedMeta && ' 已从文件名提取基本信息。'}
            </p>
          </div>
        )}
        
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 text-xs text-gray-600 dark:text-gray-400">
          <div className="truncate">
            <span className="font-medium text-gray-700 dark:text-gray-300">时间范围: </span>
            {timeRange}
          </div>
          <div className="truncate">
            <span className="font-medium text-gray-700 dark:text-gray-300">空间范围: </span>
            {spatialRange}
          </div>
          <div className="truncate">
            <span className="font-medium text-gray-700 dark:text-gray-300">生产者: </span>
            {producer}
          </div>
          <div className="truncate">
            <span className="font-medium text-gray-700 dark:text-gray-300">创建时间: </span>
            {creationDate}
          </div>
          <div className="md:col-span-2 truncate">
            <span className="font-medium text-gray-700 dark:text-gray-300">变量: </span>
            {variablesList}
          </div>
        </div>
        
        <div className="mt-4 flex justify-end space-x-3">
          {/* 模态框查看 */}
          <button
            onClick={() => onView(dataset)}
            className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800 transition-colors"
          >
            快速查看
          </button>
          
          {/* 详情页链接 */}
          {detailUrl && (
            <Link
              to={detailUrl}
              className="inline-flex items-center px-3 py-1.5 border border-blue-300 dark:border-blue-600 text-xs font-medium rounded-md shadow-sm text-blue-700 dark:text-blue-300 bg-white dark:bg-gray-700 hover:bg-blue-50 dark:hover:bg-blue-900/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800 transition-colors"
            >
              查看详情
            </Link>
          )}
          
          {/* 删除按钮 */}
          {onDelete && (
            <button
              onClick={() => onDelete(dataset)}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-xs font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:focus:ring-offset-gray-800 transition-colors"
            >
              删除
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default DatasetListItem;