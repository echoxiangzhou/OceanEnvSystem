import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const Dashboard = () => {
  return (
    <div className="space-y-lg">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">工作台</h1>
        <p className="text-muted-foreground">欢迎使用海洋环境数据融合与诊断产品集成软件</p>
      </div>
      
      <div className="grid gap-md md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-sm">
            <CardTitle className="text-sm font-medium">数据集总数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">127</div>
            <p className="text-xs text-muted-foreground mt-1">
              较上月增加 12%
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-sm">
            <CardTitle className="text-sm font-medium">融合任务数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-muted-foreground mt-1">
              较上月增加 8%
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-sm">
            <CardTitle className="text-sm font-medium">诊断任务数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">36</div>
            <p className="text-xs text-muted-foreground mt-1">
              较上月增加 15%
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-sm">
            <CardTitle className="text-sm font-medium">生成产品数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">18</div>
            <p className="text-xs text-muted-foreground mt-1">
              较上月增加 5%
            </p>
          </CardContent>
        </Card>
      </div>
      
      <div className="grid gap-md md:grid-cols-2 lg:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>最近活动</CardTitle>
            <CardDescription>过去7天的系统活动记录</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-sm">
              <div className="flex items-center gap-sm border-b pb-sm">
                <div className="h-8 w-8 rounded-full bg-ocean flex items-center justify-center text-white">
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
                    className="h-4 w-4"
                  >
                    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">创建了新数据集 "南海浮标观测数据集2025-05"</p>
                  <p className="text-xs text-muted-foreground">5分钟前</p>
                </div>
              </div>
              
              <div className="flex items-center gap-sm border-b pb-sm">
                <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
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
                    className="h-4 w-4"
                  >
                    <circle cx="18" cy="18" r="3" />
                    <circle cx="6" cy="6" r="3" />
                    <path d="M13 6h3a2 2 0 0 1 2 2v7" />
                    <path d="M11 18H8a2 2 0 0 1-2-2V9" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">完成了数据融合任务 "卫星-浮标温度场融合"</p>
                  <p className="text-xs text-muted-foreground">2小时前</p>
                </div>
              </div>
              
              <div className="flex items-center gap-sm border-b pb-sm">
                <div className="h-8 w-8 rounded-full bg-green-500 flex items-center justify-center text-white">
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
                    className="h-4 w-4"
                  >
                    <path d="M3 3v18h18" />
                    <path d="m19 9-5 5-4-4-3 3" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">执行了中尺度涡诊断任务</p>
                  <p className="text-xs text-muted-foreground">昨天</p>
                </div>
              </div>
              
              <div className="flex items-center gap-sm">
                <div className="h-8 w-8 rounded-full bg-purple-500 flex items-center justify-center text-white">
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
                    className="h-4 w-4"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
                    <path d="M2 12h20" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">生成了南海水团分析报告</p>
                  <p className="text-xs text-muted-foreground">3天前</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>快速操作</CardTitle>
            <CardDescription>常用功能快速访问</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <a href="/data/upload" className="flex items-center gap-sm p-sm rounded-md hover:bg-accent hover:text-accent-foreground">
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
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" x2="12" y1="3" y2="15" />
                </svg>
                <span className="text-sm">上传数据</span>
              </a>
              <a href="/fusion/new" className="flex items-center gap-sm p-sm rounded-md hover:bg-accent hover:text-accent-foreground">
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
                <span className="text-sm">新建融合任务</span>
              </a>
              <a href="/diagnostics/thermocline" className="flex items-center gap-sm p-sm rounded-md hover:bg-accent hover:text-accent-foreground">
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
                <span className="text-sm">跃层诊断</span>
              </a>
              <a href="/visualization/map" className="flex items-center gap-sm p-sm rounded-md hover:bg-accent hover:text-accent-foreground">
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
                <span className="text-sm">地图可视化</span>
              </a>
              <a href="/products/reports" className="flex items-center gap-sm p-sm rounded-md hover:bg-accent hover:text-accent-foreground">
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
                <span className="text-sm">生成报告</span>
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;