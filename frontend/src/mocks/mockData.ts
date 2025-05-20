import { Dataset, DatasetMetadata } from '../types/api';

// 模拟数据集
export const mockDatasets: Dataset[] = [
  {
    id: '1',
    name: '南海表层温度数据',
    description: '2023年南海区域表层温度数据集，包含每日平均温度',
    source_type: 'SATELLITE',
    data_type: 'OBSERVATIONS',
    spatial_coverage: {
      type: 'Polygon',
      coordinates: [[[110, 10], [120, 10], [120, 20], [110, 20], [110, 10]]]
    },
    temporal_coverage: {
      start: '2023-01-01T00:00:00Z',
      end: '2023-12-31T23:59:59Z'
    },
    variables: [
      {
        name: 'temperature',
        standard_name: 'sea_surface_temperature',
        unit: '°C',
        description: '海表温度'
      },
      {
        name: 'quality_flag',
        unit: '',
        description: '质量标识'
      }
    ],
    file_format: 'nc',
    file_location: 'oceandata/temperature_2023.nc',
    created_at: '2023-12-01T08:00:00Z',
    updated_at: '2023-12-01T08:00:00Z'
  },
  {
    id: '2',
    name: '南海表层盐度数据',
    description: '2023年南海区域表层盐度数据集，包含每日平均盐度',
    source_type: 'MODEL',
    data_type: 'REANALYSIS',
    spatial_coverage: {
      type: 'Polygon',
      coordinates: [[[110, 10], [120, 10], [120, 20], [110, 20], [110, 10]]]
    },
    temporal_coverage: {
      start: '2023-01-01T00:00:00Z',
      end: '2023-12-31T23:59:59Z'
    },
    variables: [
      {
        name: 'salinity',
        standard_name: 'sea_surface_salinity',
        unit: 'psu',
        description: '海表盐度'
      },
      {
        name: 'quality_flag',
        unit: '',
        description: '质量标识'
      }
    ],
    file_format: 'nc',
    file_location: 'oceandata/salinity_2023.nc',
    created_at: '2023-12-02T10:30:00Z',
    updated_at: '2023-12-02T10:30:00Z'
  },
  {
    id: '3',
    name: '站点1号CTD数据',
    description: '2023年测量站点1号的CTD观测数据',
    source_type: 'SURVEY',
    data_type: 'OBSERVATIONS',
    spatial_coverage: {
      type: 'Polygon',
      coordinates: [[[115.5, 15.5], [115.6, 15.5], [115.6, 15.6], [115.5, 15.6], [115.5, 15.5]]]
    },
    temporal_coverage: {
      start: '2023-05-15T00:00:00Z',
      end: '2023-05-15T23:59:59Z'
    },
    variables: [
      {
        name: 'temperature',
        standard_name: 'sea_water_temperature',
        unit: '°C',
        description: '海水温度'
      },
      {
        name: 'salinity',
        standard_name: 'sea_water_salinity',
        unit: 'psu',
        description: '海水盐度'
      },
      {
        name: 'pressure',
        standard_name: 'sea_water_pressure',
        unit: 'dbar',
        description: '海水压力'
      }
    ],
    file_format: 'nc',
    file_location: 'oceandata/ctd/station_01.nc',
    created_at: '2023-05-16T14:20:00Z',
    updated_at: '2023-05-16T14:20:00Z'
  }
];

// 模拟OPeNDAP数据
export const mockOpenDAPData: DatasetMetadata = {
  variables: ['time', 'latitude', 'longitude', 'temperature', 'salinity', 'u', 'v'],
  dims: {
    time: 365,
    latitude: 100,
    longitude: 100,
    depth: 50
  },
  attrs: {
    title: '南海数值模式数据集',
    institution: '海洋环境研究所',
    source: '数值模拟',
    references: 'http://example.org/reference',
    Conventions: 'CF-1.6',
    history: '2023-12-01 创建',
    creator_name: '数据团队',
    creator_email: 'data@example.org'
  }
};
