
/**
 * @file FormContent.jsx
 * @description A React component for rendering a dynamic form with support for various input types, error messages, and success messages.
 * 
 * @param {Object} props - The props object.
 * @param {Array} props.fields - An array of field objects to render. Each field object should contain properties like `name`, `label`, `type`, `value`, `onChange`, and optionally `component`, `options`, `placeholder`, and `min`.
 * @param {Object} [props.error] - An object containing error messages for the fields. Each field's error can be an array of strings.
 * @param {Object} [props.success] - An object containing a success message to display.
 * 
 * @returns {JSX.Element} The rendered form content.
 */
import './styles/form.css';

const FormContent = ({ fields, error, success }) => {
  return (
    <div className="form-input-container">
      {fields.map((field) => (
        <div key={field.name} className="form-field-container">
          <label htmlFor={field.name} className="form-label">
            {field.label}:
          </label>
          {error &&
            error[field.name] &&
            Array.isArray(error[field.name]) &&
            error[field.name].map((err, index) => (
              <div key={`${field.name}-error-${index}`} className="message-error">
                {err.split('.')[0]}
              </div>
            ))}
          {field.component ? (
            <field.component {...field} />
          ) : field.type === 'select' ? (
            <select
              id={field.name}
              name={field.name}
              className="form-input"
              value={field.value}
              onChange={field.onChange}
            >
              {field.options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              type={field.type}
              id={field.name}
              name={field.name}
              className="form-input"
              value={field.value}
              onChange={field.onChange}
              placeholder={field.placeholder}
              min={field.min}
            />
          )}
        </div>
      ))}
      <div className="message-container">
        {error && <div className="message-error">{error.message}</div>}
        {success && <div className="message-success">{success.message}</div>}
      </div>
    </div>
  );
};

export default FormContent;