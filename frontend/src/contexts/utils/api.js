const jsonifyGarden = (name, x, y) => {
    return JSON.stringify({
        name: name,
        size_x: x,
        size_y: y,
    });
}

// Body for new notifications
const jsonifyNotification = (gardenId, name, interval) => {
    return JSON.stringify({
        gardenId: gardenId,
        name: name,
        interval: interval,
        type: "Other",
    });
}

// Body for new plants
const jsonifyPlantAssociation = (name, family, type, subtype) => {
    return JSON.stringify({
        name: name,
        family: family,
        type: type,
        subtype: subtype,
    });
}


