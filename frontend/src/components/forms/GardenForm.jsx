/**
 * @file GardenForm.jsx
 * @description Form component for creating gardens with x/y dimensions and name
 * 
 */
import { useContext, useEffect, useState } from 'react';
import { GridLoading } from '../widgets';
import { FormWrapper, FormContent } from './utils';
import { UserContext } from '../../context/UserProvider';
import { BASE_API } from '../../constants';
import './utils/styles/form.css';

/**
 * Performs the garden creation API request.
 * 
 * @param {{ size_x: number, size_y: number, name: string }} newGarden
 * @returns {Promise<{ success: boolean|null, data?: any, error?: any }>}
 */
const createGarden = async (newGarden) => {
  try {
    const url = `${BASE_API}/gardens/gardens/`;
    const requestBody = newGarden;

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

const GardenForm = ({ callback, focus=false }) => {
  const [x, setX] = useState('');
  const [y, setY] = useState('');
  const [name, setName] = useState('');
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { dispatch } = useContext(UserContext);

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

    // Soft validation
    if (!x || !y || !name) {
      setError({ message: 'All fields are required.' });
      return;
    }
    if (isNaN(x) || isNaN(y)) {
      setError({ message: 'X and Y must be integers.' });
      return;
    }
    if (name.trim().length === 0) {
      setError({ message: 'Name cannot be empty.' });
      return;
    }

    setLoading(true);

    const newGarden = {
      size_x: parseInt(x, 10),
      size_y: parseInt(y, 10),
      name: name.trim(),
    };

    const result = await createGarden(newGarden);

    if (result.success) {
      setSuccess({ message: 'Garden created successfully!' });
      dispatch({ type: 'ADD_GARDEN', payload: { ...result.data, Notifications: [] } });
      setX('');
      setY('');
      setName('');
      callback();
      console.log('Garden created successfully:', result.data);
    } else if (result.success === null) {
      setError({ message: 'Network Error.', error: result.error });
      setX('');
      setY('');
      setName('');
      console.error('Network error:', result.error);
    } else {
      setError({
        message: 'Failed to create garden.',
        size_x: result.error.size_x || [],
        size_y: result.error.size_y || [],
        name: result.error.name || ['Invalid input.'],
      });
      setX('');
      setY('');
      setName('');
      console.error('Problem creating garden:', result.error);
    }

    setLoading(false);
  };

  if (loading) {
    return (
      <div className="loading-container">
        <GridLoading />
      </div>
    );
  }

  const fields = [
    {
      name: 'x',
      label: 'X (Integer)',
      type: 'number',
      value: x,
      onChange: (e) => setX(e.target.value),
    },
    {
      name: 'y',
      label: 'Y (Integer)',
      type: 'number',
      value: y,
      onChange: (e) => setY(e.target.value),
    },
    {
      name: 'name',
      label: 'Name (String)',
      type: 'text',
      value: name,
      onChange: (e) => setName(e.target.value),
    },
  ];

  return (
    <FormWrapper
      onCancel={callback}
      onSubmit={handleSubmit}
      submitLabel={loading ? 'Submitting' : 'Submit'}
      isSubmitting={loading}
    >
      <FormContent fields={fields} error={error} success={success} />
    </FormWrapper>
  );
};

export default GardenForm;