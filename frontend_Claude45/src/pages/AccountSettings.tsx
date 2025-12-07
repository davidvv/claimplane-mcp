/**
 * Account Settings Page
 * Allows customers to manage their email, password, and account deletion
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { User, Mail, Lock, Trash2, Calendar, Shield } from 'lucide-react';
import apiClient from '@/services/api';
import { isAuthenticated } from '@/services/auth';

interface AccountInfo {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  created_at: string;
  last_login_at: string | null;
  is_email_verified: boolean;
  total_claims: number;
}

export function AccountSettings() {
  const navigate = useNavigate();
  const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);
  const [loading, setLoading] = useState(true);

  // Email change form
  const [emailForm, setEmailForm] = useState({
    currentPassword: '',
    newEmail: '',
  });
  const [emailChanging, setEmailChanging] = useState(false);

  // Password change form
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [passwordChanging, setPasswordChanging] = useState(false);

  // Account deletion form
  const [deletionForm, setDeletionForm] = useState({
    reason: '',
  });
  const [deleting, setDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/auth');
      return;
    }

    loadAccountInfo();
  }, [navigate]);

  const loadAccountInfo = async () => {
    try {
      const response = await apiClient.get('/account/info');
      setAccountInfo(response.data);
    } catch (error: any) {
      console.error('Failed to load account info:', error);
      toast.error(error.response?.data?.detail || 'Failed to load account information');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailChange = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!emailForm.newEmail || !emailForm.currentPassword) {
      toast.error('Please fill in all fields');
      return;
    }

    setEmailChanging(true);
    try {
      const response = await apiClient.put('/account/email', {
        current_password: emailForm.currentPassword,
        new_email: emailForm.newEmail,
      });

      toast.success(response.data.message);
      setEmailForm({ currentPassword: '', newEmail: '' });

      // User will be logged out, redirect to login
      setTimeout(() => {
        navigate('/auth');
      }, 2000);
    } catch (error: any) {
      console.error('Email change failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to change email');
    } finally {
      setEmailChanging(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!passwordForm.currentPassword || !passwordForm.newPassword) {
      toast.error('Please fill in all fields');
      return;
    }

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    if (passwordForm.newPassword.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return;
    }

    setPasswordChanging(true);
    try {
      const response = await apiClient.put('/account/password', {
        current_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword,
      });

      toast.success(response.data.message);
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });

      // User will be logged out, redirect to login
      setTimeout(() => {
        navigate('/auth');
      }, 2000);
    } catch (error: any) {
      console.error('Password change failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to change password');
    } finally {
      setPasswordChanging(false);
    }
  };

  const handleAccountDeletion = async () => {
    setDeleting(true);
    try {
      const response = await apiClient.post('/account/delete-request', {
        reason: deletionForm.reason || null,
      });

      toast.success(response.data.message, { duration: 8000 });

      // User account is blacklisted, redirect to home
      setTimeout(() => {
        navigate('/');
      }, 3000);
    } catch (error: any) {
      console.error('Account deletion request failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to request account deletion');
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20">
        <div className="container">
          <div className="max-w-4xl mx-auto">
            <div className="animate-pulse space-y-8">
              <div className="h-8 bg-muted rounded w-1/3"></div>
              <div className="h-48 bg-muted rounded"></div>
              <div className="h-48 bg-muted rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!accountInfo) {
    return (
      <div className="py-20">
        <div className="container text-center">
          <h1 className="text-2xl font-bold mb-4">Error Loading Account</h1>
          <p className="text-muted-foreground mb-8">
            Failed to load account information. Please try again.
          </p>
          <button
            onClick={loadAccountInfo}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="py-12">
      <div className="container">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Account Settings</h1>
            <p className="text-muted-foreground">
              Manage your email, password, and account preferences
            </p>
          </div>

          {/* Account Information */}
          <div className="bg-card rounded-lg border p-6 mb-6">
            <div className="flex items-center gap-3 mb-6">
              <User className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-semibold">Account Information</h2>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Name</p>
                <p className="font-medium">{accountInfo.first_name} {accountInfo.last_name}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">Email</p>
                <div className="flex items-center gap-2">
                  <p className="font-medium">{accountInfo.email}</p>
                  {accountInfo.is_email_verified ? (
                    <Shield className="w-4 h-4 text-green-600" title="Verified" />
                  ) : (
                    <Shield className="w-4 h-4 text-muted-foreground" title="Not verified" />
                  )}
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">Member Since</p>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <p className="font-medium">
                    {new Date(accountInfo.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">Total Claims</p>
                <p className="font-medium">{accountInfo.total_claims}</p>
              </div>
              {accountInfo.last_login_at && (
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Last Login</p>
                  <p className="font-medium">
                    {new Date(accountInfo.last_login_at).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Change Email */}
          <div className="bg-card rounded-lg border p-6 mb-6">
            <div className="flex items-center gap-3 mb-6">
              <Mail className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-semibold">Change Email Address</h2>
            </div>

            <form onSubmit={handleEmailChange} className="space-y-4">
              <div>
                <label htmlFor="currentPasswordEmail" className="block text-sm font-medium mb-2">
                  Current Password
                </label>
                <input
                  id="currentPasswordEmail"
                  type="password"
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Enter your current password"
                  value={emailForm.currentPassword}
                  onChange={(e) => setEmailForm({ ...emailForm, currentPassword: e.target.value })}
                  required
                />
              </div>

              <div>
                <label htmlFor="newEmail" className="block text-sm font-medium mb-2">
                  New Email Address
                </label>
                <input
                  id="newEmail"
                  type="email"
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Enter new email address"
                  value={emailForm.newEmail}
                  onChange={(e) => setEmailForm({ ...emailForm, newEmail: e.target.value })}
                  required
                />
              </div>

              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md p-4">
                <p className="text-sm text-amber-800 dark:text-amber-200">
                  <strong>Note:</strong> Changing your email will log you out of all devices. You'll need to log in again with your new email address.
                </p>
              </div>

              <button
                type="submit"
                disabled={emailChanging}
                className="w-full md:w-auto inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
              >
                {emailChanging ? 'Changing Email...' : 'Change Email'}
              </button>
            </form>
          </div>

          {/* Change Password */}
          <div className="bg-card rounded-lg border p-6 mb-6">
            <div className="flex items-center gap-3 mb-6">
              <Lock className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-semibold">Change Password</h2>
            </div>

            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label htmlFor="currentPasswordPass" className="block text-sm font-medium mb-2">
                  Current Password
                </label>
                <input
                  id="currentPasswordPass"
                  type="password"
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Enter your current password"
                  value={passwordForm.currentPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                  required
                />
              </div>

              <div>
                <label htmlFor="newPassword" className="block text-sm font-medium mb-2">
                  New Password
                </label>
                <input
                  id="newPassword"
                  type="password"
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Enter new password (min 8 characters)"
                  value={passwordForm.newPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                  minLength={8}
                  required
                />
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium mb-2">
                  Confirm New Password
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Confirm new password"
                  value={passwordForm.confirmPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                  minLength={8}
                  required
                />
              </div>

              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md p-4">
                <p className="text-sm text-amber-800 dark:text-amber-200">
                  <strong>Note:</strong> Changing your password will log you out of all devices. You'll need to log in again with your new password.
                </p>
              </div>

              <button
                type="submit"
                disabled={passwordChanging}
                className="w-full md:w-auto inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
              >
                {passwordChanging ? 'Changing Password...' : 'Change Password'}
              </button>
            </form>
          </div>

          {/* Account Deletion */}
          <div className="bg-card rounded-lg border border-red-200 dark:border-red-900 p-6">
            <div className="flex items-center gap-3 mb-6">
              <Trash2 className="w-5 h-5 text-red-600" />
              <h2 className="text-xl font-semibold text-red-600 dark:text-red-400">Delete Account</h2>
            </div>

            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 mb-4">
              <p className="text-sm text-red-800 dark:text-red-200 mb-2">
                <strong>Warning:</strong> This action cannot be undone.
              </p>
              <ul className="text-sm text-red-700 dark:text-red-300 list-disc list-inside space-y-1">
                <li>Your account will be immediately deactivated</li>
                <li>You will no longer be able to log in</li>
                <li>Our team will review your request within 2-3 business days</li>
                <li>Your personal data will be permanently deleted within 30 days</li>
                <li>Some data may be retained for legal compliance (up to 7 years)</li>
              </ul>
            </div>

            {!showDeleteConfirm ? (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-red-600 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 h-10 px-4 py-2"
              >
                Request Account Deletion
              </button>
            ) : (
              <div className="space-y-4">
                <div>
                  <label htmlFor="deletionReason" className="block text-sm font-medium mb-2">
                    Reason for Deletion (Optional)
                  </label>
                  <textarea
                    id="deletionReason"
                    className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Please let us know why you're leaving..."
                    rows={3}
                    value={deletionForm.reason}
                    onChange={(e) => setDeletionForm({ ...deletionForm, reason: e.target.value })}
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={handleAccountDeletion}
                    disabled={deleting}
                    className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-red-600 text-white hover:bg-red-700 h-10 px-4 py-2"
                  >
                    {deleting ? 'Submitting Request...' : 'Confirm Deletion'}
                  </button>
                  <button
                    onClick={() => setShowDeleteConfirm(false)}
                    disabled={deleting}
                    className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
