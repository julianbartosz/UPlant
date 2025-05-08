import TextButton from './TextButton';
import './styles/generic-btn.css';

function BackButton({ onClick }) {
    return (
        <TextButton
            text="← Back"
            className="back-btn"
            style={{borderRadius: '5px'}}
            onLeftClick={onClick}
            onRightClick={(e) => {
                e.preventDefault();
                onClick(e);
            }}
        />
    );
}           

export default BackButton;