/**
 * @file NotificationForm.jsx
 * @description A form component for creating and managing notifications associated with plants in a garden.
 */
import { useState, useEffect, useContext } from 'react';
import { AddWithOptions } from '../ui';
import { FormWrapper, FormContent } from './utils';
import { UserContext } from '../../context/UserProvider';
import { 
  BASE_API, 
  MAX_PLANTS_NOTIFICATION, 
  MAX_CHAR_NOTIFICATION, 
  DEBUG 
} from '../../constants';

/**
 * Performs the notification creation API request, including plant association and fetching updated data.
 * 
 * @param {Object} newNotification
 * @param {Array} plants 
 * @param {number} gardenIndex
 * @param {Function} refreshCounts
 * @returns {Promise<{ success: boolean|null, data?: any, error?: any }>} 
 */
const createNotification = async (newNotification, plants) => {
  if (DEBUG) {
    console.log('--- Create Notification Request ---');
    console.log('New Notification Data:', newNotification);
    console.log('Selected Plants:', plants);
  }
  try {
    const notificationResponse = await fetch(`${BASE_API}/notifications/notifications/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(newNotification),
    });

    if (!notificationResponse.ok) {
      const errorData = await notificationResponse.json();
      return { success: false, error: errorData };
    }

    const notificationData = await notificationResponse.json();

    if (DEBUG) {
      console.log('notification result:', notificationData);
    }

    for (const plant of plants) {
      try {
        const plantResponse = await fetch(`${BASE_API}/notifications/notifications/${notificationData.id}/add_plant/`, {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ plant_id: plant.id }),
        });

        if (!plantResponse.ok) {
          console.error('Add plant failed:', plantResponse.statusText);
          continue;
        }
      } catch (error) {
        console.error('Error adding plant:', error);
      }
    }

    const updatedNotificationResponse = await fetch(`${BASE_API}/notifications/notifications/${notificationData.id}/`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!updatedNotificationResponse.ok) {
      const errorData = await updatedNotificationResponse.json();
      return { success: false, error: errorData };
    }

    const updatedNotificationData = await updatedNotificationResponse.json();
    return { success: true, data: updatedNotificationData };
  } catch (error) {
    return { success: null, error: error.message };
  }
};

const NotificationForm = ({ setToggleForm, onBack, selectedGardenIndex }) => {
  const [selectedPlants, setSelectedPlants] = useState(new Set());
  const [formName, setFormName] = useState('');
  const [formType, setFormType] = useState('');
  const [formInterval, setFormInterval] = useState(7);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [plantOptions, setPlantOptions] = useState([]);
  const { gardens, dispatch, refreshCounts } = useContext(UserContext);

  useEffect(() => {
    const determinePlantOptions = () => {
      setSelectedPlants(new Set());
      if (DEBUG) console.log('--- Determining plant options ---');
      setPlantOptions([]);
      const garden = gardens[selectedGardenIndex];
      const optionsTaken = garden.notifications
        .filter(notification => notification.type === formType)
        .map(notification => notification.plant_names);
      if (DEBUG) console.log('Options taken:', optionsTaken);
     
      const plantOptions = garden.cells
        .flat()
        .filter(cell => cell !== null)
        .map(cell => cell.plant_detail);
      const uniqueOptions = Array.from(new Map(plantOptions.map(plant => [plant.id, plant])).values());
      const optionsFiltered = uniqueOptions.filter(plant => {
        const isTaken = optionsTaken.some(taken => taken.includes(plant.name));
        return !isTaken;
      });

      if (DEBUG) console.log('Filtered plant options:', optionsFiltered);
      setPlantOptions(optionsFiltered);
    };
    determinePlantOptions();
  }, [gardens, selectedGardenIndex, formType]);

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

  const handlePlantSelection = (selected) => {
    if (DEBUG) console.log('Plants selected:', selected);
    if (selected.length > MAX_PLANTS_NOTIFICATION) {
      setError({ message: `Select up to ${MAX_PLANTS_NOTIFICATION} plants.` });
      return;
    }
    setSelectedPlants(new Set(selected));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    const name = formName.trim();
    const type = formType;
    const interval = formInterval;
    const gardenIndex = selectedGardenIndex;

    if (!name) {
      setError({ message: 'Enter a notification name.', name: [] });
      setSubmitting(false);
      return;
    }
    if (name.length > MAX_CHAR_NOTIFICATION) {
      setError({ message: `Name > ${MAX_CHAR_NOTIFICATION} characters.` });
      setSubmitting(false);
      return;
    }
    if (!type) {
      setError({ message: 'Select a notification type.', type: [] });
      setSubmitting(false);
      return;
    }
    if (interval < 1) {
      setError({ message: 'Interval must be at least 1 day.', interval: [] });
      setSubmitting(false);
      return;
    }
    if (selectedPlants.size === 0) {
      setError({ message: 'Select at least one plant.', plant_names: [] });
      setSubmitting(false);
      return;
    }
    const isNameDuplicate = gardens[gardenIndex].notifications?.some(
      (existingNotification) => existingNotification.name.toLowerCase() === name.toLowerCase()
    );
    if (isNameDuplicate) {
      setError({ message: 'Name must be unique.', name: [] });
      setSubmitting(false);
      return;
    }

    const plants = Array.from(selectedPlants).map(plant => ({
      name: plant.name,
      id: plant.id,
    }));

    const newNotification = {
      garden: gardens[gardenIndex].id,
      name: name,
      type: type,
      interval: interval,
      next_due: new Date(Date.now() + interval * 24 * 60 * 60 * 1000).toISOString(),
      plant_names: plants.map(plant => plant.name),
    };

    if (DEBUG) console.log('New notification data:', newNotification);

    const result = await createNotification(newNotification, plants, gardenIndex);

    if (result.success) {
      refreshCounts();
      setSuccess({ message: 'Notification created successfully!' });
      dispatch({ type: 'ADD_NOTIFICATION', garden_index: selectedGardenIndex, payload: result.data });
      setFormName('');
      setFormType('');
      setFormInterval(7);
      setSelectedPlants(new Set());
      setToggleForm(false);
      if (DEBUG) console.log('Notification created successfully:', result.data);
    } else if (result.success === null) {
      setError({ message: 'Network Error.', error: result.error });
      setFormName('');
      setFormType('');
      setFormInterval(7);
      setSelectedPlants(new Set());
      console.error('Network error:', result.error);
    } else {
      setError({
        message: 'Failed to create notification.',
        name: result.error.name || [],
        type: result.error.type || [],
        interval: result.error.interval || [],
        plant_names: result.error.plant_names || ['Invalid input.'],
      });
      setFormName('');
      setFormType('');
      setFormInterval(7);
      setSelectedPlants(new Set());
      console.error('Problem creating notification:', result.error);
    }

    setSubmitting(false);
  };

  const fields = [
    {
      name: 'name',
      label: 'Name',
      type: 'text',
      value: formName,
      onChange: (e) => setFormName(e.target.value),
      placeholder: 'Enter notification name',
    },
    {
      name: 'type',
      label: 'Notification Type',
      type: 'select',
      value: formType,
      onChange: (e) => setFormType(e.target.value),
      options: [
        { value: '', label: '-- Select Type --' },
        { value: 'WA', label: 'Water' },
        { value: 'FE', label: 'Fertilize' },
        { value: 'PR', label: 'Prune' },
        { value: 'HA', label: 'Harvest' },
        { value: 'OT', label: 'Other' },
        { value: 'WE', label: 'Weather' },
      ],
    },
    {
      name: 'interval',
      label: 'Interval (in days)',
      type: 'number',
      value: formInterval,
      onChange: (e) => setFormInterval(parseInt(e.target.value) || 1),
      min: 1,
    },
    {
      name: 'plant_names',
      label: 'Affected Plants',
      component: AddWithOptions,
      handleSelection: handlePlantSelection,
      options: plantOptions,
      selectedOptions: Array.from(selectedPlants),
    },
  ];

  return (
    <FormWrapper
      onCancel={onBack}
      onSubmit={handleSubmit}
      submitLabel={submitting ? 'Submitting...' : 'Submit'}
      isSubmitting={submitting}
    >
      <FormContent fields={fields} error={error} success={success} />
    </FormWrapper>
  );
};

export default NotificationForm;
