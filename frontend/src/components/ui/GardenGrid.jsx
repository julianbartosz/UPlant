import { ICONS } from "../../constants";
import { 
    FaArrowUp, 
    FaArrowDown, 
    FaArrowLeft, 
    FaArrowRight 
} from "react-icons/fa";
import { CircleButton } from "../buttons";
import { Tooltip } from "react-tooltip";
import { useGardens } from "../../hooks";
import "./styles/garden-grid.css"

const GardenGrid = ({
    garden, 
    fontSize, 
    squareSize,
    contentSize,
    interactive = true,
    selectedEmptyCells = null, 
    selectedPlantCells = null,
    cellClickHandler = null,
    coloredCells = null
}) => {

    if (!garden) {  
        return (null);
    }
    
    const { mediateGridSizeChange } = useGardens();

    const isSelectedEmpty = (i, j) => selectedEmptyCells && selectedEmptyCells.has(`${i}-${j}`);
    const isSelectedPlant = (i, j) => selectedPlantCells && selectedPlantCells.has(`${i}-${j}`);
    const isColored = (i, j) => coloredCells && coloredCells.has(`${i}-${j}`);
    
    return (
        <div className={ interactive ? "garden-grid-container" : "garden-grid-container-static" } style={{height: `${contentSize}px`}}>
                <div 
                    className="grid-container" 
                    style={{
                    width: `${squareSize * garden.x}px`, 
                    height: `${squareSize * garden.y}px`,
                }}
                 >
        <div 
        className="grid" 
        style={{
        gridTemplateColumns: `repeat(${garden.x}, ${squareSize}px)`, 
        gridTemplateRows: `repeat(${garden.y}, ${squareSize}px)`,
        }}>

       { garden.cells.map((row, i) => (
                    row.map((item, j) => (
                        <div  key={`${i}-${j}`} data-tooltip-id="my-tooltip" data-tooltip-content={item ? item['common_name'] : ""}>
                            <div
                                className={`${isColored(i, j) ? 'needs-care' : 'square'} ${isSelectedEmpty(i, j) ? 'selected' : ''} ${isSelectedPlant(i, j) ? 'selected-shear' : ''}`}
                                style={{ 
                                    fontSize: `${fontSize}px`,
                                 
                                }}
                                onClick={() => {cellClickHandler && cellClickHandler(item, i, j)}}
                            >
                                {item ? (ICONS[item.family] || ICONS['default']) : ""}
                            </div>
                        </div>
                    ))
                ))}

            <Tooltip id="my-tooltip" style={{ zIndex: 9999 }}/>
            {interactive && (
                <>
                    <div style={{ position: "absolute", top: "-20px", left: "50%", transform: "translateX(-50%)", zIndex: -0.5, display: "flex" }}>
                        {/* Top Center Button */}
                        <CircleButton text={<FaArrowUp />} className="grid-add-btn" onClick={() => mediateGridSizeChange('y', 1, "top", garden.name)} />
                        <CircleButton text={<FaArrowDown />} className="grid-remove-btn" onClick={() => mediateGridSizeChange('y', -1, "top", garden.name)} />
                    </div>
                    <div style={{
                        position: "absolute",
                        top: "50%", left: "-20px",
                        transform: "translateY(-50%)",
                        zIndex: 1,
                        display: "flex",
                        flexDirection: "column",
                        justifyContent: "center",
                    }}>
                        {/* Left Center Button */}
                        <CircleButton text={<FaArrowRight />} className="grid-remove-btn" onClick={() => mediateGridSizeChange('x', -1, "left", garden.name)} />
                        <CircleButton text={<FaArrowLeft />} className="grid-add-btn" onClick={() => mediateGridSizeChange('x', 1, "left", garden.name)} />
                    </div>
                    <div style={{
                        position: "absolute",
                        top: "50%", right: "-20px",
                        transform: "translateY(-50%)",
                        zIndex: 1,
                        display: "flex",
                        flexDirection: "column",
                        justifyContent: "center",
                    }}>
                        {/* Right Center Button */}
                        <CircleButton text={<FaArrowLeft />} className="grid-remove-btn" onClick={() => mediateGridSizeChange('x', -1, "right", garden.name)} />
                        <CircleButton text={<FaArrowRight />} className="grid-add-btn" onClick={() => mediateGridSizeChange('x', 1, "right", garden.name)} />
                    </div>
                    <div style={{ position: "absolute", bottom: "-20px", left: "50%", transform: "translateX(-50%)", zIndex: 1, display: "flex" }}>
                        {/* Bottom Center Button */}
                        <CircleButton text={<FaArrowDown />} className="grid-add-btn" onClick={() => mediateGridSizeChange('y', 1, "bottom", garden.name)} />
                        <CircleButton text={<FaArrowUp />} className="grid-remove-btn" onClick={() => mediateGridSizeChange('y', -1, "bottom", garden.name)} />
                    </div>
                </>
            )}
                
                
                     </div>
            
                </div>
        </div>

    )
}

export default GardenGrid;

