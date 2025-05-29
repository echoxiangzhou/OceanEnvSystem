/**
 * CF-1.8规范检查页面
 * 提供NetCDF文件的CF规范验证和转换功能
 */

import React, { useState, useCallback } from 'react';
import { Upload, FileText, CheckCircle, AlertTriangle, XCircle, Download, Loader2 } from 'lucide-react';
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

interface ValidationResult {
  is_valid: boolean;
  cf_version?: string;
  critical_issues: number;
  warning_issues: number;
  info_issues: number;
  issues: ValidationIssue[];
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
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [conversionResult, setConversionResult] = useState<ConversionResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');
  const { toast } = useToast();

  // 文件选择处理
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // 检查文件格式
      const validExtensions = ['.nc', '.netcdf', '.nc4'];
      const isValidFormat = validExtensions.some(ext => 
        file.name.toLowerCase().endsWith(ext)
      );
      
      if (!isValidFormat) {
        toast({
          title: "文件格式错误",
          description: "请选择NetCDF格式文件（.nc, .netcdf, .nc4）",
          variant: "destructive"
        });
        return;
      }
      
      setSelectedFile(file);
      setValidationResult(null);
      setConversionResult(null);
      toast({
        title: "文件已选择",
        description: `已选择文件: ${file.name}`
      });
    }
  }, [toast]);

  // 拖拽处理
  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) {
      const fakeEvent = {
        target: { files: [file] }
      } as React.ChangeEvent<HTMLInputElement>;
      handleFileSelect(fakeEvent);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  }, []);

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

  // 转换文件
  const handleConvertFile = async () => {
    if (!selectedFile) {
      toast({
        title: "未选择文件",
        description: "请先选择要转换的NetCDF文件",
        variant: "destructive"
      });
      return;
    }

    setIsConverting(true);
    try {
      const result = await cfAPI.convertUploadedFile(selectedFile, true);
      setConversionResult(result);
      setActiveTab('conversion');
      
      if (result.success) {
        toast({
          title: "转换成功",
          description: "文件已成功转换为CF-1.8标准格式"
        });
      } else {
        toast({
          title: "转换失败",
          description: result.message,
          variant: "destructive"
        });
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

  // 下载转换后的文件
  const handleDownloadConverted = async () => {
    if (!conversionResult?.output_path) {
      toast({
        title: "无法下载",
        description: "没有可下载的转换结果",
        variant: "destructive"
      });
      return;
    }

    try {
      await cfAPI.downloadConvertedFile(conversionResult.output_path);
      toast({
        title: "下载开始",
        description: "转换后的文件下载已开始"
      });
    } catch (error) {
      toast({
        title: "下载失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      });
    }
  };

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
          <TabsTrigger value="conversion">转换结果</TabsTrigger>
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
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 transition-colors"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => document.getElementById('file-input')?.click()}
              >
                <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="text-lg mb-2">
                  {selectedFile ? selectedFile.name : '点击选择文件或拖拽文件到此处'}
                </p>
                <p className="text-sm text-gray-500">
                  支持格式：.nc, .netcdf, .nc4
                </p>
                <input
                  id="file-input"
                  type="file"
                  accept=".nc,.netcdf,.nc4"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
              
              {selectedFile && (
                <div className="mt-6 flex flex-col sm:flex-row gap-4">
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
                  
                  <Button
                    onClick={handleConvertFile}
                    disabled={isConverting}
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    {isConverting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <FileText className="w-4 h-4" />
                    )}
                    {isConverting ? '转换中...' : '转换文件'}
                  </Button>
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
                    <Alert>
                      <AlertDescription>
                        检测到CF版本: <strong>{validationResult.cf_version}</strong>
                      </AlertDescription>
                    </Alert>
                  )}
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
                                  {issue.level.toUpperCase()}
                                </Badge>
                                <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                                  {issue.code}
                                </code>
                              </div>
                              <p className="text-sm mb-2">{issue.message}</p>
                              <p className="text-xs text-gray-500 mb-2">
                                位置: {issue.location}
                              </p>
                              {issue.suggestion && (
                                <div className="bg-blue-50 border border-blue-200 rounded p-2">
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
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-600">请先上传并验证文件</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="conversion" className="space-y-6">
          {conversionResult ? (
            <>
              {/* 转换结果概览 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {conversionResult.success ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-500" />
                    )}
                    转换结果
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Alert variant={conversionResult.success ? "default" : "destructive"}>
                    <AlertDescription>
                      {conversionResult.message}
                    </AlertDescription>
                  </Alert>
                  
                  {conversionResult.success && conversionResult.output_path && (
                    <div className="mt-4">
                      <Button onClick={handleDownloadConverted} className="flex items-center gap-2">
                        <Download className="w-4 h-4" />
                        下载转换后的文件
                      </Button>
                    </div>
                  )}
                  
                  {conversionResult.backup_path && (
                    <p className="text-sm text-gray-600 mt-2">
                      原文件已备份至: {conversionResult.backup_path}
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* 已修复的问题 */}
              {conversionResult.issues_fixed.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-green-600">已修复的问题</CardTitle>
                    <CardDescription>
                      转换过程中自动修复的问题列表
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {conversionResult.issues_fixed.map((issue, index) => (
                        <div key={index} className="flex items-center gap-2 p-2 bg-green-50 rounded">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span className="text-sm">{issue.message}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 剩余问题 */}
              {conversionResult.remaining_issues.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-red-600">剩余问题</CardTitle>
                    <CardDescription>
                      仍需手动处理的问题
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {conversionResult.remaining_issues.map((issue, index) => (
                        <div key={index} className="flex items-center gap-2 p-2 bg-red-50 rounded">
                          <XCircle className="w-4 h-4 text-red-500" />
                          <span className="text-sm">{issue.message}</span>
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
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-600">请先上传并转换文件</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CFCompliancePage;
