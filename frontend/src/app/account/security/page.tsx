'use client';

import React from 'react';
import { AccountLayout } from '@/features/account';
import { SecurityTab } from '@/features/account';

export default function SecurityPage() {
  return (
    <div className="min-h-screen bg-background">
      <AccountLayout>
        <SecurityTab />
      </AccountLayout>
    </div>
  );
}