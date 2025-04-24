function patchGarden(newGarden, oldGarden) {
    const patchBody = {};
    if (newGarden.id !== oldGarden.id) {
        throw new Error("Cannot patch garden with different IDs");
    }
    if (newGarden.name !== oldGarden.name) {
        patchBody.name = newGarden.name;
    }
    if (newGarden.size_x !== oldGarden.size_x) {
        patchBody.size_x = newGarden.size_x;
    }
    if (newGarden.size_y !== oldGarden.size_y) {
        patchBody.size_y = newGarden.size_y;
    }
    return patchBody;
}

export default patchGarden;