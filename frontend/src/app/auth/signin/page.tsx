'use client';

import React from 'react';
import SignIn from '@/features/auth/SignIn';

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <SignIn />
    </div>
  );
}