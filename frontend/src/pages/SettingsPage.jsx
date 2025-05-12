/**
 * SettingsPage Component
 * 
 * @file SettingsPage.jsx
 * @version 1.0.0
 * @description A page component that allows users to manage their account settings.
 * This component provides options to change password, username, or delete the user account.
 * 
 * @component
 * @returns {JSX.Element} The rendered SettingsPage component.
 * 
 * @example
 * <SettingsPage />
 * 
 * @remarks
 * - Provides options to change password, username, or delete the user account.
 * - Toggles between displaying buttons and specific forms (ChangePasswordForm, ChangeUsernameForm).
 * - Uses PromptModal to collect password for account deletion.
 * - Uses ErrorModal to display error messages instead of alerts.
 * - Hides main content when PromptModal or ErrorModal is open for exclusive display.
 * - Navigates to the dashboard on back button click.
 * - Uses the BASE_API constant for API endpoints and LOGIN_URL for redirection.
 */

import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChangePasswordForm, ChangeUsernameForm } from '../components/forms';
import { NavBar } from '../components/layout';
import { PromptModal, ErrorModal } from '../components/modals';
import { BASE_API, LOGIN_URL, DEBUG } from '../constants';
import { GenericButton } from '../components/buttons';
import { CSSTransition } from 'react-transition-group'; // You'll need to install this package
import './styles/settings-page.css';

/**
 * Deletes the user account.
 * 
 * @param {string} password - The user's password to confirm account deletion.
 * @returns {Promise<{ success: boolean, data?: any, error?: string }>} The result of the API request.
 */
const deleteAccount = async (password) => {
  if (DEBUG) {
    console.log('--- Delete Account Request ---');
    console.log('Password provided:', password ? 'Yes' : 'No');
  }

  try {
    const response = await fetch(`${BASE_API}/users/me/delete/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ password }),
    });

    if (response.ok) {
      if (DEBUG) {
        console.log('Account deleted successfully');
      }
      return { success: true, data: await response.json() };
    } else {
      const errorData = await response.json();
      if (DEBUG) {
        console.error('Error deleting account:', errorData);
      }
      return { success: false, error: errorData.message || 'Failed to delete account' };
    }
  } catch (error) {
    if (DEBUG) {
      console.error('Error deleting account:', error);
    }
    return { success: false, error: error.message };
  }
};

const SettingsPage = () => {
  const navigate = useNavigate();
  const [togglePasswordForm, setTogglePasswordForm] = useState(false);
  const [toggleUsernameForm, setToggleUsernameForm] = useState(false);
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleDeleteAccount = async (password) => {
    if (DEBUG) {
      console.log('--- handleDeleteAccount ---');
      console.log('Initiating account deletion with password:', password ? 'Yes' : 'No');
    }

    if (!password) {
      if (DEBUG) {
        console.log('No password provided, aborting deletion');
      }
      return;
    }

    const result = await deleteAccount(password);
    if (result.success) {
      if (DEBUG) {
        console.log('Account deletion successful, redirecting to login');
      }
      window.location.href = LOGIN_URL;
    } else {
      setErrorMessage(result.error);
      if (DEBUG) {
        console.log('Account deletion failed:', result.error);
      }
    }
  };

  return (
    <div>
      <NavBar title="Settings" buttonOptions={['back']} onBack={() => navigate('/dashboard')} />
      <div className="settings-content">
        {(!showPromptModal && !errorMessage) && (
          <>
            {!togglePasswordForm && !toggleUsernameForm && (
              <SettingsButtons 
                onPasswordChange={() => setTogglePasswordForm(true)}
                onUsernameChange={() => setToggleUsernameForm(true)}
                onDeleteAccount={() => setShowPromptModal(true)}
              />
            )}
            {togglePasswordForm && <ChangePasswordForm focus={true} onCancel={() => setTogglePasswordForm(false)} />}
            {toggleUsernameForm && <ChangeUsernameForm focus={true} onCancel={() => setToggleUsernameForm(false)} />}
          </>
        )}
        <PromptModal
          message="Enter password to confirm deletion"
          placeholder="Enter password"
          ConfirmStyle={{backgroundColor: '#A3351F'}}
          onConfirm={(password) => {
            handleDeleteAccount(password);
            setShowPromptModal(false);
          }}
          onCancel={() => setShowPromptModal(false)}
          isOpen={showPromptModal}
        />
        <ErrorModal
          isOpen={!!errorMessage}
          onClose={() => setErrorMessage(null)}
          message={errorMessage || 'An error occurred'}
        />
      </div>
    </div>
  );
};


/**
 * SettingsButtons Component
 * 
 * @file SettingsButtons.jsx
 * @component
 * @returns {JSX.Element} The rendered SettingsButtons component.
 * 
 * @example
 * <SettingsButtons 
 *   onPasswordChange={() => setTogglePasswordForm(true)}
 *   onUsernameChange={() => setToggleUsernameForm(true)}
 *   onDeleteAccount={() => setShowPromptModal(true)}
 * />
 * 
 * @remarks
 * - Consolidates the three settings action buttons into a single component
 * - Handles click events for changing password, username, and deleting account
 * - Style can be customized via CSS class or inline styles
 */
const SettingsButtons = ({
  onPasswordChange,
  onUsernameChange,
  onDeleteAccount,
  className = "form parchment"
}) => {
  const [visible, setVisible] = useState(false);
  const nodeRef = useRef(null);
  const formRef = useRef(null);

  // Set visible to true after component mounts to trigger transition
  useEffect(() => {
    // Small delay to ensure React has time to render the component
    const timer = setTimeout(() => {
      setVisible(true);
    }, 10);
    
    return () => {
      clearTimeout(timer);
      setVisible(false);
    };
  }, []);

  useEffect(() => {
    if (formRef.current) {
      formRef.current.focus();
    }
  }, [visible]);

  return (    
    <CSSTransition
      nodeRef={nodeRef}
      in={visible}
      timeout={300}
      classNames="fade"
      unmountOnExit
      onEnter={() => console.log('Entering SettingsButtons')}
      onExit={() => console.log('Exiting SettingsButtons')}
    >
      <div className={className} ref={(el) => { nodeRef.current = el; formRef.current = el; }}>
        <GenericButton
          label="Change Password"
          disableMouseOver={true}
          style={{ width: '66%' }}
          onClick={onPasswordChange}
        />
        <GenericButton
          label="Change Username"
          disableMouseOver={true}
          style={{ marginTop: '20px', width: '66%' }}
          onClick={onUsernameChange}
        />
        <GenericButton
          label="DELETE ACCOUNT"
          disableMouseOver={true}
          style={{ backgroundColor: '#A3351F', marginTop: '20px', width: '66%' }}
          onClick={onDeleteAccount}
        />
      </div>
    </CSSTransition>
  );
};

export default SettingsPage;