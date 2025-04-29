import { useContext } from 'react';
import { useGardens } from '../../hooks/useGardens';
import { AddButton, DeleteButton, GardenButton } from '../buttons';
import { UserContext } from '../../context/UserProvider';

import './styles/garden-bar.css';

const GardenBar = ({ selectedGardenIndex, setSelectedGardenIndex, dynamic = true, style = {}, onAdd }) => {
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

        const rollback = { ...gardens[index] };

        // Optimistically update
        dispatch({ type: 'REMOVE_GARDEN', garden_index: index });

        const gardenUrl = `${import.meta.env.VITE_GARDENS_API_URL}${gardens[index].id}/`;
        console.log(`Deleting garden at ${gardenUrl}`);
        
        (async () => {
            try {
                const response = await fetch(gardenUrl, {
                    method: 'DELETE',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });
                if (!response.ok) {
                    // Rollback if the request fails
                    dispatch({ type: 'ADD_GARDEN', garden_index: index, payload: rollback });
                    alert("Failed to delete garden. Please try again.");
                } else {
                    console.log(`Garden deleted successfully.`);
                }
    
            } catch (error) {
                console.error("Error deleting garden:", error);
                // Rollback if the request fails
                dispatch({ type: 'ADD_GARDEN', garden_index: index, payload: rollback });
                alert(error.message);
            }
        })();
    };

    return (
        <div className="garden-bar-container" style={style}>
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