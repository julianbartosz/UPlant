import React from 'react';
import { LoadingBar } from '../widgets'; // Adjust the path if necessary
import { TailSpin } from 'react-loader-spinner'; // Ensure you have this package installed
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