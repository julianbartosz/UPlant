import React from 'react';
import { TiPlus } from 'react-icons/ti';
import './styles/btn-styles.css';

function AddButton({ onClick }) {
    return (
        <button 
            className='no-style-btn'
            onClick={onClick} >
            <TiPlus className={'add-garden-btn'}/>
        </button>
    );
}

export default AddButton;