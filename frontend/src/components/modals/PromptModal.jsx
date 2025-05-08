/**
 * @file PromptModal.jsx
 * @description A reusable modal component that prompts the user for input and provides confirm and cancel actions.
 *
 * PromptModal Component
 *
 * @param {Object} props - Component properties.
 * @param {string} props.message - The message to display in the modal.
 * @param {string} [props.placeholder=''] - Placeholder text for the input field.
 * @param {Function} props.onConfirm - Callback function to handle the confirm action. Receives the input value as an argument.
 * @param {Function} props.onCancel - Callback function to handle the cancel action.
 * @param {boolean} [props.isOpen=true] - Determines whether the modal is open or closed.
 *
 * @returns {JSX.Element|null} The rendered modal component or null if not open.
 */
import { useState, useEffect, useRef } from 'react';
import { DEBUG } from '../../constants';
import { FormWrapper, FormContent } from '../forms/utils';
import { CSSTransition } from 'react-transition-group'; // You'll need to install this package
import './styles/generic-modal.css';

const PromptModal = ({ message, placeholder = '', onConfirm, onCancel, isOpen = true, ConfirmStyle={} }) => {
  const [input, setInput] = useState('');
  const [error, setError] = useState(null);
  const inputRef = useRef(null);
  const [visible, setVisible] = useState(false);
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
      // Remove the error after 5 seconds
      setTimeout(() => setError(null), 5000);
      return;
    }

    setError(null);

    onConfirm(input);

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
    }, 300); // Matches the transition duration
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
          isSubmitting={false}
          submitLabel="Confirm"
          submitButtonStyle={{ ...ConfirmStyle}}
        >
          <FormContent fields={fields} error={error} success={null} />
        </FormWrapper>
    </div>
    </CSSTransition>
  );
};

export default PromptModal;