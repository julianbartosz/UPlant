/**
 * @file FormWrapper.jsx
 * @description A reusable form wrapper component with cancel and submit buttons, 
 *              supporting optional modal overlay and customizable labels.
 */
import { GenericButton } from "../../buttons";
import "./styles/form.css";

const FormWrapper = ({
  children,
  onCancel,
  onSubmit,
  cancelLabel = "Return",
  submitLabel = 'Submit',
  isSubmitting = false,
  focus = false,
  cancelButtonStyle = {},
  submitButtonStyle = {},
}) => {
  const content = (
    <div className="form parchment">
      <div className="form-header">
        <GenericButton
          label={cancelLabel}
          onClick={onCancel}
          // Soft blue for default
          style={{ backgroundColor: '#6495ED', ...cancelButtonStyle }}
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
          style={{ backgroundColor: 'rgba(56, 55, 55, 0.8)', ...submitButtonStyle }}
        />
      </div>
    </div>
  );

  return (
    <>
      {focus ? (
        <div className="form-overlay">
          {content}
        </div>
      ) : (
        content
      )}
    </>
  );
};

export default FormWrapper;