// frontend/src/components/NavBarSection/NavBar.jsx

import React from 'react';
import { FaCog } from 'react-icons/fa';
import { useUser } from '../../contexts/ProtectedRoute';

const NavBar = ({user}) => {

    return (
        <div className="navbar" style={{
            position: 'fixed', top: 0, left: 0, width: '100%', height: '60px',
            background: 'white', display: 'flex', alignItems: 'center', padding: '0 20px',
            zIndex: 10, justifyContent: 'space-between'
        }}>
            <div>
                <button style={{ width: '180px', borderWidth: '1px',borderColor: 'black', background: 'lightgreen', marginLeft: '0px', color: 'black'}}>Browse Catalog</button>
                <button style={{ borderWidth: '1px',borderColor: 'black', background:  'grey', marginLeft: '50px', color: 'black'}}>Community Portal</button>
            </div>

            <h1 style={{fontFamily:'Brush Script MT', color: 'black', fontSize: '50px',fontWeight: 'bold'}}>UPlant</h1>
            <div style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{ color: 'black', fontSize: '20px', marginRight: '50px', border: '1px dotted gray', padding: '0 10px' }}>
                    {user.username}
                </div>
                <FaCog style={{ color: 'black', fontSize: '50px', cursor: 'pointer', marginRight: '30px' }} />
            </div>
        </div>
    );
    
};

export default NavBar;