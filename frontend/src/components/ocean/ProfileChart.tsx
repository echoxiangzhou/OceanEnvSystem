import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ProfileChartProps {
  title: string;
  children?: React.ReactNode;
}

const ProfileChart: React.FC<ProfileChartProps> = ({ title, children }) => {
  return (
    <Card className="h-full">
      <CardHeader className="pb-sm">
        <CardTitle className="text-title-3">{title}</CardTitle>
      </CardHeader>
      <CardContent className="h-[400px] flex items-center justify-center bg-muted rounded-md">
        {children || <p className="text-muted-foreground">此处将显示垂直剖面图</p>}
      </CardContent>
    </Card>
  );
};

export default ProfileChart;