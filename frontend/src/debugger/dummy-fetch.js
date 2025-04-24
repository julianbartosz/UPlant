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
 * - `import.meta.env.VITE_GARDENS_API_URL`: Returns a list of gardens with their dimensions and cell structures.
 * - `import.meta.env.VITE_PLANTS_API_URL`: Returns a list of plants with their common names, IDs, and families.
 * - `import.meta.env.VITE_NOTIFICATIONS_API_URL`: Returns a list of grouped notificationsList with details about reminders and associated plants.
 * - `import.meta.env.VITE_USERNAME_API_URL`: Returns a mock username.
 */

const DummyFetch = async (url) => {
    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
    await sleep(1000);

    switch (url) {

        case import.meta.env.VITE_GARDENS_API_URL:
            return {

                data: [
                    { name: 'Bonsai', x: 1, y: 1, cells: [[{ common_name: 'Oak', id: 12, family: 'Fagaceae' }]] },
                ]
            };

        case import.meta.env.VITE_PLANTS_API_URL:
            return { 
                data: [
                    { common_name: 'Rose', id: 4, family: 'Rosaceae' },
                    { common_name: 'Tulip', id: 5, family: 'Liliaceae' },
                    { common_name: 'Orchid', id: 7, family: 'Orchidaceae' },
                    { common_name: 'Cactus', id: 8, family: 'Cactaceae' },
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

        case import.meta.env.VITE_NOTIFICATIONS_API_URL:
            console.log("Fetching notificationsList from dummy data");
            return { 
                data: { 33:
                    [
                        { 
                            name: 'Water', 
                            description: 'Reminds you to water your plants', 
                            interval: 3, 
                            plants: [
                                { common_name: 'Oak', id: 12, family: 'Fagaceae' },
                            ] 
                        },
                        { 
                            name: 'Fertilize', 
                            description: 'Reminds you to fertilize your plants', 
                            interval: 5, 
                            plants: [
                                { common_name: 'Oak', id: 12, family: 'Fagaceae' },
                            ] 
                        },
                        { 
                            name: 'Prune', 
                            description: 'Reminds you to prune your plants', 
                            interval: 7, 
                            plants: [
                                { common_name: 'Oak', id: 12, family: 'Fagaceae' },
                            ] 
                        }
                    ]
                }
            };

        case import.meta.env.VITE_USERNAME_API_URL:
            return { data: 'Johnny Appleseed' };
            
        default:
            return { error: 'Endpoint not found' };
    }
};

export default DummyFetch;
