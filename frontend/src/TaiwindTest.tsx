import React from 'react';

const TailwindTest: React.FC = () => {
  return (
    <div className="p-lg">
      <h1 className="mb-md">海洋环境数据系统</h1>
      
      <div className="ocean-card mb-md">
        <h2 className="mb-sm">数据浏览</h2>
        <p className="text-secondary text-gray-600">
          使用左侧导航浏览可用的海洋数据集和诊断工具。
        </p>
        <button className="btn btn-primary mt-sm">
          浏览数据
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
        <div className="profile-viewer">
          <h3 className="mb-sm">温度垂直剖面</h3>
          <div className="h-64 bg-gray-100 flex items-center justify-center">
            剖面图示例
          </div>
        </div>
        
        <div className="thermocline-visualizer">
          <h3 className="mb-sm">跃层诊断</h3>
          <div className="h-64 bg-gray-100 flex items-center justify-center">
            跃层诊断示例
          </div>
        </div>
      </div>
    </div>
  );
};

export default TailwindTest;