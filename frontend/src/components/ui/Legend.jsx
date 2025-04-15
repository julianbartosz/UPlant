import React from 'react';

const Legend = ({ items }) => {
    
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {items.map((item, index) => (
                <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                        style={{
                            display: 'inline-block',
                            width: '16px',
                            height: '16px',
                            borderRadius: '50%',
                            backgroundColor: item.color,
                        }}
                    ></span>
                    <span>{item.name}</span>
                </div>
            ))}
        </div>
    );
};


export default Legend;