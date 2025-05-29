import xarray as xr
from typing import List, Dict, Any, Optional

class OpendapClient:
    def __init__(self, base_url: str):
        """
        base_url: TDS OPeNDAP 服务的根URL，例如 http://localhost:8080/thredds/dodsC/
        """
        self.base_url = base_url.rstrip('/')

    def open_dataset(self, dataset_path: str) -> xr.Dataset:
        """
        通过 OPeNDAP URL 远程打开 NetCDF 数据集
        dataset_path: 例如 'mydata/test.nc'，会拼接到 base_url 后
        """
        url = f"{self.base_url}/{dataset_path.lstrip('/')}"
        try:
            ds = xr.open_dataset(url, engine="netcdf4")
            return ds
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error opening dataset {url}: {str(e)}")
            raise

    def list_variables(self, dataset_path: str) -> List[str]:
        """
        列出数据集中的所有变量名
        """
        ds = self.open_dataset(dataset_path)
        return list(ds.variables.keys())

    def get_metadata(self, dataset_path: str) -> Dict[str, Any]:
        """
        获取数据集的元数据信息
        """
        ds = self.open_dataset(dataset_path)
        return {var: dict(ds[var].attrs) for var in ds.variables}
        
    def get_enhanced_metadata(self, dataset_path: str) -> Dict[str, Any]:
        """
        获取OPeNDAP数据集的增强元数据，包括以下信息：
        - 标题、描述
        - 时间范围（起止日期）
        - 空间范围（经纬度边界）
        - 数据创建者/机构信息
        - 创建日期
        - 变量详情
        """
        # 构造完整URL
        url = f"{self.base_url}/{dataset_path.lstrip('/')}"
        
        try:
            # 使用xarray打开数据集
            ds = xr.open_dataset(url, engine="netcdf4", decode_times=True)
            metadata = {}
            
            # 1. 数据集标题和描述
            metadata['title'] = ds.attrs.get('title', ds.attrs.get('name', dataset_path.split('/')[-1]))
            metadata['description'] = ds.attrs.get('summary', ds.attrs.get('description', 'No description available.'))
            
            # 2. 时间范围
            time_var_names = ['time', 'TIME', 'Time', 't']
            time_coord = None
            for name in time_var_names:
                if name in ds.coords:
                    time_coord = ds.coords[name]
                    break
            
            if time_coord is not None and time_coord.size > 0:
                try:
                    # 尝试获取时间范围
                    min_time = time_coord.min().values
                    max_time = time_coord.max().values
                    metadata['time_range'] = {
                        'start': min_time.isoformat() if hasattr(min_time, 'isoformat') else str(min_time),
                        'end': max_time.isoformat() if hasattr(max_time, 'isoformat') else str(max_time),
                        'count': len(time_coord)
                    }
                except Exception as e:
                    metadata['time_range'] = {'error': f"无法解析时间信息: {str(e)}"}
            else:
                # 尝试从全局属性获取时间范围
                start_attr = ds.attrs.get('time_coverage_start', ds.attrs.get('geospatial_time_min', None))
                end_attr = ds.attrs.get('time_coverage_end', ds.attrs.get('geospatial_time_max', None))
                if start_attr and end_attr:
                    metadata['time_range'] = {'start': str(start_attr), 'end': str(end_attr)}
                else:
                    metadata['time_range'] = {'error': '数据集中未找到时间坐标或时间范围信息'}
            
            # 3. 空间范围
            lat_names = ['lat', 'latitude', 'LATITUDE', 'Latitude', 'lat_rho', 'nav_lat']
            lon_names = ['lon', 'longitude', 'LONGITUDE', 'Longitude', 'lon_rho', 'nav_lon']
            lat_coord, lon_coord = None, None
            
            for name in lat_names:
                if name in ds.coords:
                    lat_coord = ds.coords[name]
                    break
            
            for name in lon_names:
                if name in ds.coords:
                    lon_coord = ds.coords[name]
                    break
            
            if lat_coord is not None and lon_coord is not None and lat_coord.size > 0 and lon_coord.size > 0:
                metadata['spatial_range'] = {
                    'latitude': {
                        'min': float(lat_coord.min().values),
                        'max': float(lat_coord.max().values),
                        'units': lat_coord.attrs.get('units', 'degrees_north')
                    },
                    'longitude': {
                        'min': float(lon_coord.min().values),
                        'max': float(lon_coord.max().values),
                        'units': lon_coord.attrs.get('units', 'degrees_east')
                    }
                }
            else:
                # 尝试从全局属性获取空间范围
                min_lat = ds.attrs.get('geospatial_lat_min', ds.attrs.get('southernmost_latitude', None))
                max_lat = ds.attrs.get('geospatial_lat_max', ds.attrs.get('northernmost_latitude', None))
                min_lon = ds.attrs.get('geospatial_lon_min', ds.attrs.get('westernmost_longitude', None))
                max_lon = ds.attrs.get('geospatial_lon_max', ds.attrs.get('easternmost_longitude', None))
                
                if all([min_lat, max_lat, min_lon, max_lon]):
                    try:
                        metadata['spatial_range'] = {
                            'latitude': {
                                'min': float(min_lat),
                                'max': float(max_lat),
                                'units': 'degrees_north'
                            },
                            'longitude': {
                                'min': float(min_lon),
                                'max': float(max_lon),
                                'units': 'degrees_east'
                            }
                        }
                    except ValueError:
                        metadata['spatial_range'] = {'error': '无法转换全局空间属性'}
                else:
                    metadata['spatial_range'] = {'error': '数据集中未找到经纬度坐标或空间范围信息'}
            
            # 4. 变量信息
            variables_info = []
            for var_name, variable in ds.data_vars.items():
                var_info = {
                    'name': var_name,
                    'standard_name': variable.attrs.get('standard_name', ''),
                    'long_name': variable.attrs.get('long_name', var_name),
                    'units': variable.attrs.get('units', ''),
                    'dimensions': list(variable.dims),
                    'shape': [int(s) for s in variable.shape],
                    'attributes': dict(variable.attrs)
                }
                variables_info.append(var_info)
            metadata['variables'] = variables_info
            
            # 5. 数据生产者/机构信息
            source_info = {}
            creator_keys = ['creator_name', 'creator', 'institution', 'source', 'publisher_name', 'project']
            for key in creator_keys:
                if key in ds.attrs:
                    source_info[key.replace('_name', '').replace('publisher_', '')] = ds.attrs[key]
            
            if not source_info and 'Conventions' in ds.attrs:
                source_info['conventions'] = ds.attrs['Conventions']
                
            metadata['source_information'] = source_info if source_info else {'info': '未找到生产者/机构信息'}
            
            # 6. 创建/修改日期
            metadata['creation_date'] = ds.attrs.get('date_created', 
                                      ds.attrs.get('history_date', 
                                      ds.attrs.get('date_modified', None)))
            
            # 7. 全局属性
            metadata['global_attributes'] = dict(ds.attrs)
            
            # 8. 维度信息
            metadata['dimensions'] = {dim: int(size) for dim, size in ds.dims.items()}
            
            ds.close()
            return metadata
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in get_enhanced_metadata for {url}: {str(e)}")
            raise

    def subset(self, dataset_path: str, var_names: List[str], sel: Optional[Dict[str, Any]] = None) -> xr.Dataset:
        """
        提取指定变量和子集（如经纬度、时间范围）
        sel: 例如 {'time': slice('2024-01-01', '2024-01-31'), 'lat': slice(-10, 10)}
        """
        ds = self.open_dataset(dataset_path)
        ds_sel = ds[var_names]
        if sel:
            ds_sel = ds_sel.sel(**sel)
        return ds_sel
