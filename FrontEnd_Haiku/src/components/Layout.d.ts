import React from 'react';

export interface LayoutProps {
  children: React.ReactNode;
}

declare const Layout: React.FC<LayoutProps>;

export default Layout;