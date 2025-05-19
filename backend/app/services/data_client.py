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
        ds = xr.open_dataset(url, engine="netcdf4")
        return ds

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
