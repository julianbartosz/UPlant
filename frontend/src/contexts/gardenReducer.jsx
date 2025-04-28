// Garden reducer to manage the state of gardens and their notifications
const DEBUG = import.meta.env.VITE_DEBUG === 'true';

const initialState = {contentSize: null, info: null};

// Validation to aid in debugging
function validate(state, action) {

    switch (action.type) {
        case 'UPDATE_CONTENT':
            if (!action.contentSize.width || !action.contentSize.height) {
                throw new Error("Content size must include both width and height");
            }
            if (action.contentSize.width <= 0 || action.contentSize.height <= 0) {
                throw new Error("Content size must be greater than zero");
            }
            if (typeof action.contentSize.width !== 'number' || typeof action.contentSize.height !== 'number') {
                throw new Error("Content size must be a number");
            }
            break;

        case 'ADD_GARDEN':
            if (!action.payload) {
                throw new Error("Payload is required for ADD_GARDEN action");
            }
            if (!action.payload.id || !action.payload.name || !action.payload.size_x || !action.payload.size_y || !action.payload.cells) {
                throw new Error("Garden must have an id, name, size_x, size_y, and cells");
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
            if (action.garden_index < 0 || action.garden_index >= state.info.length) {
                throw new Error("Garden index is out of bounds");
            }
            break;

        case 'UPDATE_GARDEN':
            if (!action.garden_index) {
                throw new Error("Garden index is required for UPDATE_GARDEN action");
            }
            if (typeof action.garden_index !== 'number') {
                throw new Error("Garden index must be a number");
            }
            if (action.garden_index < 0 || action.garden_index >= state.info.length) {
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
            if (action.notification_id < 0 || action.notification_id >= state.info.length) {
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
            if (action.notification_id < 0 || action.notification_id >= state.info.length) {
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

// Reducer function to handle garden actions
function gardenReducer(state, action) {
    // Validate action before processing
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
        case 'UPDATE_CONTENT':
            validateContentAction(action);
            return {...state, contentSize: action.contentSize};

        case 'ADD_GARDEN':
            validateGardenAction(action);
            return {contentSize: state.contentSize, info: [action.payload, ...state.info]};

        case 'POPULATE':
            // Special case for populating on mount, skip validation
            let processedInfo = action.payload.map((garden) => {
                const { size_x, size_y, garden_logs } = garden;
                garden.cells = Array.from({ length: size_y }, () => Array.from({ length: size_x }, () => null));
                for (const log of garden_logs) {
                    const { x_coordinate, y_coordinate, planted_date, id: logId, plant_details: plant } = log;
                    garden.cells[y_coordinate][x_coordinate] = { logId, planted_date, ...plant };
                }
                // Remove garden_logs from the final state to avoid redundancy
                return { ...garden, garden_logs: undefined };
            });
            return { contentSize: state.contentSize, info: processedInfo };
        
        case 'REMOVE_GARDEN':
            validateGardenAction(action);
            const removeIndex = action.garden_index;
            const newInfo = state.info.filter((_, index) => { return index !== removeIndex });
            return { ...state, info: newInfo };
        
        case 'UPDATE_GARDEN':
            validateGardenAction(action);
            return { ...state, info: state.info.map((gardenInfo, index) => {
                    if (index === action.garden_index) {
                    return { ...gardenInfo, ...action.payload };
                    } else {
                        return gardenInfo;
                    }
                }) 
            }
        
        case 'ADD_NOTIFICATION':
            validateNotificationAction(action);
            return { ...state, info: state.info.map((gardenInfo, index) => {
                    if (index === action.garden_index) {
                        return { ...gardenInfo, notifications: [...gardenInfo.notifications, action.payload] };
                    } else {
                        return gardenInfo;
                    }
                })
            };

        case 'REMOVE_NOTIFICATION':
            validateNotificationAction(action);
            return { ...state, info: state.info.map((gardenInfo, index) => {
                    if (index === action.garden_index) {
                        return { ...gardenInfo, notifications: gardenInfo.notifications.filter((notification) => notification.id !== action.notification_id) };
                    } else {
                        return gardenInfo;
                    }
                })
            };

        case 'UPDATE_NOTIFICATION':
            validateNotificationAction(action);
            return { ...state, info: state.info.map((gardenInfo, index) => {
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
            validateNotificationAction(action);
            return { ...state, info: state.info.map((gardenInfo, index) => {
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

export { initialState, gardenReducer };