import React, { useState } from 'react';

const SettingsForm = () => {
    const [showAdditionalForm, setShowAdditionalForm] = useState(false);

    const handleAddClick = () => {
        setShowAdditionalForm(true);
    };

    return (
        <div>
            <h2>Settings</h2>
            <form>
                <div>
                    <label htmlFor="username">Username:</label>
                    <input type="text" id="username" name="username" />
                </div>
                <div>
                    <label htmlFor="password">Password:</label>
                    <input type="password" id="password" name="password" />
                </div>
                <button type="button" onClick={handleAddClick}>
                    +
                </button>
            </form>

            {showAdditionalForm && (
                <div>
                    <h3>Additional Form</h3>
                    <form>
                        <div>
                            <label htmlFor="extraField1">Extra Field 1:</label>
                            <input type="text" id="extraField1" name="extraField1" />
                        </div>
                        <div>
                            <label htmlFor="extraField2">Extra Field 2:</label>
                            <input type="text" id="extraField2" name="extraField2" />
                        </div>
                    </form>
                </div>
            )}
        </div>
    );
};

export default SettingsForm;