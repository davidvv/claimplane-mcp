import React from 'react';

export interface AuthProps {
  onLogin: (token: string) => void;
}

declare const Auth: React.FC<AuthProps>;

export default Auth;