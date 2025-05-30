import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '@/hooks/use-toast'
import './index.css'

// 导入布局组件
import AppLayout from './components/layout/AppLayout'

// 导入页面
import Dashboard from './pages/Dashboard/Dashboard' // 使用Dashboard.tsx
import DataBrowser from './pages/DataManagement/DataBrowser'
import DataImport from './pages/DataManagement/DataImport'
import OpenDAPBrowser from './pages/OpenDAP/OpenDAPBrowser'
import FusionConfig from './pages/DataFusion/FusionConfig'
import TaskCenter from './pages/TaskCenter/TaskCenter'
import TaskDetail from './pages/TaskCenter/TaskDetail'
// CF规范检查页面
import CFCompliancePage from './pages/CFCompliance/CFCompliancePage'
import CFMonitorPage from './pages/CFCompliance/CFMonitorPage'

// 创建查询客户端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5分钟
    },
  },
})

// 创建路由
const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout><Dashboard /></AppLayout>,
  },
  {
    path: "/dashboard",
    element: <AppLayout><Dashboard /></AppLayout>,
  },
  {
    path: "/data",
    element: <AppLayout><DataBrowser /></AppLayout>,
  },
  {
    path: "/data/import",
    element: <AppLayout><DataImport /></AppLayout>,
  },
  {
    path: "/data/import/upload",
    element: <AppLayout><DataImport /></AppLayout>,
  },
  {
    path: "/data/import/preview",
    element: <AppLayout><DataImport /></AppLayout>,
  },
  {
    path: "/data/import/metadata",
    element: <AppLayout><DataImport /></AppLayout>,
  },
  {
    path: "/data/import/validate",
    element: <AppLayout><DataImport /></AppLayout>,
  },
  {
    path: "/data/import/complete",
    element: <AppLayout><DataImport /></AppLayout>,
  },
  {
    path: "/data/cf-check",
    element: <AppLayout><CFCompliancePage /></AppLayout>,
  },
  {
    path: "/opendap",
    element: <AppLayout><OpenDAPBrowser /></AppLayout>,
  },
  {
    path: "/fusion/new",
    element: <AppLayout><FusionConfig /></AppLayout>,
  },
  {
    path: "/fusion/task",
    element: <AppLayout><TaskCenter /></AppLayout>,
  },
  {
    path: "/fusion/task/:taskId",
    element: <AppLayout><TaskDetail /></AppLayout>,
  },
  {
    path: "/cf-compliance",
    element: <AppLayout><CFCompliancePage /></AppLayout>,
  },
  {
    path: "/cf-compliance/monitor",
    element: <AppLayout><CFMonitorPage /></AppLayout>,
  },
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <RouterProvider router={router} />
      </ToastProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
