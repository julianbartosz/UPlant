import { TiPlus } from 'react-icons/ti';
import './styles/generic-btn.css';

function AddButton({ onClick, style }) {
    return (
        <button 
            className='no-style-btn'
            onClick={onClick} 
            style={style} >
            <TiPlus className={'add-garden-btn'} />
        </button>
    );
}

export default AddButton;