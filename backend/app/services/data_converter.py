import os
import pandas as pd
import xarray as xr
from seabird.cnv import fCNV

class DataConverter:
    """
    数据文件（csv, xlsx, cnv）转换为 CF-Conventions NetCDF 文件的服务
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def convert(self, file_path: str, file_type: str, output_filename: str = None) -> str:
        """
        统一入口：根据文件类型自动解析并转换为 NetCDF
        :param file_path: 输入文件路径
        :param file_type: 文件类型（csv, xlsx, cnv）
        :param output_filename: 输出 NetCDF 文件名（可选）
        :return: NetCDF 文件保存路径
        """
        if file_type == "csv":
            ds = self._from_csv(file_path)
        elif file_type == "xlsx":
            ds = self._from_xlsx(file_path)
        elif file_type == "cnv":
            ds = self._from_cnv(file_path)
        else:
            raise ValueError("Unsupported file type")

        if not output_filename:
            output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".nc"
        output_path = os.path.join(self.output_dir, output_filename)
        ds.to_netcdf(output_path)
        return output_path

    def _from_csv(self, file_path: str) -> xr.Dataset:
        df = pd.read_csv(file_path)
        ds = xr.Dataset.from_dataframe(df)
        # 可在此处补充变量属性、全局属性等
        return ds

    def _from_xlsx(self, file_path: str) -> xr.Dataset:
        df = pd.read_excel(file_path)
        ds = xr.Dataset.from_dataframe(df)
        return ds

    def _from_cnv(self, file_path: str) -> xr.Dataset:
        cnv = fCNV(file_path)
        data = {k: cnv[k] for k in cnv.keys()}
        ds = xr.Dataset({k: ("N", v) for k, v in data.items()})
        # 可根据 cnv.header、cnv.attrs 添加元数据
        return ds

# 示例用法
# converter = DataConverter("/path/to/thredds/data")
# nc_path = converter.convert("/path/to/data.csv", "csv")
# print("NetCDF 文件已保存：", nc_path)
