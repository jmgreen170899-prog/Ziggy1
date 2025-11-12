'use client';

import React from 'react';
import { AccountLayout } from '@/features/account';
import { ProfileTab } from '@/features/account';

export default function AccountPage() {
  return (
    <div className="min-h-screen bg-background">
      <AccountLayout>
        <ProfileTab />
      </AccountLayout>
    </div>
  );
}