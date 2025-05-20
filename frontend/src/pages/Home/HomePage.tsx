import React from 'react';
import { Link } from 'react-router-dom';

const HomePage: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-6">
          多源多尺度海洋环境数据融合与诊断产品集成软件
        </h1>
        <p className="max-w-2xl mx-auto text-gray-600 dark:text-gray-300 mb-8">
          一套专为海洋科研人员、环境监测机构及海洋相关行业设计的专业数据处理平台
        </p>
      </div>

      <div className="mt-12 grid gap-8 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {/* 数据浏览卡片 */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
          <div className="bg-blue-600 h-2"></div>
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">数据浏览</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">浏览和管理多源海洋数据集，支持筛选、搜索和下载功能。</p>
            <Link 
              to="/data" 
              className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
            >
              前往数据浏览
              <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
              </svg>
            </Link>
          </div>
        </div>

        {/* 数据导入卡片 */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
          <div className="bg-teal-600 h-2"></div>
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">数据导入</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">上传和转换海洋数据文件，支持CSV、Excel和CNV等格式。</p>
            <Link 
              to="/data/import" 
              className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
            >
              前往数据导入
              <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
              </svg>
            </Link>
          </div>
        </div>

        {/* OPeNDAP浏览卡片 */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
          <div className="bg-green-600 h-2"></div>
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">OPeNDAP浏览</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">浏览远程OPeNDAP数据源，查看数据集元信息和结构。</p>
            <Link 
              to="/opendap" 
              className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
            >
              前往OPeNDAP浏览
              <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
              </svg>
            </Link>
          </div>
        </div>

        {/* 数据融合卡片 */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
          <div className="bg-purple-600 h-2"></div>
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">数据融合</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">使用最优插值、卡尔曼滤波等算法融合不同来源的海洋数据。</p>
            <Link 
              to="/fusion" 
              className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
            >
              前往数据融合
              <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
              </svg>
            </Link>
          </div>
        </div>

        {/* 诊断分析卡片 */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
          <div className="bg-red-600 h-2"></div>
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">诊断分析</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">进行跃层、中尺度涡、锋面等海洋环境特征的诊断分析。</p>
            <Link 
              to="/diagnostics" 
              className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
            >
              前往诊断分析
              <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
              </svg>
            </Link>
          </div>
        </div>

        {/* 可视化卡片 */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
          <div className="bg-amber-600 h-2"></div>
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">数据可视化</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">多种方式可视化展示海洋数据，包括地图、剖面、时间序列等。</p>
            <Link 
              to="/visualization" 
              className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
            >
              前往数据可视化
              <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
              </svg>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;