/**
 * CF规范监控管理页面
 * 管理CF规范监控服务，查看文件处理结果
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Play, 
  Square, 
  RefreshCw, 
  Folder, 
  FileText, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Eye,
  Download,
  Clock,
  Server
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { cfAPI, MonitorStatus, ProcessingResult, DirectoryStructure, FileInfo } from '@/services/cfAPI';

const CFMonitorPage: React.FC = () => {
  const [monitorStatus, setMonitorStatus] = useState<MonitorStatus | null>(null);
  const [processingResults, setProcessingResults] = useState<ProcessingResult[]>([]);
  const [directoryStructure, setDirectoryStructure] = useState<DirectoryStructure | null>(null);
  const [dataDir, setDataDir] = useState('/Users/echo/codeProjects/OceanEnvSystem/OceanEnvSystem/backend/docker/thredds/data/oceanenv');
  const [recursiveScan, setRecursiveScan] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [pollingEnabled, setPollingEnabled] = useState(false);
  const { toast } = useToast();

  // 获取监控状态
  const fetchMonitorStatus = useCallback(async () => {
    try {
      const status = await cfAPI.getMonitorStatus();
      setMonitorStatus(status);
    } catch (error) {
      console.error('获取监控状态失败:', error);
    }
  }, []);

  // 获取处理结果
  const fetchProcessingResults = useCallback(async () => {
    try {
      const data = await cfAPI.getProcessingResults(100);
      setProcessingResults(data.results);
    } catch (error) {
      console.error('获取处理结果失败:', error);
    }
  }, []);

  // 获取目录结构
  const fetchDirectoryStructure = useCallback(async () => {
    try {
      const structure = await cfAPI.getDirectoryStructure(dataDir);
      setDirectoryStructure(structure);
    } catch (error) {
      console.error('获取目录结构失败:', error);
    }
  }, [dataDir]);

  // 启动监控服务
  const handleStartMonitor = async () => {
    setIsLoading(true);
    try {
      await cfAPI.startMonitor(dataDir);
      await fetchMonitorStatus();
      toast({
        title: "监控服务已启动",
        description: `正在监控目录: ${dataDir}${recursiveScan ? ' (包含所有子目录)' : ''}`
      });
    } catch (error) {
      toast({
        title: "启动失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 停止监控服务
  const handleStopMonitor = async () => {
    setIsLoading(true);
    try {
      await cfAPI.stopMonitor();
      await fetchMonitorStatus();
      toast({
        title: "监控服务已停止",
        description: "CF规范监控服务已停止运行"
      });
    } catch (error) {
      toast({
        title: "停止失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 扫描目录
  const handleScanDirectory = async () => {
    setIsLoading(true);
    try {
      await cfAPI.scanDirectory();
      toast({
        title: "目录扫描已启动",
        description: "正在后台扫描并处理NetCDF文件"
      });
      // 稍后刷新结果
      setTimeout(fetchProcessingResults, 2000);
    } catch (error) {
      toast({
        title: "扫描失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 手动处理文件
  const handleProcessFile = async (filePath: string) => {
    try {
      const result = await cfAPI.processFileManually(filePath);
      toast({
        title: "文件处理完成",
        description: `文件 ${filePath} 处理状态: ${result.status}`
      });
      fetchProcessingResults();
    } catch (error) {
      toast({
        title: "处理失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      });
    }
  };

  // 获取状态对应的图标和颜色
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'valid':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'converted':
        return <RefreshCw className="w-4 h-4 text-blue-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <FileText className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'valid':
        return <Badge variant="outline" className="text-green-600 border-green-600">符合标准</Badge>;
      case 'converted':
        return <Badge variant="outline" className="text-blue-600 border-blue-600">已转换</Badge>;
      case 'failed':
        return <Badge variant="destructive">转换失败</Badge>;
      case 'error':
        return <Badge variant="secondary">处理错误</Badge>;
      default:
        return <Badge variant="outline">未知状态</Badge>;
    }
  };

  // 格式化时间
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('zh-CN');
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  // 组件挂载时获取初始数据
  useEffect(() => {
    fetchMonitorStatus();
    fetchProcessingResults();
    fetchDirectoryStructure();
  }, [fetchMonitorStatus, fetchProcessingResults, fetchDirectoryStructure]);

  // 启用轮询时的效果
  useEffect(() => {
    let cleanup: (() => void) | undefined;

    if (pollingEnabled && monitorStatus?.status === 'running') {
      cleanup = cfAPI.startPollingResults(
        (results) => setProcessingResults(results),
        3000, // 3秒轮询一次
        100
      );
    }

    return () => {
      if (cleanup) cleanup();
    };
  }, [pollingEnabled, monitorStatus?.status]);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">CF规范监控管理</h1>
        <p className="text-gray-600">
          管理CF-1.8规范监控服务，监控数据目录中的NetCDF文件并自动处理
        </p>
      </div>

      <div className="space-y-6">
        {/* 监控服务状态 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="w-5 h-5" />
              监控服务状态
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="space-y-3">
                <div>
                  <Label htmlFor="data-dir">监控目录</Label>
                  <Input
                    id="data-dir"
                    value={dataDir}
                    onChange={(e) => setDataDir(e.target.value)}
                    disabled={monitorStatus?.status === 'running'}
                    className="mt-1"
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="recursive-scan"
                    checked={recursiveScan}
                    onChange={(e) => setRecursiveScan(e.target.checked)}
                    disabled={monitorStatus?.status === 'running'}
                    className="rounded border-gray-300"
                  />
                  <Label htmlFor="recursive-scan" className="text-sm">
                    扫描所有子目录
                  </Label>
                </div>
              </div>
              <div className="flex items-end">
                <div className="space-y-2">
                  <Label>服务状态</Label>
                  <div className="flex items-center gap-2">
                    {monitorStatus?.status === 'running' ? (
                      <Badge variant="outline" className="text-green-600 border-green-600">
                        运行中
                      </Badge>
                    ) : (
                      <Badge variant="secondary">已停止</Badge>
                    )}
                    {monitorStatus?.processing_results_count !== undefined && (
                      <span className="text-sm text-gray-600">
                        {monitorStatus.processing_results_count} 个处理结果
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-end gap-2">
                {monitorStatus?.status === 'running' ? (
                  <Button
                    onClick={handleStopMonitor}
                    disabled={isLoading}
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    <Square className="w-4 h-4" />
                    停止监控
                  </Button>
                ) : (
                  <Button
                    onClick={handleStartMonitor}
                    disabled={isLoading}
                    className="flex items-center gap-2"
                  >
                    <Play className="w-4 h-4" />
                    启动监控
                  </Button>
                )}
                <Button
                  onClick={handleScanDirectory}
                  disabled={isLoading || monitorStatus?.status !== 'running'}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  扫描目录
                </Button>
              </div>
            </div>

            {monitorStatus?.message && (
              <Alert>
                <AlertDescription>{monitorStatus.message}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        <Tabs defaultValue="results" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="results">处理结果</TabsTrigger>
            <TabsTrigger value="directory">目录结构</TabsTrigger>
          </TabsList>

          <TabsContent value="results" className="space-y-6">
            {/* 处理结果控制 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Clock className="w-5 h-5" />
                    处理结果 ({processingResults.length})
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      onClick={fetchProcessingResults}
                      variant="outline"
                      size="sm"
                      className="flex items-center gap-2"
                    >
                      <RefreshCw className="w-4 h-4" />
                      刷新
                    </Button>
                    <Button
                      onClick={() => setPollingEnabled(!pollingEnabled)}
                      variant={pollingEnabled ? "default" : "outline"}
                      size="sm"
                      className="flex items-center gap-2"
                    >
                      <Eye className="w-4 h-4" />
                      {pollingEnabled ? '停止实时' : '实时监控'}
                    </Button>
                  </div>
                </CardTitle>
                <CardDescription>
                  查看最近处理的NetCDF文件及其CF规范检查结果
                </CardDescription>
              </CardHeader>
              <CardContent>
                {processingResults.length > 0 ? (
                  <div className="space-y-4">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>文件</TableHead>
                          <TableHead>状态</TableHead>
                          <TableHead>CF版本</TableHead>
                          <TableHead>问题统计</TableHead>
                          <TableHead>处理时间</TableHead>
                          <TableHead>操作</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {processingResults.map((result, index) => (
                          <TableRow key={index}>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <FileText className="w-4 h-4 text-gray-500" />
                                <div>
                                  <div className="font-medium">{result.relative_path}</div>
                                  <div className="text-sm text-gray-500">{result.file_path}</div>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                {getStatusIcon(result.status)}
                                {getStatusBadge(result.status)}
                              </div>
                            </TableCell>
                            <TableCell>
                              {result.validation_result.cf_version || '未检测'}
                            </TableCell>
                            <TableCell>
                              <div className="space-y-1">
                                {result.validation_result.critical_issues > 0 && (
                                  <Badge variant="destructive" className="text-xs">
                                    严重: {result.validation_result.critical_issues}
                                  </Badge>
                                )}
                                {result.validation_result.warning_issues > 0 && (
                                  <Badge variant="secondary" className="text-xs">
                                    警告: {result.validation_result.warning_issues}
                                  </Badge>
                                )}
                                {result.validation_result.info_issues > 0 && (
                                  <Badge variant="outline" className="text-xs">
                                    信息: {result.validation_result.info_issues}
                                  </Badge>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className="text-sm">
                              {formatTimestamp(result.timestamp)}
                            </TableCell>
                            <TableCell>
                              <Button
                                onClick={() => handleProcessFile(result.file_path)}
                                size="sm"
                                variant="outline"
                                className="text-xs"
                              >
                                重新处理
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Clock className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-600">暂无处理结果</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="directory" className="space-y-6">
            {/* 目录结构 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Folder className="w-5 h-5" />
                    目录结构
                  </span>
                  <Button
                    onClick={fetchDirectoryStructure}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    刷新
                  </Button>
                </CardTitle>
                <CardDescription>
                  查看数据目录的分层结构（raw/processing/standard）
                </CardDescription>
              </CardHeader>
              <CardContent>
                {directoryStructure ? (
                  <Tabs defaultValue="standard" className="space-y-4">
                    <TabsList>
                      <TabsTrigger value="standard">
                        标准文件 ({directoryStructure.standard.length})
                      </TabsTrigger>
                      <TabsTrigger value="raw">
                        原始文件 ({directoryStructure.raw.length})
                      </TabsTrigger>
                      <TabsTrigger value="processing">
                        处理中 ({directoryStructure.processing.length})
                      </TabsTrigger>
                    </TabsList>

                    {Object.entries(directoryStructure).map(([category, files]) => (
                      <TabsContent key={category} value={category}>
                        {files.length > 0 ? (
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>文件名</TableHead>
                                <TableHead>路径</TableHead>
                                <TableHead>大小</TableHead>
                                <TableHead>修改时间</TableHead>
                                <TableHead>操作</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {files.map((file: FileInfo, index: number) => (
                                <TableRow key={index}>
                                  <TableCell>
                                    <div className="flex items-center gap-2">
                                      <FileText className="w-4 h-4 text-gray-500" />
                                      {file.name}
                                    </div>
                                  </TableCell>
                                  <TableCell className="text-sm text-gray-600">
                                    {file.path}
                                  </TableCell>
                                  <TableCell className="text-sm">
                                    {formatFileSize(file.size)}
                                  </TableCell>
                                  <TableCell className="text-sm">
                                    {new Date(file.modified * 1000).toLocaleString('zh-CN')}
                                  </TableCell>
                                  <TableCell>
                                    <div className="flex items-center gap-2">
                                      <Button
                                        onClick={() => handleProcessFile(file.full_path)}
                                        size="sm"
                                        variant="outline"
                                        className="text-xs"
                                      >
                                        处理
                                      </Button>
                                      {category === 'standard' && (
                                        <Button
                                          onClick={() => cfAPI.downloadConvertedFile(file.full_path)}
                                          size="sm"
                                          variant="outline"
                                          className="text-xs flex items-center gap-1"
                                        >
                                          <Download className="w-3 h-3" />
                                          下载
                                        </Button>
                                      )}
                                    </div>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        ) : (
                          <div className="text-center py-8">
                            <Folder className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                            <p className="text-gray-600">该目录中暂无文件</p>
                          </div>
                        )}
                      </TabsContent>
                    ))}
                  </Tabs>
                ) : (
                  <div className="text-center py-8">
                    <Folder className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-600">请先配置并启动监控服务</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default CFMonitorPage;
