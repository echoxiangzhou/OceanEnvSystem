import React from 'react';
import { cn } from '@/lib/utils';
import { Link, useLocation } from 'react-router-dom';

interface SidebarProps extends React.HTMLAttributes<HTMLElement> {
  isOpen: boolean;
}

type NavItem = {
  title: string;
  href: string;
  icon: JSX.Element;
  children?: NavItem[];
};

const navItems: NavItem[] = [
  {
    title: '数据管理',
    href: '/data',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-5 w-5"
      >
        <path d="M20 6v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2Z" />
        <path d="M8 2v4" />
        <path d="M16 2v4" />
        <path d="M2 10h20" />
      </svg>
    ),
    children: [
      {
        title: '数据浏览',
        href: '/data',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      },
      {
        title: '数据导入',
        href: '/data/import',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      }
    ]
  },
  {
    title: '数据融合',
    href: '/fusion',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-5 w-5"
      >
        <circle cx="18" cy="18" r="3" />
        <circle cx="6" cy="6" r="3" />
        <path d="M13 6h3a2 2 0 0 1 2 2v7" />
        <path d="M11 18H8a2 2 0 0 1-2-2V9" />
      </svg>
    ),
    children: [
      {
        title: '新建融合任务',
        href: '/fusion/new',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      },
      {
        title: '融合任务列表',
        href: '/fusion/tasks',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      }
    ]
  },
  {
    title: '诊断分析',
    href: '/diagnostics',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-5 w-5"
      >
        <path d="M3 3v18h18" />
        <path d="m19 9-5 5-4-4-3 3" />
      </svg>
    ),
    children: [
      {
        title: '跃层诊断',
        href: '/diagnostics/thermocline',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      },
      {
        title: '中尺度涡诊断',
        href: '/diagnostics/eddy',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      },
      {
        title: '锋面诊断',
        href: '/diagnostics/front',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      },
      {
        title: '诊断任务列表',
        href: '/diagnostics/tasks',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      }
    ]
  },
  {
    title: '可视化',
    href: '/visualization',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-5 w-5"
      >
        <circle cx="12" cy="12" r="10" />
        <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
        <path d="M2 12h20" />
      </svg>
    ),
    children: [
      {
        title: '地图可视化',
        href: '/visualization/map',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      },
      {
        title: '剖面可视化',
        href: '/visualization/profile',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      },
      {
        title: '时间序列',
        href: '/visualization/timeseries',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      },
      {
        title: '断面可视化',
        href: '/visualization/section',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      },
      {
        title: '三维可视化',
        href: '/visualization/3d',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      }
    ]
  },
  {
    title: '产品生成',
    href: '/products',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-5 w-5"
      >
        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
    ),
    children: [
      {
        title: '报告管理',
        href: '/products/reports',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      },
      {
        title: '图表管理',
        href: '/products/charts',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      },
      {
        title: '导出设置',
        href: '/products/export',
        icon: <span className="h-1.5 w-1.5 rounded-full bg-current" />,
      }
    ]
  }
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen, className, ...props }) => {
  const location = useLocation();
  const [openItems, setOpenItems] = React.useState<Record<string, boolean>>({});

  // 初始化时，根据当前路径决定哪个菜单项应该展开
  React.useEffect(() => {
    const newOpenItems: Record<string, boolean> = {};
    navItems.forEach(item => {
      if (item.children) {
        const shouldBeOpen = item.children.some(child => 
          location.pathname === child.href || location.pathname.startsWith(child.href + '/'));
        if (shouldBeOpen) {
          newOpenItems[item.title] = true;
        }
      }
    });
    setOpenItems(newOpenItems);
  }, [location.pathname]);

  const toggleItem = (title: string) => {
    setOpenItems(prev => ({
      ...prev,
      [title]: !prev[title]
    }));
  };

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-20 w-64 border-r bg-background transition-transform duration-300 ease-in-out",
        isOpen ? "translate-x-0" : "-translate-x-full",
        "md:translate-x-0",
        className
      )}
      {...props}
    >
      <div className="h-14 border-b px-md flex items-center">
        <span className="font-bold text-lg text-ocean">海洋环境数据系统</span>
      </div>
      <nav className="flex flex-col gap-1 p-md pt-md overflow-y-auto h-[calc(100vh-3.5rem)]">
        {navItems.map((item) => (
          <div key={item.title} className="flex flex-col">
            <button
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 hover:bg-accent hover:text-accent-foreground",
                item.children && openItems[item.title] ? "bg-accent/50" : ""
              )}
              onClick={() => item.children && toggleItem(item.title)}
            >
              {item.icon}
              <span className="flex-1 text-sm font-medium">{item.title}</span>
              {item.children && (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className={cn(
                    "h-4 w-4 transition-transform",
                    openItems[item.title] ? "rotate-180" : ""
                  )}
                >
                  <path d="m6 9 6 6 6-6" />
                </svg>
              )}
            </button>
            {item.children && openItems[item.title] && (
              <div className="ml-6 mt-1 flex flex-col gap-1">
                {item.children.map((child) => (
                  <Link
                    key={child.title}
                    to={child.href}
                    className={cn(
                      "flex items-center gap-3 rounded-md px-3 py-2 hover:bg-accent hover:text-accent-foreground",
                      location.pathname === child.href || location.pathname.startsWith(child.href + '/') 
                        ? "bg-accent text-accent-foreground" 
                        : "text-muted-foreground"
                    )}
                  >
                    {child.icon}
                    <span className="text-sm">{child.title}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;