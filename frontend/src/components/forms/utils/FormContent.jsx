/**
 * FormContent Component
 * 
 * @file FormContent.jsx
 * @component
 * @param {Object} props
 * @param {Array} props.fields - Array of field objects with name, label, type, value, onChange, and optional component, options, or other props.
 * @param {Object|null} props.error - Error state for field-specific and general error messages.
 * @param {Object|null} props.success - Success state for success messages.
 * 
 * @returns {JSX.Element} The rendered FormContent component.
 * 
 * @example
 * <FormContent
 *   fields={[
 *     { name: 'username', label: 'Username', type: 'text', value: '', onChange: () => {} },
 *     { name: 'plants', label: 'Plants', component: AddWithOptions, handleSelection: () => {}, options: [] },
 *   ]}
 *   error={{ message: 'Error', username: ['Invalid'] }}
 *   success={{ message: 'Success' }}
 * />
 * 
 * @remarks
 * - Renders form fields dynamically: standard inputs (text, number), select elements, or custom components.
 * - Displays field-specific errors and general error/success messages.
 * - Uses styles from `form.css` for layout and error/success messages.
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
          {error && error[field.name] && Array.isArray(error[field.name]) && error[field.name].map((err, index) => (
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