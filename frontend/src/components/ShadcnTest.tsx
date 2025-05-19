import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const ShadcnTest: React.FC = () => {
  return (
    <div className="p-lg max-w-4xl mx-auto">
      <h1 className="mb-md">海洋环境数据系统</h1>
      
      <Tabs defaultValue="data" className="mb-lg">
        <TabsList>
          <TabsTrigger value="data">数据浏览</TabsTrigger>
          <TabsTrigger value="diagnostics">诊断工具</TabsTrigger>
          <TabsTrigger value="fusion">数据融合</TabsTrigger>
        </TabsList>
        
        <TabsContent value="data" className="mt-md">
          <Card>
            <CardHeader>
              <CardTitle>海洋数据浏览</CardTitle>
              <CardDescription>浏览和管理多源海洋环境数据集</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-md mb-md">
                <div className="space-y-sm">
                  <label htmlFor="search" className="text-secondary font-medium">搜索数据集</label>
                  <Input id="search" placeholder="输入关键词..." />
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button>浏览所有数据</Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        <TabsContent value="diagnostics" className="mt-md">
          <Card>
            <CardHeader>
              <CardTitle>海洋诊断工具</CardTitle>
              <CardDescription>利用专业算法分析海洋特征</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
                <Card>
                  <CardHeader className="pb-sm">
                    <CardTitle className="text-title-3">跃层诊断</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-secondary text-muted-foreground">
                      识别和分析海洋中的温跃层、盐跃层和密度跃层特征
                    </p>
                  </CardContent>
                  <CardFooter>
                    <Button variant="outline" size="sm">开始分析</Button>
                  </CardFooter>
                </Card>
                
                <Card>
                  <CardHeader className="pb-sm">
                    <CardTitle className="text-title-3">中尺度涡诊断</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-secondary text-muted-foreground">
                      识别和分析海洋中的中尺度涡旋特征
                    </p>
                  </CardContent>
                  <CardFooter>
                    <Button variant="outline" size="sm">开始分析</Button>
                  </CardFooter>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="fusion" className="mt-md">
          <Card>
            <CardHeader>
              <CardTitle>数据融合工具</CardTitle>
              <CardDescription>融合不同来源的海洋数据</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="mb-md text-secondary text-muted-foreground">
                使用先进的融合算法，将不同来源、不同尺度的海洋数据集成为统一的数据产品。
              </p>
              <Button variant="outline">创建融合任务</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ShadcnTest;