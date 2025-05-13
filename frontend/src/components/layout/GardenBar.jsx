/**
 * @file GardenBar.jsx
 * @description Component for displaying and managing a bar of garden buttons with add and delete functionality.
 */
import { useContext, useState } from 'react';
import { AddButton, DeleteButton, GardenButton } from '../buttons';
import { UserContext } from '../../context/UserProvider';
import { BASE_API, DEBUG } from '../../constants';
import { ErrorModal } from '../modals';
import './styles/garden-bar.css';

/**
 * Deletes a garden by sending a DELETE request to the API.
 * @param {number} index
 * @param {Array} gardens
 * @param {Function} dispatch
 * @param {Function} setError
 */
const deleteGarden = async (index, gardens, dispatch, setError) => {
    if (DEBUG) console.log(`Attempting to delete garden at index: ${index}`);

    if (gardens.length <= 1) {
        setError("You cannot delete the last garden.");
        if (DEBUG) console.log("Delete operation aborted: Only one garden left.");
        return;
    }

    if (!window.confirm("Are you sure you want to delete this garden?")) {
        if (DEBUG) console.log("Delete operation canceled by user.");
        return { success: false };
    }

    const gardenUrl = `${BASE_API}/gardens/gardens/${gardens[index].id}/`;

    try {
        if (DEBUG) console.log(`Sending DELETE request to: ${gardenUrl}`);
        const response = await fetch(gardenUrl, {
            method: 'DELETE',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok) {
            setError("Failed to delete garden. Please try again.");
            if (DEBUG) console.error("Failed to delete garden. Response:", response);
            return { success: false };
        } else {
            if (DEBUG) console.log("Garden deleted successfully.");
        }
    } catch (error) {
        console.error("Error deleting garden:", error);
        setError(error.message);
        return;
    } finally {
        dispatch({ type: 'REMOVE_GARDEN', garden_index: index });
        if (DEBUG) console.log(`Dispatched REMOVE_GARDEN action for index: ${index}`);
    }
};

const GardenBar = ({ selectedGardenIndex, setSelectedGardenIndex, dynamic = true, style = {}, onAdd, centered = false }) => {
    const { gardens, dispatch, loading } = useContext(UserContext);
    const [error, setError] = useState(null);

    if (DEBUG) console.log("GardenBar rendered with props:", { dynamic, style, centered });

    if (loading) {
        if (DEBUG) console.log("GardenBar is loading...");
        return null;
    }

    return (
        <>
            <ErrorModal
                isOpen={!!error}
                onClose={() => setError(null)}
                message={error}
            />
            <div
                className="garden-bar-container"
                style={{ ...style, display: 'flex', justifyContent: centered ? 'center' : 'flex-start' }}
            >
                <div className="garden-bar">
                    {dynamic && (
                        <div className="garden-bar-item" key={-1}>
                            <AddButton
                                onClick={() => {
                                    if (DEBUG) console.log("AddButton clicked.");
                                    onAdd();
                                }}
                            />
                        </div>
                    )}
                    {!loading &&
                        gardens.map((garden, index) => (
                            <div className="garden-bar-item" key={index}>
                                {dynamic && (
                                    <DeleteButton
                                        onClick={async () => {
                                            if (DEBUG) console.log(`DeleteButton clicked for garden at index: ${index}`);
                                            const result = await deleteGarden(index, gardens, dispatch, setError);
                                            if (DEBUG) console.log("Delete operation completed.");
                                            if (result && result.success === false) {
                                                return;
                                            }
                                            if (selectedGardenIndex === index) {
                                                setSelectedGardenIndex(0);
                                                if (DEBUG) console.log("Selected garden index reset to 0.");
                                            } else if (selectedGardenIndex > index) {
                                                setSelectedGardenIndex(selectedGardenIndex - 1);
                                                if (DEBUG) console.log("Selected garden index decremented.");
                                            }
                                        }}
                                    />
                                )}
                                <GardenButton
                                    onRightClick={(e) => {
                                        e.preventDefault();
                                        if (dynamic) {
                                            if (DEBUG) console.log(`Right-clicked on garden at index: ${index}`);
                                            mediateRenameGarden(index);
                                        }
                                    }}
                                    onLeftClick={() => {
                                        setSelectedGardenIndex(index);
                                        if (DEBUG) console.log(`Garden at index ${index} selected.`);
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
        </>
    );
};

export default GardenBar;
