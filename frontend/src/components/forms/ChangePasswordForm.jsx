/**
 * @file ChangePasswordForm.jsx
 * @description A React component for handling password change functionality with form validation and animations.
 */

import { useEffect, useState, useRef } from 'react';
import { BASE_API, LOGIN_URL, DEBUG } from '../../constants';
import { FormWrapper, FormContent } from './utils';
import { CSSTransition } from 'react-transition-group';

/**
 * Function to handle password change request.
 * @param {string} currentPassword - The current password of the user.
 * @param {string} newPassword - The new password to be set.
 * @param {string} confirmPassword - Confirmation of the new password.
 * @returns {Promise<Object>} - A promise that resolves to an object containing success status and data or error.
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

const ChangePasswordForm = ({ onCancel, focus = false }) => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState(false);
  const formRef = useRef(null);

  // Set visible to true after component mounts to trigger transition
  useEffect(() => {
    setVisible(true);
    return () => {
      setVisible(false);
    };
  }, []);

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
      setError({ error: null, message: 'Passwords did not match.' });
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
      setError({ error: null, message: 'Network Error.' });
      setConfirmPassword('');
      setNewPassword('');
      setCurrentPassword('');
      console.error('Network error.');
    } else {
      setError({ error: null, message: 'Try again.' });
      setConfirmPassword('');
      setNewPassword('');
      setCurrentPassword('');
      console.error('Problem changing password.');
    }

    setLoading(false);
  };

  const handleCancel = () => {
    setVisible(false);
    // Delay the onCancel call to allow transition to complete
    setTimeout(() => {
      onCancel();
    }, 300); // Matching the transition duration
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
    <CSSTransition
      in={visible}
      timeout={300}
      classNames="form-transition"
      unmountOnExit
      nodeRef={formRef}
    >
      <div ref={formRef} className={focus && 'modal-overlay'}>
        <FormWrapper
          onCancel={handleCancel}
          onSubmit={handleSubmit}
          cancelLabel="Return"
          submitLabel={loading ? 'Submitting' : 'Submit'}
          isSubmitting={loading}
          focus={false}
        >
          <FormContent fields={fields} error={error} success={success} />
        </FormWrapper>
      </div>
    </CSSTransition>
  );
};

export default ChangePasswordForm;