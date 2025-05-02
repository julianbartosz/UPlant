import { useContext } from 'react';
import { useGardens } from '../../hooks/useGardens';
import { AddButton, DeleteButton, GardenButton } from '../buttons';
import { UserContext } from '../../context/UserProvider';

import './styles/garden-bar.css';

const GardenBar = ({ selectedGardenIndex, setSelectedGardenIndex, dynamic = true, style = {}, onAdd, centered=false }) => {
    const { gardens, dispatch, loading } = useContext(UserContext);
    
    if (loading) {
        return null;
    }

    const handleDeleteGarden = (index) => {
        if (gardens.length <= 1) {
            alert("You cannot delete the last garden.");
            return;
        }
        if (!window.confirm("Are you sure you want to delete this garden?")) {
            return;
        }

        const gardenUrl = `http://localhost:8000/api/gardens/gardens/${gardens[index].id}/`;
        console.log(`Deleting garden at ${gardenUrl}`);
    
        (async () => {
            try {
                const response = await fetch(gardenUrl, {
                    method: 'DELETE',
                    credentials: 'include',
                    headers: {
                        // 'Authorization': `Token 4c1775be909a3873ee6c23104d433adaf4cbde29`,
                        'Content-Type': 'application/json',
                    },
                });
                if (!response.ok) {
                    alert("Failed to delete garden. Please try again.");
                    return;
                } else {
                    console.log(`Garden deleted successfully.`)
                }
    
            } catch (error) {
                console.error("Error deleting garden:", error);
                alert(error.message);
                return;
            } finally {
                dispatch({ type: 'REMOVE_GARDEN', garden_index: index });
            }
        })();
    };

    return (
        <div className="garden-bar-container" style={{ ...style, display: 'flex', justifyContent: centered ? 'center' : 'flex-start' }}>
        <div className="garden-bar">
            {dynamic && (
                <div className="garden-bar-item" key={-1}>
                    <AddButton
                        onClick={() => {
                            onAdd();
                        }}
                    />
                </div>
            )}
            {!loading && gardens.map((garden, index) => (
                <div className="garden-bar-item" key={index}>
                    {dynamic && (
                        <DeleteButton
                            onClick={() => {
                                console.log("Deleting garden...");
                                if (gardens.length <= 1) {
                                    alert("You cannot delete the last garden.");
                                    return;
                                }
                                handleDeleteGarden(index);
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
                            color: 'black',
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