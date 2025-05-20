import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'

// 导入布局组件
import AppLayout from './components/layout/AppLayout'

// 导入页面
import Dashboard from './pages/Dashboard/Dashboard'
import DataBrowser from './pages/DataManagement/DataBrowser'
import DataImport from './pages/DataManagement/DataImport'
import OpenDAPBrowser from './pages/OpenDAP/OpenDAPBrowser'

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
    path: "/opendap",
    element: <AppLayout><OpenDAPBrowser /></AppLayout>,
  },
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
)
