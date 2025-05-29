import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const TestComponents = () => {
  return (
    <div className="p-8 space-y-4">
      <h1 className="text-2xl font-bold">Component Test</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Test Card</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Button>Primary Button</Button>
            <Button variant="outline">Outline Button</Button>
            <div className="flex gap-2">
              <Badge>Default Badge</Badge>
              <Badge variant="success">Success Badge</Badge>
              <Badge variant="error">Error Badge</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TestComponents;
