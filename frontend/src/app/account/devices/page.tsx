'use client';

import React from 'react';
import { AccountLayout } from '@/features/account';
import { DevicesTab } from '@/features/account';

export default function DevicesPage() {
  return (
    <div className="min-h-screen bg-background">
      <AccountLayout>
        <DevicesTab />
      </AccountLayout>
    </div>
  );
}