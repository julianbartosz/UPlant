/**
 * PromptModal Component
 * 
 * @file PromptModal.jsx
 * @component
 * @param {Object} props
 * @param {string} props.message - The message to display in the prompt.
 * @param {string} [props.placeholder=""] - Placeholder text for the input field.
 * @param {Function} props.onConfirm - Callback function to handle the confirmed input string.
 * @param {Function} props.onCancel - Callback function to handle the cancel action.
 * @param {boolean} [props.isOpen=true] - Controls whether the modal is visible.
 * 
 * @returns {JSX.Element | null} The rendered PromptModal component or null if not open.
 * 
 * @example
 * <PromptModal
 *   message="Please enter your password to confirm account deletion:"
 *   placeholder="Enter password"
 *   onConfirm={(input) => console.log('Confirmed:', input)}
 *   onCancel={() => console.log('Cancelled')}
 *   isOpen={true}
 * />
 * 
 * @remarks
 * - Displays a modal with an input field for a string, using FormWrapper and FormContent for consistency.
 * - Validates that the input is not empty before allowing confirmation.
 * - Implements focus management and ARIA attributes for accessibility.
 * - Supports DEBUG logging for user interactions.
 * - Styled to match ConfirmModal and other form components.
 */

import { useState, useEffect, useRef } from 'react';
import { DEBUG } from '../../constants';
import { FormWrapper, FormContent } from '../forms/utils';
import { CSSTransition } from 'react-transition-group'; // You'll need to install this package
import './styles/generic-modal.css';

const PromptModal = ({ message, placeholder = '', onConfirm, onCancel, isOpen = true }) => {
  const [input, setInput] = useState('');
  const [error, setError] = useState(null);
  const inputRef = useRef(null);
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const formRef = useRef(null);

  // Set visible to true after component mounts to trigger transition
  useEffect(() => {
    if (isOpen) {
      setVisible(true);
    } else {
      setVisible(false);
    }
  }, [isOpen]);
  
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;



  const handleConfirm = () => {

    if (DEBUG) {
      console.log('--- PromptModal handleConfirm ---');
      console.log('Input:', input);
    }

    if (!input.trim()) {
      setError({ message: 'Input cannot be empty' });
      if (DEBUG) {
        console.log('Error: Input is empty');
      }
      return;
    }

    setError(null);
    setLoading(true);
    onConfirm(input);
    setLoading(false);
    if (DEBUG) {
      console.log('Confirmed with input:', input);
    }
  };
  
  const handleCancel = () => {
    setVisible(false);
    if (DEBUG) {
      console.log('--- PromptModal handleCancel ---');
    }
    // Delay the onCancel call to allow transition to complete
    setTimeout(() => {
        if (DEBUG) {
            console.log('PromptModal cancelled');
        }
      onCancel();
    }, 300); // Match this with your CSS transition duration
  };


  const handleInputChange = (e) => {
    setInput(e.target.value);
    setError(null);
    if (DEBUG) {
      console.log('--- PromptModal inputChange ---');
      console.log('New input:', e.target.value);
    }
  };

  const fields = [
    {
      name: 'promptInput',
      label: message,
      type: 'text',
      value: input,
      onChange: handleInputChange,
      placeholder,
      ref: inputRef,
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
    <div ref={formRef} className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-message" >
        <FormWrapper
          onCancel={handleCancel}
          onSubmit={handleConfirm}
          cancelLabel="Cancel"
          submitLabel="Confirm"
          isSubmitting={false}
          cancelButtonStyle={{ backgroundColor: 'blue' }}
          submitButtonStyle={{ backgroundColor: 'green' }}
        >
          <FormContent fields={fields} error={error} success={null} />
        </FormWrapper>
    </div>
    </CSSTransition>
  );
};

export default PromptModal;