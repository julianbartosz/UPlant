import React from 'react';
import { TiDelete } from 'react-icons/ti';
import './styles/btn-styles.css';

function DeleteButton({ onClick }) {
    return (
      <button 
        className='no-style-btn'
        onClick={onClick}  >
        <TiDelete className={"delete-garden-btn"}/>
      </button>
    );
  }

  export default DeleteButton;