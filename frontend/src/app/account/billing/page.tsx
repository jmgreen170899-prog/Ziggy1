'use client';

import React from 'react';
import { AccountLayout } from '@/features/account';
import { BillingTab } from '@/features/account';

export default function BillingPage() {
  return (
    <div className="min-h-screen bg-background">
      <AccountLayout>
        <BillingTab />
      </AccountLayout>
    </div>
  );
}