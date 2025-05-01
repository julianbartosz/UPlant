

const formatGardens = (gardens) => {
    return gardens.map(garden => {
        const { id, name, size_x, size_y, garden_logs } = garden;
        let cells = Array.from({ length: size_y }, () => Array.from({ length: size_x }, () => null));  
        for (const log of garden_logs) {
            const { x_coordinate, y_coordinate, planted_date, id: logId, plant_details: plant } = log;
            cells[y_coordinate][x_coordinate] = { logId, planted_date, ...plant };
        }
        console.log("Formatted garden:", { id, name, size_x, size_y, cells });
        return { id: id, name: name, x: size_x, y: size_y, cells: cells };
    });
}

const formatNotifications = (notificationsData) => { 
    // let gardenId = notificationsData['garden_id'];
    // let notifications = notificationsData[0]['notifications']
    // return 
    
    // });
    return null;
}

export { formatGardens, formatNotifications };