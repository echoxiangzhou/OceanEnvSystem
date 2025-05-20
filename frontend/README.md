# 多源多尺度海洋环境数据融合与诊断产品集成软件 - 前端

这是多源多尺度海洋环境数据融合与诊断产品集成软件的前端项目。

## 技术栈

- React 18
- TypeScript
- Tailwind CSS
- React Router
- React Query

## 开发环境设置

### 前提条件

- Node.js 18+ 
- npm 9+

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

应用将在 [http://localhost:3000](http://localhost:3000) 运行。

### 构建生产版本

```bash
npm run build
```

### 启动构建预览

```bash
npm run preview
```

## 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── components/      # 可复用组件
│   │   ├── common/      # 通用组件
│   │   ├── data/        # 数据相关组件
│   │   ├── layout/      # 布局组件
│   │   └── opendap/     # OPeNDAP相关组件
│   ├── hooks/           # 自定义React钩子
│   ├── mocks/           # 模拟数据
│   ├── pages/           # 页面组件
│   ├── services/        # API服务
│   ├── types/           # TypeScript类型定义
│   ├── utils/           # 工具函数
│   ├── App.tsx          # 应用入口组件
│   ├── main.tsx         # 应用入口文件
│   └── index.css        # 全局样式
├── .env                 # 环境变量
├── index.html           # HTML模板
├── package.json         # 项目配置
├── postcss.config.js    # PostCSS配置
├── tailwind.config.js   # Tailwind CSS配置
├── tsconfig.json        # TypeScript配置
└── vite.config.ts       # Vite配置
```

## 模拟数据

在开发阶段，前端使用模拟数据。要切换到真实API，请编辑`src/services/dataService.ts`，将`USE_MOCK_DATA`设置为`false`。
