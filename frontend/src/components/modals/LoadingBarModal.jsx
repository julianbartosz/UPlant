/**
 * @file LoadingBarModal.jsx
 * @description A modal component that displays a loading bar and a spinner animation 
 *              when a loading process is active.
 * 
 * @component
 * @param {Object} props - The props object.
 * @param {boolean} props.loading - A flag indicating whether the loading modal should be displayed.
 * @param {number} props.loadingEstimate - An estimated time in seconds for the loading process.
 * 
 * @returns {JSX.Element} The rendered LoadingBarModal component.
 */
import { LoadingBar } from '../widgets';
import { TailSpin } from 'react-loader-spinner';
import "./styles/generic-modal.css";

const LoadingBarModal = ({ loading, loadingEstimate }) => {
    return (
        <>
        {loading && 
        <div className="modal-overlay" style={{zIndex: 1000}} role="dialog" aria-modal="true" aria-labelledby="modal-message">
            <div className="modal-container">
                <div className="modal-message">
            <LoadingBar isLoading={loading} seconds={loadingEstimate} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', height: '100%', marginBottom: '10px' }}>
            <TailSpin
                height="80"
                width="80"
                color="#4fa94d"
                ariaLabel="tail-spin-loading"
                radius="1"
                visible={true}
            />
            </div>
            </div>
        </div>}
        </>
    );
};

export default LoadingBarModal;