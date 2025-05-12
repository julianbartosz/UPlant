/**
 * FormWrapper Component
 * 
 * @file FormWrapper.jsx
 * @component
 * @param {Object} props
 * @param {React.ReactNode} props.children - The form content (e.g., inputs, labels).
 * @param {Function} props.onCancel - Callback function for the Cancel button.
 * @param {Function} props.onSubmit - Callback function for the Submit button.
 * @param {string} [props.cancelLabel="Cancel"] - Label for the Cancel button.
 * @param {string} [props.submitLabel="Submit"] - Label for the Submit button.
 * @param {boolean} [props.isSubmitting=false] - Whether the form is submitting (affects Submit button).
 * 
 * @returns {JSX.Element} The rendered FormWrapper component.
 * 
 * @example
 * <FormWrapper onCancel={() => console.log('Canceled')} onSubmit={() => console.log('Submitted')}>
 *   <input type="text" />
 * </FormWrapper>
 * 
 * @remarks
 * - Provides a consistent form layout with Cancel and Submit buttons.
 * - Uses styles from `form.css` for layout and button appearance.
 */

import { GenericButton } from "../../buttons";
import "./styles/form.css"

const FormWrapper = ({
  children,
  onCancel,
  onSubmit,
  cancelLabel = 'Cancel',
  submitLabel = 'Submit',
  isSubmitting = false,
}) => {
  return (
    <div className="form">
      <div className="form-header">
        <GenericButton
          label={cancelLabel}
          onClick={onCancel}
          style={{ backgroundColor: 'blue' }}
          className="form-cancel-button"
          disabled={isSubmitting}
        />
      </div>
      {children}
      <div className="form-footer">
        <GenericButton
          label={submitLabel}
          onClick={onSubmit}
          className="form-button"
          disabled={isSubmitting}
          style={{ backgroundColor: 'rgba(56, 55, 55, 0.8)' }}
        />
      </div>
    </div>
  );
};

export default FormWrapper;