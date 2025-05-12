import './styles/generic-btn.css'; 

function CircleButton({className, onClick, text="", Icon}) {
    return (
        <button 
            className={`circle-btn ${className}`} 
            style={{paddingTop: '5px'}}
            onClick={onClick} >
            {text}
            {Icon}
        </button>
    );
    }

export default CircleButton;