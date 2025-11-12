'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/Button';
import {
  UserIcon,
  LogOutIcon,
  CreditCardIcon,
  ShieldIcon,
  ChevronDownIcon,
  BellIcon,
  SmartphoneIcon,
} from 'lucide-react';

export function AccountMenu() {
  const router = useRouter();
  const { user, signOut, isAuthenticated } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSignOut = async () => {
    await signOut();
    setIsOpen(false);
    router.push('/auth/signin');
  };

  const handleSignIn = () => {
    router.push('/auth/signin');
  };

  if (!isAuthenticated || !user) {
    return (
      <div className="flex items-center space-x-2">
        <Button variant="outline" size="sm" onClick={handleSignIn}>
          Sign In
        </Button>
      </div>
    );
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <div className="flex items-center space-x-2">
          {user.avatarUrl ? (
            <Image
              src={user.avatarUrl}
              alt="Profile"
              width={32}
              height={32}
              className="w-8 h-8 rounded-full object-cover border border-gray-200"
            />
          ) : (
            <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center">
              <UserIcon className="w-4 h-4" />
            </div>
          )}
          <div className="hidden md:block text-left">
            <div className="text-sm font-medium text-gray-900">{user.name}</div>
            <div className="text-xs text-gray-600">{user.email}</div>
          </div>
        </div>
        <ChevronDownIcon
          className={`w-4 h-4 text-gray-600 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-xl backdrop-blur-sm z-50">
          <div className="p-3 border-b border-gray-200 bg-gray-50/80">
            <div className="flex items-center space-x-3">
              {user.avatarUrl ? (
                <Image
                  src={user.avatarUrl}
                  alt="Profile"
                  width={40}
                  height={40}
                  className="w-10 h-10 rounded-full object-cover border border-gray-200"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center">
                  <UserIcon className="w-5 h-5" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-900 truncate">{user.name}</div>
                <div className="text-xs text-gray-600 truncate">{user.email}</div>
                <div className="text-xs text-gray-500 capitalize">
                  {user.role} account
                </div>
              </div>
            </div>
          </div>

          <div className="py-2">
            <Link
              href="/account/profile"
              className="flex items-center px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              <UserIcon className="w-4 h-4 mr-3 text-gray-600" />
              Profile & Account
            </Link>
            <Link
              href="/account/security"
              className="flex items-center px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              <ShieldIcon className="w-4 h-4 mr-3 text-gray-600" />
              Security
            </Link>
            <Link
              href="/account/devices"
              className="flex items-center px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              <SmartphoneIcon className="w-4 h-4 mr-3 text-gray-600" />
              Devices
            </Link>
            <Link
              href="/account/billing"
              className="flex items-center px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              <CreditCardIcon className="w-4 h-4 mr-3 text-gray-600" />
              Billing
            </Link>
            <Link
              href="/alerts"
              className="flex items-center px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              <BellIcon className="w-4 h-4 mr-3 text-gray-600" />
              Alerts & Notifications
            </Link>
          </div>



          <div className="border-t border-gray-200 py-2">
            <button
              onClick={handleSignOut}
              className="flex items-center w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
            >
              <LogOutIcon className="w-4 h-4 mr-3" />
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}