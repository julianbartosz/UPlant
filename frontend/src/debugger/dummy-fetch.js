/**
 * @file dummy-fetch.js
 * @description Mock data fetch function to simulate fetching data.
 * @async
 * @function DummyFetch
 * @param {string} url 
 * @returns {Promise<Object>}
 * 
 * @throws {Object}
 * 
 * Mock Data Endpoints:
 * - `import.meta.env.VITE__GARDENS_API_URL`: Returns a list of gardens with their dimensions and cell structures.
 * - `import.meta.env.VITE__PLANTS_API_URL`: Returns a list of plants with their common names, IDs, and families.
 * - `import.meta.env.VITE__NOTIFICATIONS_API_URL`: Returns a list of grouped notifications with details about reminders and associated plants.
 * - `import.meta.env.VITE__USERNAME_API_URL`: Returns a mock username.
 */

const DummyFetch = async (url) => {
    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
    await sleep(1000);

    switch (url) {

        case import.meta.env.VITE__GARDENS_API_URL:
            return {

                data: [
                    { name: 'Garden 1', x: 5, y: 10, cells: Array.from({ length: 10 }, () => Array(5).fill(null)) },
                    { name: 'Garden 2', x: 2, y: 7, cells: Array.from({ length: 7 }, () => Array(2).fill(null)) },
                    { name: 'Garden 3', x: 5, y: 5, cells: Array.from({ length: 5 }, () => Array(5).fill(null)) },
                ]
            };

        case import.meta.env.VITE__PLANTS_API_URL:
            return { 
                data: [
                    
                    { common_name: 'Rose', id: 4, family: 'Rosaceae' },
                    { common_name: 'Tulip', id: 5, family: 'Liliaceae' },
                    { common_name: 'Lily', id: 6, family: 'Liliaceae' },
                    { common_name: 'Orchid', id: 7, family: 'Orchidaceae' },
                    { common_name: 'Cactus', id: 8, family: 'Cactaceae' },
                    { common_name: 'Fern', id: 9, family: 'Polypodiopsida' },
                    { common_name: 'Bamboo', id: 10, family: 'Poaceae' },
                    { common_name: 'Maple', id: 11, family: 'Sapindaceae' },
                    { common_name: 'Oak', id: 12, family: 'Fagaceae' },
                    { common_name: 'Pine', id: 13, family: 'Pinaceae' },
                    { common_name: 'Lavender', id: 14, family: 'Lamiaceae' },
                    { common_name: 'Mint', id: 15, family: 'Lamiaceae' },
                    { common_name: 'Sunflower', id: 16, family: 'Asteraceae' },
                    { common_name: 'Daisy', id: 17, family: 'Asteraceae' },
                    { common_name: 'Tomato', id: 18, family: 'Solanaceae' },
                    { common_name: 'Pepper', id: 19, family: 'Solanaceae' },
                    { common_name: 'Strawberry', id: 20, family: 'Rosaceae' },
                    { common_name: 'Blueberry', id: 21, family: 'Ericaceae' }
                ] 
            };

        case import.meta.env.VITE__NOTIFICATIONS_API_URL:
            console.log("Fetching notifications from dummy data");
            return { 
                data: [
                    [
                        { 
                            name: 'Water Reminder', 
                            description: 'Reminds you to water your plants', 
                            interval: 3, 
                            plants: [
                                { common_name: 'Sunflower', id: 1 },
                                { common_name: 'Daisy', id: 2 }
                            ] 
                        },
                        { 
                            name: 'Fertilizer Reminder', 
                            description: 'Reminds you to fertilize your plants', 
                            interval: 5, 
                            plants: [
                                { common_name: 'Tomato', id: 3 }
                            ] 
                        }
                    ],
                    [
                        { 
                            name: 'Pruning Reminder', 
                            description: 'Reminds you to prune your plants', 
                            interval: 7, 
                            plants: [
                                { common_name: 'Sunflower', id: 1 }
                            ] 
                        },
                        { 
                            name: 'Pest Control Reminder', 
                            description: 'Reminds you to check for pests', 
                            interval: 10, 
                            plants: [
                                { common_name: 'Daisy', id: 2 },
                                { common_name: 'Tomato', id: 3 }
                            ] 
                        }
                    ],
                    [
                        { 
                            name: 'Repotting Reminder', 
                            description: 'Reminds you to repot your plants', 
                            interval: 30, 
                            plants: [
                                { common_name: 'Sunflower', id: 1 },
                                { common_name: 'Tomato', id: 3 }
                            ] 
                        },
                        { 
                            name: 'Harvest Reminder', 
                            description: 'Reminds you to harvest your plants', 
                            interval: 15, 
                            plants: [
                                { common_name: 'Daisy', id: 2 }
                            ] 
                        }
                    ]
                ] 
            };

        case import.meta.env.VITE__USERNAME_API_URL:
            return { data: 'Johnny Appleseed' };
            
        default:
            return { error: 'Endpoint not found' };
    }
};

export default DummyFetch;
