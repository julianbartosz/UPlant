/**
 * ChangeUsernameForm Component
 * 
 * @file ChangeUsernameForm.jsx
 * @component
 * @param {Object} props
 * @param {Function} props.onCancel - Callback function to handle the cancel action.
 * 
 * @returns {JSX.Element} The rendered ChangeUsernameForm component.
 * 
 * @example
 * <ChangeUsernameForm onCancel={() => console.log('Cancel clicked')} />
 * 
 * @remarks
 * - The `newUsername` must be at least 5 characters long and different from the current username.
 * - Success and error messages are automatically cleared after 5 seconds.
 * - Uses the `VITE_USERNAME_CHANGE_API_URL` environment variable for the API endpoint.
 */

import { useContext, useEffect, useState } from 'react';
import { FormWrapper, FormContent } from './utils';
import { BASE_API, DEBUG } from '../../constants';
import { UserContext } from '../../context/UserProvider';

/**
 * Performs the username change API request.
 * 
 * @param {string} newUsername - The new username.
 * @param {string} currentUsername - The current username.
 * @returns {Promise<{ success: boolean|null, data?: any, error?: any }>} The result of the API request.
 */
const changeUsername = async (newUsername, currentUsername) => {
  if (DEBUG) {
    console.log('--- Change Username Request ---');
    console.log('Current Username:', currentUsername);
    console.log('New Username:', newUsername);
  }

  try {
    const url = `${BASE_API}/users/me/update_username/`;
    const requestBody = { username: newUsername };

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

const ChangeUsernameForm = ({ onCancel }) => {
  const [newUsername, setNewUsername] = useState('');
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { user, setUser } = useContext(UserContext);

  useEffect(() => {
    if (user?.username && user.username !== newUsername) {
      setNewUsername(user.username);
    }
  }, [user?.username]);

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
    setSuccess(null);
    setError(null);
    if (!newUsername) {
      setError({ message: 'Username cannot be empty.' });
      setNewUsername(user.username);
      return;
    }
    if (newUsername === user?.username) {
      setError({ message: 'Please try again.' });
      setNewUsername(user.username);
      return;
    }
    if (newUsername.length < 5) {
      setError({ message: 'Username is too short.' });
      return;
    }

    setLoading(true);
    const result = await changeUsername(newUsername, user?.username);
    if (DEBUG) {
      console.log('--- Change Username Result ---');
      console.log('Result:', result);
    }

    if (result.success) {
      setSuccess({ message: 'Success.' });
      setUser({ ...user, username: newUsername });
      setNewUsername(newUsername);
      console.log('Username changed successfully:', result.data);

    } else if (result.success === null) {
      setError({ message: 'Network Error.', error: result.error });
      setNewUsername(user.username);
      console.error('Network error:', result.error);

    } else {
      setError({
        message: 'Please try again.',
        error: result.error,
      });
      setNewUsername(user.username);
      console.error('Problem changing username:', result.error);
    }

    setLoading(false);
  };

  const fields = [
    {
      name: 'newUsername',
      label: 'New Username',
      type: 'text',
      value: newUsername,
      onChange: (e) => setNewUsername(e.target.value),
    },
  ];

  return (
    <FormWrapper
      onCancel={onCancel}
      onSubmit={handleSubmit}
      cancelLabel="Cancel"
      submitLabel={loading ? 'Submitting' : 'Submit'}
      isSubmitting={loading}
      cancelButtonStyle={{ backgroundColor: 'red' }}
    >
      <FormContent fields={fields} error={error} success={success} />
    </FormWrapper>
  );
};

export default ChangeUsernameForm;