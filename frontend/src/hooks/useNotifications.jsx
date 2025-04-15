import { useEffect, useState } from 'react';



const useNotifications = () => {

    const [notifications, setNotifications] = useState(null);

    useEffect(() => {
        // Fetch notifications from an API or other source
        const fetchedNotifications = [[
            {
                id: 1,
                name: 'Alice',
                plants: [
                    { id: 101, name: 'Fern' },
                    { id: 102, name: 'Cactus' },
                ],
                interval: 7,
            },
            {
                id: 2,
                name: 'Bob',
                plants: [
                    { id: 103, name: 'Bamboo' },
                ],
                interval: 14,
            },
            {
                id: 3,
                name: 'Charlie',
                plants: [
                    { id: 104, name: 'Palm' },
                    { id: 105, name: 'Orchid' },
                ],
                interval: 69,
            },
            {
                id: 4,
                name: 'David',
                plants: [
                    { id: 106, name: 'Rose' },
                ],
                interval: 21,
            },
            {
                id: 5,
                name: 'Eve',
                plants: [
                    { id: 107, name: 'Tulip' },
                ],
                interval: 30,
            },
            
        ], [
            {
                id: 6,
                name: 'Frank',
                plants: [
                    { id: 108, name: 'Daisy' },
                ],
                interval: 14,
            },
            {
                id: 7,
                name: 'Grace',
                plants: [
                    { id: 109, name: 'Lily' },
                ],
                interval: 7,
            },
            {
                id: 8,
                name: 'Heidi',
                plants: [
                    { id: 110, name: 'Sunflower' },
                ],
                interval: 14,
            },
            {
                id: 9,
                name: 'Ivan',
                plants: [
                    { id: 111, name: 'Daffodil' },
                ],
                interval: 30,
            },
            {
                id: 10,
                name: 'Judy',
                plants: [
                    { id: 112, name: 'Marigold' },
                ],
                interval: 21,
            }],[]];

        setNotifications(fetchedNotifications);
    }
    , []);

    const addNotification = (notification) => {
        setNotifications((prev) => [...prev, notification]);
    };

    return { notifications, addNotification };
};

export default useNotifications;