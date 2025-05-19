import React from 'react';

type ThemeProviderProps = {
  children: React.ReactNode;
};

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // 这里可以添加主题切换逻辑，如暗/亮模式切换
  return (
    <div className="ocean-theme">
      {children}
    </div>
  );
};

export default ThemeProvider;