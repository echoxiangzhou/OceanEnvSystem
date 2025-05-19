import React from 'react';
import { cn } from '@/lib/utils';

interface MainContentProps extends React.HTMLAttributes<HTMLElement> {
  isSidebarOpen?: boolean;
}

const MainContent: React.FC<MainContentProps> = ({ 
  children, 
  className,
  isSidebarOpen = true,
  ...props 
}) => {
  return (
    <main
      className={cn(
        "flex-1 overflow-auto p-md md:p-lg transition-all duration-300 ease-in-out",
        {
          "md:ml-64": isSidebarOpen,
          "ml-0": !isSidebarOpen
        },
        className
      )}
      {...props}
    >
      {children}
    </main>
  );
};

export default MainContent;