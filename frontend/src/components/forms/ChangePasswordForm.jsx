/**
 * ChangePasswordForm Component
 * 
 * @file ChangePasswordForm.jsx
 * @component
 * @param {Object} props
 * @param {Function} props.onCancel - Callback function to handle the cancel action.
 * 
 * @returns {JSX.Element} The rendered ChangePasswordForm component.
 * 
 * @example
 * <ChangePasswordForm onCancel={() => console.log('Cancel clicked')} />
 * 
 * @remarks
 * - The `newPassword` and `confirmPassword` must match.
 * - Success and error messages are automatically cleared after 5 seconds.
 * - Uses the `BASE_API` constant for the API endpoint.
 */

import { useEffect, useState } from 'react';
import { BASE_API, LOGIN_URL, DEBUG } from '../../constants';
import{ FormWrapper, FormContent } from './utils';

/**
 * Performs the password change API request.
 * 
 * @param {string} currentPassword - The user's current password.
 * @param {string} newPassword - The new password.
 * @param {string} confirmPassword - The confirmation of the new password.
 * @returns {Promise<{ success: boolean, data?: any, error?: any }>} The result of the API request.
 */
const changePassword = async (currentPassword, newPassword, confirmPassword) => {
  if (DEBUG) {
    console.log('--- Change Password Request ---');
    console.log('Current Password:', currentPassword);
    console.log('New Password:', newPassword);
    console.log('Confirm Password:', confirmPassword);
  }

  try {
    const url = `${BASE_API}/users/password/change/`;
    const requestBody = {
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    };

    const response = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (response.ok) {
      const result = await response.json();
      return { success: true, data: result };
    } else {
      const errorData = await response.json();
      return { success: false, error: errorData };
    }
  } catch (e) {
    return { success: null, error: e.message };
  }
};

const ChangePasswordForm = ({ onCancel }) => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => {
        setSuccess(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError({ error: null, message: "Passwords did not match." });
      setConfirmPassword('');
      setNewPassword('');
      setCurrentPassword('');
      return;
    }

    setLoading(true);
    const result = await changePassword(currentPassword, newPassword, confirmPassword);

    if (DEBUG) {
      console.log('Result:', result);
    }

    if (result.success) {
      setSuccess({ message: 'Redirecting to login...' });
      setConfirmPassword('');
      setNewPassword('');
      setCurrentPassword('');
      console.log('Password changed successfully.');
      window.location.href = LOGIN_URL;

    } else if (result.success === null) {
      setError({ error: null, message: "Network Error." });
      setConfirmPassword('');
      setNewPassword('');
      setCurrentPassword('');
      console.error('Network error.');
    } else {
      setError({ error: null, message: "Try again." });
      setConfirmPassword('');
      setNewPassword('');
      setCurrentPassword('');
      console.error('Problem changing password.');
    }

    setLoading(false);
  };

  const fields = [
    {
      name: 'currentPassword',
      label: 'Current Password',
      type: 'password',
      value: currentPassword,
      onChange: (e) => setCurrentPassword(e.target.value),
    },
    {
      name: 'newPassword',
      label: 'New Password',
      type: 'password',
      value: newPassword,
      onChange: (e) => setNewPassword(e.target.value),
    },
    {
      name: 'confirmPassword',
      label: 'Confirm Password',
      type: 'password',
      value: confirmPassword,
      onChange: (e) => setConfirmPassword(e.target.value),
    },
  ];

  return (
    <FormWrapper
      onCancel={onCancel}
      onSubmit={handleSubmit}
      cancelLabel="Cancel"
      submitLabel={loading ? 'Submitting' : 'Submit'}
      isSubmitting={loading}
      cancelButtonStyle={{ backgroundColor: 'blue' }}
    >
      <FormContent fields={fields} error={error} success={success} />
    </FormWrapper>
  );
};

export default ChangePasswordForm;