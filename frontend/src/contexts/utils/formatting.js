

const formatGardens = (gardens) => {
    return gardens.map(garden => {
        const { name, size_x, size_y } = garden;
        const cells = Array.from({ length: size_y }, () => Array.from({ length: size_x }, () => null));  
        console.log("Formatted garden:", { name, size_x, size_y, cells });
        return { name: name, x: size_x, y: size_y, cells: cells };
    });
}

export default formatGardens;
