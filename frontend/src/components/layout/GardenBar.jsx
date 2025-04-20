import { useGardens } from '../../hooks/useGardens';
import { AddButton, DeleteButton, GardenButton } from '../buttons';
import './styles/garden-bar.css';

const GardenBar = ({ selectedGardenIndex, setSelectedGardenIndex, dynamic = true, style = {} }) => {
    const { gardens, mediateAddGarden, mediateDeleteGarden, mediateRenameGarden } = useGardens();

    if (!gardens) {
        return <div className="garden-bar">No gardens available.</div>;
    }

    return (
        <div className="garden-bar-container" style={style}>
        <div className="garden-bar">
            {dynamic && (
                <div className="garden-bar-item" key={-1}>
                    <AddButton
                        onClick={() => {
                            mediateAddGarden(setSelectedGardenIndex);
                        }}
                    />
                </div>
            )}
            {gardens.map((garden, index) => (
                <div className="garden-bar-item" key={index}>
                    {dynamic && (
                        <DeleteButton
                            onClick={() => {
                                console.log("Deleting garden...");
                                if (gardens.length <= 1) {
                                    alert("You cannot delete the last garden.");
                                    return;
                                }
                                mediateDeleteGarden(index);
                                if (selectedGardenIndex === index) {
                                    setSelectedGardenIndex(0);
                                } else if (selectedGardenIndex > index) {
                                    setSelectedGardenIndex(selectedGardenIndex - 1);
                                }
                            }}
                        />
                    )}
                    <GardenButton
                        onRightClick={(e) => {
                            e.preventDefault();
                            if (dynamic) mediateRenameGarden(index);
                        }}
                        onLeftClick={() => {
                            setSelectedGardenIndex(index);
                        }}
                        text={garden.name}
                        style={{
                            
                            backgroundColor: selectedGardenIndex === index ? 'green' : 'lightgreen',
                        }}
                    />
                </div>
            ))}
        </div>
        </div>
    );
};

export default GardenBar;