import React, { useState } from 'react';
import { Link } from 'react-router-dom';

// 导航项定义
const navItems = [
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
    label: '数据管理',
    path: '/data',
    subItems: [
      { label: '数据浏览', path: '/data' },
      { label: '数据导入', path: '/data/import' },
      { label: '规范检查与转换', path: '/data/cf-check' },
      { label: '规范监控管理', path: '/cf-compliance/monitor' }
    ]
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
    ),
    label: '数据融合',
    path: '/fusion',
    subItems: [
      { label: '创建融合任务', path: '/fusion/new' },
      { label: '历史融合任务', path: '/fusion/task' }
    ]
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    label: '诊断分析',
    path: '/diagnostics',
    subItems: [
      { label: '跃层诊断', path: '/diagnostics/thermocline' },
      { label: '中尺度涡诊断', path: '/diagnostics/eddy' },
      { label: '锋面诊断', path: '/diagnostics/front' }
    ]
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    label: '可视化',
    path: '/visualization',
    subItems: [
      { label: '地图可视化', path: '/visualization/map' },
      { label: '剖面可视化', path: '/visualization/profile' },
      { label: '时间序列', path: '/visualization/timeseries' }
    ]
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    label: '产品生成',
    path: '/products',
    subItems: [
      { label: '报告生成', path: '/products/reports' },
      { label: '图表导出', path: '/products/charts' }
    ]
  }
];

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({
    '数据管理': true, // 默认展开数据管理
    '数据融合': true  // 默认展开数据融合
  });

  const toggleItem = (label: string) => {
    setExpandedItems(prev => ({
      ...prev,
      [label]: !prev[label]
    }));
  };

  const handleItemClick = (item: typeof navItems[0]) => {
    if (item.subItems && item.subItems.length > 0) {
      toggleItem(item.label);
    } else {
      // 如果没有子菜单，直接导航
      window.location.href = item.path;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* 顶部导航栏 */}
      <header className="fixed top-0 left-0 right-0 bg-white shadow-sm h-14 z-10 px-4 flex items-center justify-between">
        <div className="flex items-center">
          <h1 className="text-lg font-medium text-blue-700">海洋环境数据融合与诊断系统</h1>
        </div>
        <div className="flex items-center space-x-4">
          <button className="p-2 text-gray-600 hover:text-gray-900">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
            </svg>
          </button>
          <button className="p-2 text-gray-600 hover:text-gray-900">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
          <button className="p-2 text-gray-600 hover:text-gray-900">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </button>
        </div>
      </header>

      {/* 侧边栏 */}
      <aside className="fixed left-0 top-14 bottom-0 w-60 bg-white border-r border-gray-200 overflow-y-auto">
        <nav className="py-4">
          <ul className="space-y-1">
            {navItems.map((item) => (
              <li key={item.label}>
                <div 
                  className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100 cursor-pointer"
                  onClick={() => handleItemClick(item)}
                >
                  <span className="mr-3">{item.icon}</span>
                  <span>{item.label}</span>
                  {item.subItems && item.subItems.length > 0 && (
                    <svg 
                      xmlns="http://www.w3.org/2000/svg" 
                      className={`ml-auto h-4 w-4 transition-transform ${expandedItems[item.label] ? 'rotate-180' : ''}`} 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  )}
                </div>
                {item.subItems && item.subItems.length > 0 && expandedItems[item.label] && (
                  <ul className="mt-1 ml-8 space-y-1">
                    {item.subItems.map((subItem) => (
                      <li key={subItem.label}>
                        <Link 
                          to={subItem.path}
                          className="block px-4 py-2 text-sm text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md"
                        >
                          {subItem.label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {/* 主内容区域 */}
      <main className="ml-60 mt-14 flex-1 overflow-auto p-6">
        {children}
      </main>
    </div>
  );
};

export default AppLayout;