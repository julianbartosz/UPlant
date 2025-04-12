import React from 'react';
import AddWithOptions from '../ui/AddWithOptions';

const NotificationForm = () => {

    const enableSub

    return (
        <div>
            <label htmlFor="notifications">Notifications:</label>
            
            <select id="notifications" name="notifications">
              
                <option value=>Email</option>
                <option value="sms">SMS</option>
                <option value="push">Push Notifications</option>
            </select>
        </div>
    );
};



export default NotificationForm;
