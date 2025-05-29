/**
 * CF-1.8规范检查页面
 * 提供NetCDF文件的CF规范验证和转换功能
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Upload, FileText, CheckCircle, AlertTriangle, XCircle, Download, Loader2, Save, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { cfAPI } from '@/services/cfAPI';

interface ValidationIssue {
  level: 'critical' | 'warning' | 'info';
  code: string;
  message: string;
  location: string;
  suggestion?: string;
}

interface FileValidationResult {
  is_valid: boolean;
  cf_version?: string;
  critical_issues: number;
  warning_issues: number;
  info_issues: number;
  issues: ValidationIssue[];
  file_path?: string;
  file_name?: string;
}

interface ConversionResult {
  success: boolean;
  message: string;
  output_path?: string;
  issues_fixed: ValidationIssue[];
  remaining_issues: ValidationIssue[];
  backup_path?: string;
}

const CFCompliancePage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [currentUploadedFilePath, setCurrentUploadedFilePath] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationResult, setValidationResult] = useState<FileValidationResult | null>(null);
  const [conversionResult, setConversionResult] = useState<ConversionResult | null>(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showExitDialog, setShowExitDialog] = useState(false);
  const [pendingNavigation, setPendingNavigation] = useState<string | null>(null);
  const { toast } = useToast();

  // 清理上传的文件
  const cleanupUploadedFile = useCallback(async (filePath: string) => {
    try {
      await cfAPI.deleteUploadFile(filePath);
      console.log(`已清理文件: ${filePath}`);
    } catch (error) {
      console.error('清理文件失败:', error);
    }
  }, []);

  // 组件卸载时清理未处理的文件
  useEffect(() => {
    return () => {
      if (currentUploadedFilePath && !conversionResult) {
        // 如果有上传的文件但没有处理完成，清理文件
        cleanupUploadedFile(currentUploadedFilePath);
      }
    };
  }, [currentUploadedFilePath, conversionResult, cleanupUploadedFile]);

  // 页面退出时的确认逻辑
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      // 如果有验证结果但还没有处理，提示用户
      if (validationResult && !conversionResult && !isSubmitting) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };

    const handlePopstate = (e: PopStateEvent) => {
      // 如果有验证结果但还没有处理，阻止导航并显示确认对话框
      if (validationResult && !conversionResult && !isSubmitting) {
        e.preventDefault();
        window.history.pushState(null, '', window.location.href);
        setShowExitDialog(true);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('popstate', handlePopstate);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('popstate', handlePopstate);
    };
  }, [validationResult, conversionResult, isSubmitting]);

  // 文件选择处理
  const handleFileSelect = useCallback(async (file: File) => {
    if (!cfAPI.isValidNetCDFFile(file)) {
      toast({
        title: "文件格式错误",
        description: "请选择NetCDF格式文件 (.nc, .netcdf, .nc4)",
        variant: "destructive"
      });
      return;
    }

    // 如果之前有上传的文件且还没有处理完成，先清理它
    if (currentUploadedFilePath && !conversionResult) {
      await cleanupUploadedFile(currentUploadedFilePath);
      toast({
        title: "文件已更新",
        description: "之前上传的文件已删除，准备处理新文件",
      });
    }

    setSelectedFile(file);
    setValidationResult(null);
    setConversionResult(null);
    setCurrentUploadedFilePath(null);
    setActiveTab('upload');
    setUploadProgress(0);
  }, [toast, currentUploadedFilePath, conversionResult, cleanupUploadedFile]);

  // 验证文件
  const handleValidateFile = async () => {
    if (!selectedFile) {
      toast({
        title: "未选择文件",
        description: "请先选择要验证的NetCDF文件",
        variant: "destructive"
      });
      return;
    }

    setIsValidating(true);
    try {
      const result = await cfAPI.validateUploadedFile(selectedFile);
      setValidationResult(result);
      
      // 保存上传后的文件路径
      if (result.file_path) {
        setCurrentUploadedFilePath(result.file_path);
      }
      
      setActiveTab('validation');
      
      if (result.is_valid) {
        toast({
          title: "验证通过",
          description: "文件符合CF-1.8规范标准"
        });
      } else {
        toast({
          title: "验证未通过",
          description: `发现 ${result.critical_issues} 个严重问题，${result.warning_issues} 个警告`,
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "验证失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      });
    } finally {
      setIsValidating(false);
    }
  };

  // 转换文件并提取元数据
  const handleConvertFile = async () => {
    if (!validationResult?.file_path) {
      toast({
        title: "文件路径错误",
        description: "无法获取文件路径",
        variant: "destructive"
      });
      return;
    }

    setIsConverting(true);
    try {
      const result = await cfAPI.convertFileAndExtractMetadata(validationResult.file_path);
      
      if (result.success) {
        setConversionResult({
          success: true,
          message: result.message,
          output_path: result.output_path,
          issues_fixed: [],
          remaining_issues: [],
          backup_path: undefined
        });
        setActiveTab('conversion');
        
        // 清空当前上传文件路径，因为文件已经被处理
        setCurrentUploadedFilePath(null);
        
        toast({
          title: "转换成功",
          description: "文件已转换为CF标准格式，元数据已保存到数据库"
        });
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      toast({
        title: "转换失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      });
    } finally {
      setIsConverting(false);
    }
  };

  // 提交数据（直接提取元数据）
  const handleSubmitData = async () => {
    if (!validationResult?.file_path) {
      toast({
        title: "文件路径错误",
        description: "无法获取文件路径",
        variant: "destructive"
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await cfAPI.extractMetadataOnly(validationResult.file_path);
      
      if (result.success) {
        setConversionResult({
          success: true,
          message: result.message,
          output_path: result.file_path,
          issues_fixed: [],
          remaining_issues: [],
          backup_path: undefined
        });
        setActiveTab('conversion');
        
        // 清空当前上传文件路径，因为文件已经被处理
        setCurrentUploadedFilePath(null);
        
        toast({
          title: "提交成功",
          description: "元数据已提取并保存到数据库"
        });
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      toast({
        title: "提交失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // 处理退出确认对话框
  const handleExitConfirm = async (confirmed: boolean) => {
    if (confirmed) {
      if (validationResult?.is_valid) {
        // 符合规范的文件，用户确认提交数据
        await handleSubmitData();
      } else {
        // 不符合规范的文件，用户确认转换
        await handleConvertFile();
      }
    } else {
      // 用户选择不处理，删除uploads文件
      if (validationResult?.file_path) {
        try {
          await cfAPI.deleteUploadFile(validationResult.file_path);
          toast({
            title: "文件已删除",
            description: "上传的文件已从服务器删除"
          });
        } catch (error) {
          console.error('删除文件失败:', error);
        }
      }
      // 重置状态
      setValidationResult(null);
      setConversionResult(null);
      setSelectedFile(null);
      setActiveTab('upload');
    }
    setShowExitDialog(false);
    setPendingNavigation(null);
  };

  // 拖拽处理
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  // 获取问题级别对应的图标和颜色
  const getIssueIcon = (level: string) => {
    switch (level) {
      case 'critical':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'info':
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
      default:
        return <FileText className="w-4 h-4 text-gray-500" />;
    }
  };

  const getIssueBadgeVariant = (level: string) => {
    switch (level) {
      case 'critical':
        return 'destructive';
      case 'warning':
        return 'secondary';
      case 'info':
        return 'outline';
      default:
        return 'default';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">CF-1.8规范检查与转换</h1>
        <p className="text-gray-600">
          检查NetCDF文件是否符合CF-1.8标准，并提供自动修复和转换功能
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="upload">文件上传</TabsTrigger>
          <TabsTrigger value="validation">验证结果</TabsTrigger>
          <TabsTrigger value="conversion">处理结果</TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-6">
          {/* 文件上传区域 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5" />
                文件上传
              </CardTitle>
              <CardDescription>
                选择或拖拽NetCDF文件进行CF规范检查
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  isDragOver 
                    ? 'border-blue-400 bg-blue-50' 
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <div className="mb-4">
                  <p className="text-lg font-medium text-gray-900 mb-2">
                    拖拽文件到此处，或点击选择文件
                  </p>
                  <p className="text-sm text-gray-500">
                    支持格式: .nc, .netcdf, .nc4
                  </p>
                </div>
                <input
                  type="file"
                  accept=".nc,.netcdf,.nc4"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleFileSelect(file);
                  }}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
                >
                  选择文件
                </label>
              </div>

              {selectedFile && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-gray-500" />
                      <div>
                        <p className="font-medium text-gray-900">{selectedFile.name}</p>
                        <p className="text-sm text-gray-500">
                          {cfAPI.formatFileSize(selectedFile.size)}
                        </p>
                      </div>
                    </div>
                    <Button 
                      onClick={handleValidateFile}
                      disabled={isValidating}
                      className="flex items-center gap-2"
                    >
                      {isValidating ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <CheckCircle className="w-4 h-4" />
                      )}
                      {isValidating ? '验证中...' : '验证文件'}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="validation" className="space-y-6">
          {validationResult ? (
            <>
              {/* 验证概览 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {validationResult.is_valid ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-500" />
                    )}
                    验证结果概览
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {validationResult.is_valid ? '✓' : '✗'}
                      </div>
                      <div className="text-sm text-gray-600">规范符合性</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">
                        {validationResult.critical_issues}
                      </div>
                      <div className="text-sm text-gray-600">严重问题</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-yellow-600">
                        {validationResult.warning_issues}
                      </div>
                      <div className="text-sm text-gray-600">警告问题</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {validationResult.info_issues}
                      </div>
                      <div className="text-sm text-gray-600">信息提示</div>
                    </div>
                  </div>
                  
                  {validationResult.cf_version && (
                    <Alert className="mb-4">
                      <AlertDescription>
                        检测到CF版本: <strong>{validationResult.cf_version}</strong>
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* 根据验证结果显示不同的操作按钮 */}
                  <div className="flex gap-4 justify-center">
                    {validationResult.is_valid ? (
                      <Button 
                        onClick={handleSubmitData}
                        disabled={isSubmitting}
                        className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
                        size="lg"
                      >
                        {isSubmitting ? (
                          <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                          <Save className="w-5 h-5" />
                        )}
                        {isSubmitting ? '提交中...' : '提交数据'}
                      </Button>
                    ) : (
                      <Button 
                        onClick={handleConvertFile}
                        disabled={isConverting}
                        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
                        size="lg"
                      >
                        {isConverting ? (
                          <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                          <RefreshCw className="w-5 h-5" />
                        )}
                        {isConverting ? '转换中...' : '转换文件'}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* 问题详情 */}
              {validationResult.issues.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>问题详情</CardTitle>
                    <CardDescription>
                      检测到的CF规范符合性问题列表
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {validationResult.issues.map((issue, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex items-start gap-3">
                            {getIssueIcon(issue.level)}
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <Badge variant={getIssueBadgeVariant(issue.level) as any}>
                                  {cfAPI.formatIssueLevel(issue.level)}
                                </Badge>
                                <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                                  {issue.code}
                                </code>
                              </div>
                              <p className="text-gray-900 mb-1">{issue.message}</p>
                              <p className="text-sm text-gray-600 mb-2">
                                位置: {issue.location}
                              </p>
                              {issue.suggestion && (
                                <div className="mt-2 p-3 bg-blue-50 rounded-md">
                                  <p className="text-sm text-blue-800">
                                    <strong>建议:</strong> {issue.suggestion}
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">请先上传文件进行验证</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="conversion" className="space-y-6">
          {conversionResult ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {conversionResult.success ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                  处理结果
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Alert className={conversionResult.success ? "" : "border-red-200 bg-red-50"}>
                  <AlertDescription>
                    {conversionResult.message}
                  </AlertDescription>
                </Alert>

                {conversionResult.success && conversionResult.output_path && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg">
                    <p className="text-green-800 font-medium mb-2">处理完成</p>
                    <p className="text-sm text-green-700">
                      文件已保存到: {conversionResult.output_path}
                    </p>
                    <p className="text-sm text-green-700">
                      元数据已成功提取并保存到数据库
                    </p>
                  </div>
                )}

                <div className="mt-4 flex gap-4">
                  <Button 
                    onClick={() => {
                      setSelectedFile(null);
                      setValidationResult(null);
                      setConversionResult(null);
                      setCurrentUploadedFilePath(null);
                      setActiveTab('upload');
                    }}
                    variant="outline"
                  >
                    处理新文件
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <RefreshCw className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">请先验证文件并进行处理</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* 退出确认对话框 */}
      <div
        className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center ${showExitDialog ? 'block' : 'hidden'}`}
        onClick={() => setShowExitDialog(false)}
      >
        <div
          className="bg-white p-8 rounded-lg shadow-lg max-w-md"
          onClick={(e) => e.stopPropagation()}
        >
          <h2 className="text-2xl font-bold mb-4">确认操作</h2>
          <p className="text-gray-700 mb-4">
            {validationResult?.is_valid 
              ? "文件已通过验证，是否提交数据到数据库？选择\"否\"将删除上传的文件。" 
              : "文件未通过验证，是否转换文件到CF标准格式？选择\"否\"将删除上传的文件。"
            }
          </p>
          <div className="flex gap-4 justify-center">
            <Button variant="outline" onClick={() => handleExitConfirm(false)}>
              否
            </Button>
            <Button onClick={() => handleExitConfirm(true)}>
              是
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CFCompliancePage;
