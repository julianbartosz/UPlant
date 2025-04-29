
import { useState } from 'react';
import { GenericButton } from '../buttons';
import { GridLoading } from '../widgets';
import { UserContext } from '../../context/UserProvider';
import { useContext } from 'react';

import './styles/form.css';

const GardenForm = ({ callback }) => {
    const [x, setX] = useState('');
    const [y, setY] = useState('');
    const [name, setName] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const { dispatch } = useContext(UserContext);

    const handleSubmit = () => {

        // Soft validation 
        if (!x || !y || !name) {
            alert('All fields are required.');
            return;
        }
        if (isNaN(x) || isNaN(y)) {
            alert('X and Y must be integers.');
            return;
        }
        if (name.trim().length === 0) {
            alert('Name cannot be empty.');
            return;
        }

        setLoading(true);

        const newGarden = {
            size_x: parseInt(x, 10),
            size_y: parseInt(y, 10),
            name: name.trim(),
        };
        
        const requestBody = newGarden;

        (async () => {
            try {
                const url = 'http://localhost:8000/api/gardens/gardens/'; // Added quotes around the URL

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
                    dispatch({ type: 'ADD_GARDEN', payload: { ...result, Notifications: [] } });
                    setMessage('Form submitted successfully!');
                    callback();
                    console.log('Form submission result:', result);
                } else {
                    const errorData = await response.json();
                    setMessage('Error: ' + response.statusText);
                    console.error('Error submitting form:', errorData.message);
                }
            } catch (e) {
                setError('Error (severe): ' + e.message);
                console.error('Error submitting form:', e);
            } finally {
                setLoading(false);
            }
        })();
    };

    if (loading) {
        return (
            <div className="loading-container">
                <GridLoading />
            </div>
        );
    }

    return (
        <div className="wood-form" >
            <div className="form-header">
            <GenericButton
                label="Return"
                onClick={callback}
                style={{ backgroundColor: 'red' }}
                className="form-cancel-button"
            />
            </div>

            <div className="form-input-container">
            <label htmlFor="x" className="form-label">
                X (Integer):
            </label>
            <input
                type="number"
                id="x"
                name="x"
                className="form-input"
                value={x}
                onChange={(e) => setX(e.target.value)}
            />

            <label htmlFor="y" className="form-label">
                Y (Integer):
            </label>
            <input
                type="number"
                id="y"
                name="y"
                className="form-input"
                value={y}
                onChange={(e) => setY(e.target.value)}
            />

            <label htmlFor="name" className="form-label">
                Name (String):
            </label>
            <input
                type="text"
                id="name"
                name="name"
                className="form-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
            />

            {message && <div style={{ color: 'green' }}>{message}</div>}
            {error && <div style={{ color: 'red' }}>{error}</div>}

            <div className="form-footer">
                <GenericButton
                className="form-button"
                label="Submit"
                onClick={handleSubmit}
                />
            </div>
            </div>
        </div>
        );
};

export default GardenForm;
