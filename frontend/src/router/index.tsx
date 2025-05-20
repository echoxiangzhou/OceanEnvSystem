import { createBrowserRouter } from 'react-router-dom';
import MainLayout from '../components/layout/MainLayout';
import Dashboard from '../pages/Dashboard';
import DataBrowser from '../pages/DataManagement/DataBrowser';
import DataImport from '../pages/DataManagement/DataImport';
import OpenDAPBrowser from '../pages/OpenDAP/OpenDAPBrowser';
// 以下是未实现的页面，这里是为了路由结构完整性而导入
// 当您开发这些页面时可以取消注释
// import FusionConfig from '../pages/DataFusion/FusionConfig';
// import DiagnosticsPage from '../pages/Diagnostics/DiagnosticsPage';
// import ProductGenerator from '../pages/Products/ProductGenerator';
// import TaskCenter from '../pages/TaskCenter/TaskCenter';

// 定义路由配置
const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
      },
      {
        path: 'data',
        children: [
          {
            index: true,
            element: <DataBrowser />,
          },
          {
            path: 'import',
            element: <DataImport />,
          },
        ],
      },
      {
        path: 'opendap',
        element: <OpenDAPBrowser />,
      },
      // {
      //   path: 'fusion',
      //   children: [
      //     {
      //       index: true,
      //       element: <FusionConfig />,
      //     },
      //   ],
      // },
      // {
      //   path: 'diagnostics',
      //   children: [
      //     {
      //       index: true,
      //       element: <DiagnosticsPage />,
      //     },
      //   ],
      // },
      // {
      //   path: 'products',
      //   children: [
      //     {
      //       index: true,
      //       element: <ProductGenerator />,
      //     },
      //   ],
      // },
      // {
      //   path: 'tasks',
      //   element: <TaskCenter />,
      // },
    ],
  },
]);

export default router;