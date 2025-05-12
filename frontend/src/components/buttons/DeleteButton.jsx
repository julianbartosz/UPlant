import { TiDelete } from 'react-icons/ti';
import './styles/generic-btn.css';

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