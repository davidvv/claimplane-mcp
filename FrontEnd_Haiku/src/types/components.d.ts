// Global type declarations for components

declare module '*.tsx' {
  const component: React.FC<any>;
  export default component;
}

declare module '@/components/*' {
  const component: React.FC<any>;
  export default component;
}

declare module '../../components/*' {
  const component: React.FC<any>;
  export default component;
}

declare module './components/*' {
  const component: React.FC<any>;
  export default component;
}