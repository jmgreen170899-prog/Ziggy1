'use client';

import React from 'react';
import SignUp from '@/features/auth/SignUp';

export default function SignUpPage() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <SignUp />
    </div>
  );
}