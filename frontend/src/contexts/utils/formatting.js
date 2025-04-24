

const formatGardens = (gardens) => {
    return gardens.map(garden => {
        const { id, name, size_x, size_y } = garden;
        const cells = Array.from({ length: size_y }, () => Array.from({ length: size_x }, () => null));  
        console.log("Formatted garden:", { id, name, size_x, size_y, cells });
        return { id: id, name: name, x: size_x, y: size_y, cells: cells };
    });
}


export default formatGardens;
