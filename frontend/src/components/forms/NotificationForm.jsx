import React from 'react';
import AddWithOptions from '../ui/AddWithOptions';
import { GenericButton } from '../buttons';

const NotificationForm = ({onBack}) => {

    const [selectedPlants, setSelectedPlants] = React.useState(new Set());

    const handlePlantSelection = (selected) => { 
        console.log("Selected plants:", selected);
        setSelectedPlants(new Set(selected));
    };

    return (
        <div style={{ fontFamily: 'Arial, sans-serif', fontSize: '14px', color: '#333', display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
            <div style={{ width: '100%' }}>
                <div style={{ marginBottom: '20px' }}>
                    <GenericButton label="Cancel" onClick={onBack} style={{ backgroundColor: 'red', marginTop: '10px'}} />
                </div>
                <label
                    htmlFor="affected-plants"
                    style={{
                        marginBottom: '29px',
                        color: 'white',
                        fontFamily: 'cursive',
                    }}
                >
                    Affected Plants:
                </label>
                <AddWithOptions handleSelection={handlePlantSelection}/> {/* Updated to handleSelection */}
                <div style={{ marginTop: '15px',marginBottom: '10px', display: 'flex', flexDirection: 'column' }}>

                <label
                        htmlFor="name"
                        style={{
                            marginBottom: '5px',
                            color: 'white',
                            fontFamily: 'cursive',
                        }}
                    >
                        Name:
                    </label>
                    <div style={{ display: 'flex', flexDirection: 'column', width: '100%', alignItems: 'center' }}>
                        <input
                            type="text"
                            id="name"
                            name="name"
                            style={{
                                padding: '8px',
                                border: '1px solid #ccc',
                                borderRadius: '4px',
                                boxSizing: 'border-box',
                                width: '200px',
                                marginBottom: '15px',
                            }}
                        />
                    </div>
                    <label
                        htmlFor="interval"
                        style={{
                            marginBottom: '5px',
                            color: 'white',
                            fontFamily: 'cursive',
                        }}
                    >
                        Interval:
                    </label>
                    <div style={{ display: 'flex', flexDirection: 'column', width: '100%', alignItems: 'center' }}>
                        <input
                            type="number"
                            id="interval"
                            name="interval"
                            style={{
                                padding: '8px',
                                border: '1px solid #ccc',
                                borderRadius: '4px',
                                boxSizing: 'border-box',
                                width: '200px',
                                marginBottom: '15px'
                            }}
                        />
                    </div>
                </div>
                <GenericButton label="Submit" />
            </div>
        </div>
    );
};

export default NotificationForm;
