import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const LayoutExample: React.FC = () => {
  return (
    <div className="space-y-lg">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">布局演示</h1>
          <p className="text-muted-foreground">这个页面展示了系统的基本布局组件</p>
        </div>
        <Button>操作按钮</Button>
      </div>
      
      <div className="grid gap-md md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Navbar 导航栏</CardTitle>
            <CardDescription>页面顶部的导航栏</CardDescription>
          </CardHeader>
          <CardContent>
            <p>
              Navbar 组件位于页面顶部，提供系统标题、菜单控制和用户操作。它在小屏幕上会隐藏部分内容，并提供折叠侧边栏的功能。
            </p>
            <div className="mt-md p-md bg-accent rounded-md">
              <code>{'<Navbar isSidebarOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />'}</code>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Sidebar 侧边栏</CardTitle>
            <CardDescription>页面左侧的导航菜单</CardDescription>
          </CardHeader>
          <CardContent>
            <p>
              Sidebar 组件提供系统的主要导航功能，包含分层级的菜单结构。它在小屏幕上可以折叠，并支持子菜单的展开和收起。
            </p>
            <div className="mt-md p-md bg-accent rounded-md">
              <code>{'<Sidebar isOpen={isSidebarOpen} />'}</code>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>MainContent 主内容区</CardTitle>
            <CardDescription>页面的主要内容区域</CardDescription>
          </CardHeader>
          <CardContent>
            <p>
              MainContent 组件是页面的主要内容展示区域，它会根据侧边栏的状态自动调整边距，确保内容始终可见且布局合理。
            </p>
            <div className="mt-md p-md bg-accent rounded-md">
              <code>{'<MainContent isSidebarOpen={isSidebarOpen}>...</MainContent>'}</code>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Layout 布局组合</CardTitle>
            <CardDescription>将所有布局组件组合在一起</CardDescription>
          </CardHeader>
          <CardContent>
            <p>
              Layout 组件将 Navbar、Sidebar 和 MainContent 组件组合在一起，管理它们的状态，提供完整的页面布局框架。
            </p>
            <div className="mt-md p-md bg-accent rounded-md">
              <code>{'<Layout>...</Layout>'}</code>
            </div>
          </CardContent>
        </Card>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>响应式设计</CardTitle>
          <CardDescription>布局在不同屏幕尺寸下的表现</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-md">
            <p>
              布局组件采用响应式设计，在不同屏幕尺寸下有不同的表现：
            </p>
            <ul className="list-disc pl-lg space-y-sm">
              <li>
                <strong>大屏幕 (1024px以上)：</strong> 侧边栏始终可见，主内容区域适当调整边距。
              </li>
              <li>
                <strong>中等屏幕 (768px-1024px)：</strong> 侧边栏可以折叠，导航栏显示部分内容。
              </li>
              <li>
                <strong>小屏幕 (768px以下)：</strong> 侧边栏默认折叠，导航栏简化显示，需通过菜单按钮展开侧边栏。
              </li>
            </ul>
            <p>
              布局组件会根据屏幕尺寸自动调整内容的排列方式，确保在各种设备上都能提供良好的用户体验。
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LayoutExample;