import { form } from "framer-motion/client";

// Garden reducer to manage the state of gardens and their notifications
const DEBUG = import.meta.env.VITE_DEBUG === 'true';

export const initialState = null;

// Validation to aid in debugging
export function validate(state, action) {

    switch (action.type) {
        case 'ADD_GARDEN':
            if (!action.payload) {
                throw new Error("Payload is required for ADD_GARDEN action");
            }
            break;

        case 'POPULATE':
            if (!action.payload) {
                throw new Error("Payload is required for POPULATE action");
            }
            if (!Array.isArray(action.payload)) {
                throw new Error("Payload must be an array for POPULATE action");
            }
            break;
        
        case 'REMOVE_GARDEN':
            if (action.garden_index === undefined) {
                throw new Error("Garden index is required for REMOVE_GARDEN action");
            }
            if (typeof action.garden_index !== 'number') {
                throw new Error("Garden index must be a number");
            }
            if (action.garden_index < 0 || action.garden_index >= state.length) {
                throw new Error("Garden index is out of bounds");
            }
            break;

        case 'UPDATE_GARDEN':
            if (action.garden_index === undefined) {
                throw new Error("Garden index is required for UPDATE_GARDEN action");
            }
            if (typeof action.garden_index !== 'number') {
                throw new Error("Garden index must be a number");
            }
            if (action.garden_index < 0 || action.garden_index >= state.length) {
                throw new Error("Garden index is out of bounds");
            }
            if (!action.payload) {
                throw new Error("Payload is required for UPDATE_GARDEN action");
            }
            break;
 
        case 'ADD_NOTIFICATION':
            if (!action.payload) {
                throw new Error("Payload is required for ADD_NOTIFICATION action");
            }
            if (!action.payload.id || !action.payload.name || !action.payload.interval || !action.payload.next_due || !action.payload.plant_names) {
                throw new Error("Notification must have an id, name, interval, next_due, and plant_names");
            }
            break;
        
        case 'REMOVE_NOTIFICATION':
            if (action.notification_id === undefined) {
                throw new Error("Notification id is required for REMOVE_NOTIFICATION action");
            }
            if (typeof action.notification_id !== 'number') {
                throw new Error("Notification id must be a number");
            }
            if (action.notification_id < 0 || action.notification_id >= state.length) {
                throw new Error("Notification id is out of bounds");
            }
            break;

        case 'UPDATE_NOTIFICATION':
            if (!action.notification_id) {
                throw new Error("Notification id is required for UPDATE_NOTIFICATION action");
            }
            if (typeof action.notification_id !== 'number') {
                throw new Error("Notification id must be a number");
            }
            if (action.notification_id < 0 || action.notification_id >= state.length) {
                throw new Error("Notification id is out of bounds");
            }
            if (!action.payload) {
                throw new Error("Payload is required for UPDATE_NOTIFICATION action");
            }
            break;
        
        case 'UPDATE_NOTIFICATIONS':
            if (!action.payload) {
                throw new Error("Payload is required for UPDATE_NOTIFICATIONS action");
            }
            if (!Array.isArray(action.payload)) {
                throw new Error("Payload must be an array for UPDATE_NOTIFICATIONS action");
            }
            if (action.payload.length === 0) {
                throw new Error("Payload must not be empty for UPDATE_NOTIFICATIONS action");
            }
            break;
    }
}

// Reducer function to store garden state
export function gardensReducer(state, action) {
    
    if (DEBUG) {
        console.log("--- Attempting reduction ---");
        console.log("ACTION: ", action); 
        console.log("STATE: ", state);
        
        try {
            validate(state, action);
        } catch (error) {
            console.error("Invalid action: ", error.message);
            return state;
        }
    }

    switch (action.type) {
        case 'ADD_GARDEN':
            if (action.garden_index !== undefined) {
                // Optional index for adding garden
                const updatedGardens = [...state];
                updatedGardens.splice(action.garden_index, 0, formatGarden(action.payload));
                return updatedGardens;
            }
            return [formatGarden(action.payload), ...state];

        case 'POPULATE':
            // Special case for populating on mount
            let processedInfo = action.payload.map((garden) => {
                return formatGarden(garden);
            });

            if (DEBUG) {
                console.log("Processed info: ", processedInfo);
            }
            return [ ...processedInfo];
        
        case 'REMOVE_GARDEN':
            const removeIndex = action.garden_index;
            const newGardens = state.filter((_, index) => { return index !== removeIndex });
            return newGardens;
        
        case 'UPDATE_GARDEN':
            return state.map((garden, index) => {
                return index === action.garden_index ? { ...garden, ...action.payload } : garden;
            });
        
        case 'ADD_NOTIFICATION':
            return { ...state, info: state.map((gardenInfo, index) => {
                    if (index === action.garden_index) {
                        return { ...gardenInfo, notifications: [...gardenInfo.notifications, action.payload] };
                    } else {
                        return gardenInfo;
                    }
                })
            };

        case 'REMOVE_NOTIFICATION':
            return state.map((gardenInfo, index) => {
                if (index === action.garden_index) {
                    return { ...gardenInfo, notifications: gardenInfo.notifications.filter((notification) => notification.id !== action.notification_id) };
                } else {
                    return gardenInfo;
                }
            }
            );

        case 'UPDATE_NOTIFICATION':
            return { ...state, info: state.map((gardenInfo, index) => {
                    if (index === action.garden_index) {
                        return { ...gardenInfo, notifications: gardenInfo.notifications.map((notification) => {
                            if (notification.id === action.notification_id) {
                                return { ...notification, ...action.payload };
                            } else {
                                return notification;
                            }
                        }) };
                    } else {
                        return gardenInfo;
                    }
                })
            };
        
        case 'UPDATE_NOTIFICATIONS':
            return { ...state, info: state.map((gardenInfo, index) => {
                    if (index === action.garden_index) {
                        return { ...gardenInfo, notifications: action.payload };
                    } else {
                        return gardenInfo;
                    }
                }) 
            };
    
        default:
            throw new Error(`Unsupported action type: ${action.type}`);
    }
}

// Translates to reducer expectation from raw response
const formatGarden = (garden) => {
    if (garden.cells && garden.cells.length > 0) {
        return garden;
    }
    const { size_x, size_y, garden_logs } = garden;
    garden.cells = Array.from({ length: size_y }, () => Array.from({ length: size_x }, () => null));
    for (const log of garden_logs) {
        const { x_coordinate, y_coordinate, planted_date, id: logId, plant_details: plant } = log;
        garden.cells[y_coordinate][x_coordinate] = { logId, planted_date, ...plant };
    }
    garden.notifications = garden.notifications || [];
    return garden;
};
