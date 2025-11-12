'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { PasswordField } from '@/components/auth/PasswordField';
import { OtpInput } from '@/components/auth/OtpInput';
import { useAuthStore } from '@/store/authStore';
import { 
  ShieldIcon, 
  KeyIcon, 
  SmartphoneIcon, 
  CheckCircleIcon, 
  AlertCircleIcon,
  EyeOffIcon,
  RefreshCwIcon,
  DownloadIcon,
  CopyIcon
} from 'lucide-react';

export const SecurityTab: React.FC = () => {
  const { 
    user, 
    enableTotp, 
    disableTotp, 
    isLoading, 
    error, 
    clearError 
  } = useAuthStore();
  
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [totpSetup, setTotpSetup] = useState({
    secret: '',
    qrCode: '',
    verificationCode: '',
  });
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  React.useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setSuccessMessage('');
    
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      return;
    }
    
    try {
  // Simulated password change - in a real app, this would call the auth provider
      await new Promise(resolve => setTimeout(resolve, 1000));
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
      setActiveSection(null);
      setSuccessMessage('Password changed successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch {
      // Error is handled by the store
    }
  };

  const handleEnableTotp = async () => {
    clearError();
    setSuccessMessage('');
    
    try {
      const setup = await enableTotp();
      if (setup) {
        setBackupCodes(setup.recoveryCodes);
        setShowBackupCodes(true);
        setActiveSection(null);
        setTotpSetup({ secret: '', qrCode: '', verificationCode: '' });
        setSuccessMessage('Two-factor authentication enabled successfully!');
        setTimeout(() => setSuccessMessage(''), 3000);
      }
    } catch {
      // Error is handled by the store
    }
  };

  const handleDisableTotp = async () => {
    clearError();
    setSuccessMessage('');
    
    try {
  await disableTotp('123456'); // Test verification code
      setActiveSection(null);
      setSuccessMessage('Two-factor authentication disabled.');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch {
      // Error is handled by the store
    }
  };

  const startTotpSetup = async () => {
    clearError();
    
    try {
      // Example TOTP setup data
      const setup = {
        secret: 'JBSWY3DPEHPK3PXP',
        qrCode: `data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==`
      };
      
      setTotpSetup({
        secret: setup.secret,
        qrCode: setup.qrCode,
        verificationCode: '',
      });
      setActiveSection('enable-totp');
    } catch {
      // Error is handled by the store
    }
  };

  const handleGenerateBackupCodes = async () => {
    clearError();
    setSuccessMessage('');
    
    try {
      // Example backup code generation
      const codes = [
        'abc123def', 'ghi456jkl', 'mno789pqr', 'stu012vwx',
        'yza345bcd', 'efg678hij', 'klm901nop', 'qrs234tuv'
      ];
      setBackupCodes(codes);
      setShowBackupCodes(true);
      setSuccessMessage('New backup codes generated successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch {
      // Error is handled by the store
    }
  };

  const copyBackupCodes = () => {
    const codeText = backupCodes.join('\n');
    navigator.clipboard.writeText(codeText);
    setSuccessMessage('Backup codes copied to clipboard!');
    setTimeout(() => setSuccessMessage(''), 2000);
  };

  const downloadBackupCodes = () => {
    const codeText = backupCodes.join('\n');
    const blob = new Blob([codeText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ziggy-backup-codes.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!user) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-fg-muted">Loading security settings...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Messages */}
      {error && (
        <div className="flex items-center space-x-2 text-danger bg-danger/10 p-3 rounded-md border border-danger/20">
          <AlertCircleIcon className="h-4 w-4 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}
      
      {successMessage && (
        <div className="flex items-center space-x-2 text-success bg-success/10 p-3 rounded-md border border-success/20">
          <CheckCircleIcon className="h-4 w-4 flex-shrink-0" />
          <span className="text-sm">{successMessage}</span>
        </div>
      )}

      {/* Password Security */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <KeyIcon className="w-5 h-5" />
            <span>Password Security</span>
          </CardTitle>
          <p className="text-sm text-fg-muted">
            Manage your account password and security settings.
          </p>
        </CardHeader>
        <CardContent>
          {activeSection === 'change-password' ? (
            <form onSubmit={handlePasswordChange} className="space-y-4">
              <PasswordField
                label="Current password"
                value={passwordForm.currentPassword}
                onChange={(value) => setPasswordForm(prev => ({ ...prev, currentPassword: value }))}
                placeholder="Enter your current password"
                required
                disabled={isLoading}
              />
              
              <PasswordField
                label="New password"
                value={passwordForm.newPassword}
                onChange={(value) => setPasswordForm(prev => ({ ...prev, newPassword: value }))}
                placeholder="Enter your new password"
                required
                disabled={isLoading}
              />
              
              <PasswordField
                label="Confirm new password"
                value={passwordForm.confirmPassword}
                onChange={(value) => setPasswordForm(prev => ({ ...prev, confirmPassword: value }))}
                placeholder="Confirm your new password"
                required
                disabled={isLoading}
                error={passwordForm.newPassword && passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword ? 'Passwords do not match' : undefined}
              />
              
              <div className="flex space-x-3 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setActiveSection(null);
                    setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
                    clearError();
                  }}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading || !passwordForm.currentPassword || !passwordForm.newPassword || passwordForm.newPassword !== passwordForm.confirmPassword}
                >
                  {isLoading ? 'Changing...' : 'Change password'}
                </Button>
              </div>
            </form>
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-fg">Password</p>
                <p className="text-sm text-fg-muted">Last changed 3 days ago</p>
              </div>
              <Button
                variant="outline"
                onClick={() => setActiveSection('change-password')}
                disabled={isLoading}
              >
                Change password
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Two-Factor Authentication */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <ShieldIcon className="w-5 h-5" />
            <span>Two-Factor Authentication</span>
          </CardTitle>
          <p className="text-sm text-fg-muted">
            Add an extra layer of security to your account with 2FA.
          </p>
        </CardHeader>
        <CardContent>
          {activeSection === 'enable-totp' ? (
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-lg font-medium text-fg mb-2">Set up Authenticator App</h3>
                <p className="text-sm text-fg-muted mb-4">
                  Scan this QR code with your authenticator app or enter the secret manually.
                </p>
                
                {/* QR Code */}
                <div className="bg-white p-4 rounded-lg inline-block mb-4">
                  <div className="w-48 h-48 bg-gray-200 flex items-center justify-center rounded">
                    <SmartphoneIcon className="w-12 h-12 text-gray-400" />
                  </div>
                </div>
                
                {/* Manual Entry */}
                <div className="bg-surface border border-border rounded-md p-3 mb-4">
                  <p className="text-xs text-fg-muted mb-1">Manual entry key:</p>
                  <code className="text-sm font-mono text-fg break-all">
                    {totpSetup.secret}
                  </code>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-fg mb-2">
                  Verification code
                </label>
                <OtpInput
                  value={totpSetup.verificationCode}
                  onChange={(value) => setTotpSetup(prev => ({ ...prev, verificationCode: value }))}
                  length={6}
                  disabled={isLoading}
                />
                <p className="text-xs text-fg-muted mt-1">
                  Enter the 6-digit code from your authenticator app
                </p>
              </div>
              
              <div className="flex space-x-3">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setActiveSection(null);
                    setTotpSetup({ secret: '', qrCode: '', verificationCode: '' });
                    clearError();
                  }}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleEnableTotp}
                  disabled={isLoading || totpSetup.verificationCode.length !== 6}
                >
                  {isLoading ? 'Enabling...' : 'Enable 2FA'}
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${user.totpEnabled ? 'bg-success' : 'bg-fg-muted'}`} />
                  <div>
                    <p className="text-sm font-medium text-fg">Authenticator App</p>
                    <p className="text-sm text-fg-muted">
                      {user.totpEnabled ? 'Two-factor authentication is enabled' : 'Use an app to generate verification codes'}
                    </p>
                  </div>
                </div>
                {user.totpEnabled ? (
                  <Button
                    variant="outline"
                    onClick={handleDisableTotp}
                    disabled={isLoading}
                  >
                    Disable
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    onClick={startTotpSetup}
                    disabled={isLoading}
                  >
                    Enable
                  </Button>
                )}
              </div>
              
              {user.totpEnabled && (
                <div className="flex items-center justify-between pt-4 border-t border-border">
                  <div>
                    <p className="text-sm font-medium text-fg">Backup codes</p>
                    <p className="text-sm text-fg-muted">Generate new backup codes for account recovery</p>
                  </div>
                  <Button
                    variant="outline"
                    onClick={handleGenerateBackupCodes}
                    disabled={isLoading}
                  >
                    <RefreshCwIcon className="w-4 h-4 mr-2" />
                    Generate codes
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Backup Codes Modal */}
      {showBackupCodes && backupCodes.length > 0 && (
        <Card className="border-warning">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-warning">
              <AlertCircleIcon className="w-5 h-5" />
              <span>Backup Codes</span>
            </CardTitle>
            <p className="text-sm text-fg-muted">
              Save these backup codes in a safe place. You can use them to access your account if you lose your authenticator device.
            </p>
          </CardHeader>
          <CardContent>
            <div className="bg-surface border border-border rounded-md p-4 mb-4">
              <div className="grid grid-cols-2 gap-2 font-mono text-sm">
                {backupCodes.map((code, index) => (
                  <div key={index} className="text-fg">
                    {code}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyBackupCodes}
                >
                  <CopyIcon className="w-4 h-4 mr-2" />
                  Copy
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={downloadBackupCodes}
                >
                  <DownloadIcon className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </div>
              
              <Button
                variant="ghost"
                onClick={() => setShowBackupCodes(false)}
              >
                <EyeOffIcon className="w-4 h-4 mr-2" />
                Hide codes
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Security Log */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Security Activity</CardTitle>
          <p className="text-sm text-fg-muted">
            Monitor recent security events on your account.
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 rounded-full bg-success" />
                <div>
                  <p className="text-sm font-medium text-fg">Successful sign in</p>
                  <p className="text-xs text-fg-muted">Chrome on Windows • 192.168.1.100</p>
                </div>
              </div>
              <span className="text-xs text-fg-muted">2 hours ago</span>
            </div>
            
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 rounded-full bg-success" />
                <div>
                  <p className="text-sm font-medium text-fg">Password changed</p>
                  <p className="text-xs text-fg-muted">Chrome on Windows • 192.168.1.100</p>
                </div>
              </div>
              <span className="text-xs text-fg-muted">3 days ago</span>
            </div>
            
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 rounded-full bg-success" />
                <div>
                  <p className="text-sm font-medium text-fg">2FA enabled</p>
                  <p className="text-xs text-fg-muted">Safari on macOS • 192.168.1.101</p>
                </div>
              </div>
              <span className="text-xs text-fg-muted">1 week ago</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};