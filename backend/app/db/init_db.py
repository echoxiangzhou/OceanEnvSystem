"""
数据库初始化脚本
创建表结构并插入初始数据
"""

from sqlalchemy.orm import Session
from app.db.session import engine, Base
from app.db.models import DatasetTemplate, CFStandardName, UserPreference
import json
from datetime import datetime

def create_tables():
    """创建所有数据库表"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")

def init_cf_standard_names(db: Session):
    """初始化CF标准名称库"""
    print("正在初始化CF标准名称库...")
    
    # 常用的海洋学CF标准名称
    cf_standards = [
        {
            "standard_name": "sea_water_temperature",
            "canonical_units": "K",
            "description": "Sea water temperature is the in situ temperature of the sea water.",
            "category": "temperature",
            "aliases": ["temperature", "temp", "sst", "水温", "温度"]
        },
        {
            "standard_name": "sea_water_salinity", 
            "canonical_units": "1",
            "description": "Sea water salinity is the salt content of sea water, often on the Practical Salinity Scale of 1978.",
            "category": "salinity",
            "aliases": ["salinity", "sal", "pss", "盐度"]
        },
        {
            "standard_name": "depth",
            "canonical_units": "m",
            "description": "Depth is the vertical distance below the surface.",
            "category": "vertical",
            "aliases": ["depth", "z", "level", "深度", "水深"]
        },
        {
            "standard_name": "latitude",
            "canonical_units": "degrees_north",
            "description": "Latitude is positive northward; its units of degree_north (or equivalent) indicate this explicitly.",
            "category": "coordinate",
            "aliases": ["latitude", "lat", "纬度"]
        },
        {
            "standard_name": "longitude",
            "canonical_units": "degrees_east", 
            "description": "Longitude is positive eastward; its units of degree_east (or equivalent) indicate this explicitly.",
            "category": "coordinate",
            "aliases": ["longitude", "lon", "经度"]
        },
        {
            "standard_name": "time",
            "canonical_units": "seconds since 1970-01-01 00:00:00",
            "description": "Time is the independent variable.",
            "category": "coordinate",
            "aliases": ["time", "t", "date", "datetime", "时间"]
        },
        {
            "standard_name": "sea_water_pressure",
            "canonical_units": "Pa",
            "description": "Sea water pressure is the pressure that exists in the sea water medium.",
            "category": "pressure",
            "aliases": ["pressure", "press", "压力", "海压"]
        },
        {
            "standard_name": "sea_water_density",
            "canonical_units": "kg m-3",
            "description": "Sea water density is the mass per unit volume of sea water.",
            "category": "density",
            "aliases": ["density", "rho", "sigma", "密度"]
        },
        {
            "standard_name": "eastward_sea_water_velocity",
            "canonical_units": "m s-1",
            "description": "A velocity is a vector quantity. Eastward indicates a vector component which is positive when directed eastward (negative westward).",
            "category": "velocity",
            "aliases": ["u_velocity", "u", "eastward_velocity", "东向流速"]
        },
        {
            "standard_name": "northward_sea_water_velocity",
            "canonical_units": "m s-1", 
            "description": "A velocity is a vector quantity. Northward indicates a vector component which is positive when directed northward (negative southward).",
            "category": "velocity",
            "aliases": ["v_velocity", "v", "northward_velocity", "北向流速"]
        },
        {
            "standard_name": "upward_sea_water_velocity",
            "canonical_units": "m s-1",
            "description": "A velocity is a vector quantity. Upward indicates a vector component which is positive when directed upward (negative downward).",
            "category": "velocity", 
            "aliases": ["w_velocity", "w", "vertical_velocity", "垂向流速"]
        },
        {
            "standard_name": "sea_water_electrical_conductivity",
            "canonical_units": "S m-1",
            "description": "Electrical conductivity is the ability of a substance to conduct an electric current.",
            "category": "electrical",
            "aliases": ["conductivity", "cond", "电导率"]
        },
        {
            "standard_name": "sea_water_ph_reported_on_total_scale",
            "canonical_units": "1",
            "description": "Sea water pH is a measure of the acidity of sea water.",
            "category": "chemistry",
            "aliases": ["ph", "acidity", "酸度", "pH值"]
        },
        {
            "standard_name": "mass_concentration_of_oxygen_in_sea_water",
            "canonical_units": "kg m-3",
            "description": "Mass concentration means mass per unit volume and is used in the construction mass_concentration_of_X_in_Y.",
            "category": "chemistry",
            "aliases": ["oxygen", "o2", "dissolved_oxygen", "溶解氧"]
        },
        {
            "standard_name": "mass_concentration_of_chlorophyll_a_in_sea_water",
            "canonical_units": "mg m-3",
            "description": "Mass concentration of chlorophyll a in sea water.",
            "category": "biology",
            "aliases": ["chlorophyll", "chl", "chla", "叶绿素"]
        }
    ]
    
    for cf_data in cf_standards:
        # 检查是否已存在
        existing = db.query(CFStandardName).filter(
            CFStandardName.standard_name == cf_data["standard_name"]
        ).first()
        
        if not existing:
            cf_record = CFStandardName(
                standard_name=cf_data["standard_name"],
                canonical_units=cf_data["canonical_units"],
                description=cf_data["description"],
                category=cf_data["category"],
                aliases=cf_data["aliases"],
                cf_version="CF-1.8"
            )
            db.add(cf_record)
    
    db.commit()
    print(f"CF标准名称库初始化完成，共添加 {len(cf_standards)} 个标准名称")

def init_dataset_templates(db: Session):
    """初始化数据集模板"""
    print("正在初始化数据集模板...")
    
    # 海洋观测数据模板
    oceanographic_template = {
        "name": "海洋观测数据",
        "description": "适用于CTD、浮标、船舶观测等海洋现场观测数据",
        "category": "oceanographic",
        "file_types": ["csv", "excel"],
        "data_patterns": {
            "column_patterns": {
                "required": ["lat", "lon", "time", "depth"],
                "optional": ["temp", "sal", "press"]
            },
            "data_type_patterns": {
                "numeric": 3,
                "datetime": 1
            }
        },
        "global_attributes_template": {
            "title": "海洋观测数据",
            "institution": "海洋科学研究机构",
            "source": "现场观测",
            "keywords": "oceanography, temperature, salinity, CTD",
            "summary": "现场海洋观测数据，包含温度、盐度、压力等参数",
            "conventions": "CF-1.8"
        },
        "variable_mapping_rules": {
            "temperature_keywords": ["temp", "temperature", "sst", "水温"],
            "salinity_keywords": ["sal", "salinity", "pss", "盐度"],
            "pressure_keywords": ["press", "pressure", "压力"],
            "depth_keywords": ["depth", "z", "level", "深度"]
        },
        "coordinate_detection_rules": {
            "time_columns": ["time", "date", "datetime", "时间"],
            "latitude_columns": ["lat", "latitude", "纬度"],
            "longitude_columns": ["lon", "longitude", "经度"],
            "depth_columns": ["depth", "z", "level", "深度"]
        },
        "validation_rules": {
            "required_coordinates": ["time", "latitude", "longitude"],
            "temperature_range": [-5, 40],
            "salinity_range": [0, 50],
            "depth_range": [0, 11000]
        },
        "required_attributes": ["title", "institution", "source", "conventions"],
        "is_builtin": True
    }
    
    # 卫星遥感数据模板
    satellite_template = {
        "name": "卫星遥感数据",
        "description": "适用于卫星海表温度、叶绿素、海面高度等遥感数据",
        "category": "satellite",
        "file_types": ["netcdf", "csv"],
        "data_patterns": {
            "column_patterns": {
                "required": ["lat", "lon", "time"],
                "optional": ["sst", "chl", "ssh"]
            }
        },
        "global_attributes_template": {
            "title": "卫星遥感数据",
            "institution": "卫星数据处理中心", 
            "source": "satellite remote sensing",
            "keywords": "satellite, remote sensing, SST, chlorophyll",
            "summary": "卫星遥感海洋环境数据",
            "conventions": "CF-1.8"
        },
        "variable_mapping_rules": {
            "sst_keywords": ["sst", "sea_surface_temperature", "海表温度"],
            "chlorophyll_keywords": ["chl", "chlorophyll", "叶绿素"],
            "ssh_keywords": ["ssh", "sea_surface_height", "海面高度"]
        },
        "coordinate_detection_rules": {
            "time_columns": ["time", "date"],
            "latitude_columns": ["lat", "latitude"],
            "longitude_columns": ["lon", "longitude"]
        },
        "validation_rules": {
            "required_coordinates": ["time", "latitude", "longitude"],
            "sst_range": [-5, 40],
            "chlorophyll_range": [0, 100]
        },
        "required_attributes": ["title", "institution", "source", "conventions"],
        "is_builtin": True
    }
    
    # 数值模式数据模板
    model_template = {
        "name": "数值模式数据",
        "description": "适用于海洋数值模式输出、再分析数据等",
        "category": "model",
        "file_types": ["netcdf", "csv"],
        "data_patterns": {
            "column_patterns": {
                "required": ["lat", "lon", "time", "depth"],
                "optional": ["temp", "sal", "u", "v", "w"]
            }
        },
        "global_attributes_template": {
            "title": "海洋数值模式数据",
            "institution": "海洋数值预报中心",
            "source": "numerical ocean model",
            "keywords": "model, forecast, reanalysis, ocean circulation",
            "summary": "海洋数值模式输出数据",
            "conventions": "CF-1.8"
        },
        "variable_mapping_rules": {
            "temperature_keywords": ["temp", "temperature", "潜在温度"],
            "salinity_keywords": ["sal", "salinity", "盐度"],
            "u_velocity_keywords": ["u", "eastward_velocity", "东向流速"],
            "v_velocity_keywords": ["v", "northward_velocity", "北向流速"],
            "w_velocity_keywords": ["w", "upward_velocity", "垂向流速"]
        },
        "coordinate_detection_rules": {
            "time_columns": ["time", "forecast_time"],
            "latitude_columns": ["lat", "latitude"],
            "longitude_columns": ["lon", "longitude"],
            "depth_columns": ["depth", "level", "z"]
        },
        "validation_rules": {
            "required_coordinates": ["time", "latitude", "longitude"],
            "temperature_range": [-5, 40],
            "salinity_range": [0, 50],
            "velocity_range": [-5, 5]
        },
        "required_attributes": ["title", "institution", "source", "conventions"],
        "is_builtin": True
    }
    
    templates = [oceanographic_template, satellite_template, model_template]
    
    for template_data in templates:
        # 检查是否已存在
        existing = db.query(DatasetTemplate).filter(
            DatasetTemplate.name == template_data["name"]
        ).first()
        
        if not existing:
            template = DatasetTemplate(
                name=template_data["name"],
                description=template_data["description"],
                category=template_data["category"],
                file_types=template_data["file_types"],
                data_patterns=template_data["data_patterns"],
                global_attributes_template=template_data["global_attributes_template"],
                variable_mapping_rules=template_data["variable_mapping_rules"],
                coordinate_detection_rules=template_data["coordinate_detection_rules"],
                validation_rules=template_data["validation_rules"],
                required_attributes=template_data["required_attributes"],
                is_builtin=template_data["is_builtin"],
                created_by="system"
            )
            db.add(template)
    
    db.commit()
    print(f"数据集模板初始化完成，共添加 {len(templates)} 个模板")

def init_default_user_preferences(db: Session):
    """初始化默认用户偏好"""
    print("正在创建默认用户偏好模板...")
    
    # 系统默认用户偏好
    default_preferences = {
        "user_id": "default",
        "user_name": "系统默认配置",
        "default_global_attributes": {
            "institution": "海洋环境数据中心",
            "source": "数据导入系统",
            "conventions": "CF-1.8",
            "creator_institution": "海洋环境数据中心"
        },
        "preferred_file_encoding": "utf-8",
        "auto_detect_variables": True,
        "auto_apply_cf_standards": True,
        "default_institution": "海洋环境数据中心",
        "default_creator_name": "数据管理员",
        "validation_strictness": "standard",
        "auto_fix_issues": True,
        "interface_language": "zh",
        "timezone": "Asia/Shanghai"
    }
    
    # 检查是否已存在
    existing = db.query(UserPreference).filter(
        UserPreference.user_id == "default"
    ).first()
    
    if not existing:
        preference = UserPreference(**default_preferences)
        db.add(preference)
        db.commit()
        print("默认用户偏好创建完成")
    else:
        print("默认用户偏好已存在")

def init_database():
    """初始化整个数据库"""
    print("=== 开始数据库初始化 ===")
    
    # 创建表结构
    create_tables()
    
    # 获取数据库会话
    from app.db.session import SessionLocal
    db = SessionLocal()
    
    try:
        # 初始化CF标准名称
        init_cf_standard_names(db)
        
        # 初始化数据集模板
        init_dataset_templates(db)
        
        # 初始化默认用户偏好
        init_default_user_preferences(db)
        
        print("=== 数据库初始化完成 ===")
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database() 