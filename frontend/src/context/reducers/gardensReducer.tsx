const initialState = null;

// Validation to aid in debugging
function validate(state: any, action: any): void {
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
            break;

        case 'REMOVE_NOTIFICATION':
            if (action.notification_id === undefined) {
                throw new Error("Notification id is required for REMOVE_NOTIFICATION action");
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
function gardensReducer(state: Garden[] | any, action: Action): Garden[] {
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
            let processedGardens = action.payload.map((garden) => {
                return {
                    ...formatGarden(garden),
                    notifications: garden.notifications.map((notification) => {
                        return formatNotification(notification);
                    }),
                };
            });

            return [...processedGardens];

        case 'ADD_GARDEN_LOGS':
            const logs = [...action.payload];

            const newwState = state.map((garden, index) => {
                if (index === action.garden_index) {
                    let cells = [...garden.cells];
                    console.log("Cells: ", cells);
                    for (const log of logs) {
                        const { x_coordinate, y_coordinate } = log;
                        cells[y_coordinate][x_coordinate] = formatGardenLog(log);
                    }
                    return { ...garden, cells: cells };
                } else {
                    return garden;
                }
            });

            return newwState;

        case 'PATCH_CELLS':
            const updatedState = state.map((garden, index) => {
                if (index === action.garden_index) {
                    return { ...garden, cells: action.payload };
                } else {
                    return garden;
                }
            });
            return updatedState;

        case 'REMOVE_GARDEN':
            const removeIndex = action.garden_index;
            const newGardens = state.filter((_, index) => {
                return index !== removeIndex;
            });
            return newGardens;

        case 'UPDATE_GARDEN':
            return state.map((garden, index) => {
                return index === action.garden_index ? { ...garden, ...action.payload } : garden;
            });

        case 'ADD_NOTIFICATION':
            return state.map((garden, index) => {
                if (index === action.garden_index) {
                    return {
                        ...garden,
                        notifications: [...garden.notifications, formatNotification(action.payload)],
                    };
                } else {
                    return garden;
                }
            });

        case 'REMOVE_NOTIFICATION':
            return state.map((gardenInfo, index) => {
                if (index === action.garden_index) {
                    return {
                        ...gardenInfo,
                        notifications: gardenInfo.notifications.filter(
                            (notification) => notification.id !== action.notification_id
                        ),
                    };
                } else {
                    return gardenInfo;
                }
            });

        case 'UPDATE_NOTIFICATION':
            return {
                ...state,
                info: state.map((gardenInfo, index) => {
                    if (index === action.garden_index) {
                        return {
                            ...gardenInfo,
                            notifications: gardenInfo.notifications.map((notification) => {
                                if (notification.id === action.notification_id) {
                                    return { ...notification, ...action.payload };
                                } else {
                                    return notification;
                                }
                            }),
                        };
                    } else {
                        return gardenInfo;
                    }
                }),
            };

        case 'UPDATE_NOTIFICATIONS':
            return {
                ...state,
                info: state.map((gardenInfo, index) => {
                    if (index === action.garden_index) {
                        return { ...gardenInfo, notifications: action.payload };
                    } else {
                        return gardenInfo;
                    }
                }),
            };

        default:
            throw new Error(`Unsupported action type: ${action.type}`);
    }
}

// Translates to reducer expectation from raw response
const formatGarden = (garden: any): Garden => {
    if (garden.cells && garden.cells.length > 0) {
        return garden;
    }

    const { size_x, size_y, garden_logs } = garden;
    garden.cells = Array.from({ length: size_y }, () =>
        Array.from({ length: size_x }, () => null)
    );
    for (const log of garden_logs) {
        const { x_coordinate, y_coordinate } = log;
        garden.cells[y_coordinate][x_coordinate] = formatGardenLog(log);
    }
    garden.notifications = garden.notifications || [];
    return {
        name: garden.name || null,
        cells: garden.cells || [],
        notifications: garden.notifications || [],
        total_plants: garden.total_plants || 0,
        id: garden.id || null,
        created_at: garden.created_at || null,
        size_x: garden.size_x || null,
        size_y: garden.size_y || null,
    };
};

const formatNotification = (notification: any): Notification => {
    const { id, name, interval, type, subtype, next_due } = notification;

    const plant_names = notification.plants
        ? notification.plants.map((plant: any) => plant.plant_details.common_name)
        : [];

    return {
        id: id,
        name: name,
        interval: interval,
        type: type,
        plant_names: plant_names || [],
        subtype: subtype || null,
        next_due: next_due || null,
    };
};

const formatGardenLog = (log: any): GardenLog => {
    const { id, x_coordinate, y_coordinate, planted_date, plant_details } = log;
    const plant_detail = formatPlantDetail(plant_details);
    return {
        id: id,
        plant_detail: plant_detail,
        x_coordinate: x_coordinate,
        y_coordinate: y_coordinate,
        planted_date: planted_date || null,
    };
};

const formatPlantDetail = (plant: any): PlantDetail => {
    const { id, common_name, family } = plant;
    return { id: id, name: common_name, family: family || null };
};

// Types for the reducer
type PlantDetail = {
    id: number;
    name: string;
    family: string;
};

type Notification = {
    id: number;
    name: string;
    interval: number;
    type: string;
    plant_names: string[];
    subtype?: string;
    next_due?: string;
};

type GardenLog = {
    id: number;
    plant_detail: PlantDetail;
    x_coordinate: number;
    y_coordinate: number;
    planted_date?: string;
};

type Garden = {
    id: number;
    name: string;
    size_x: number;
    size_y: number;
    cells: GardenLog[][];
    total_plants?: number;
    notifications?: Notification[];
    created_at?: string;
};

type Action = {
    type: string;
    garden_index?: number;
    payload?: any;
    notification_id?: number;
};

export { gardensReducer, initialState, validate };