import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const LoadingAnimation = ({ redirect }) => {
    const navigate = useNavigate();
    const videoRef = useRef();

    const styles = {
        container: {
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            backgroundColor: 'black',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 99999,
        },

        video: {
            width: '100%',
            height: '100%',
            objectFit: 'cover',
        },
    };

    useEffect(() => {
        const timer = setTimeout(() => {
            navigate(redirect); 
        }, 2500);

        return () => clearTimeout(timer);
    }, [navigate, redirect]);

    useEffect(() => {
        if (videoRef.current) {
            videoRef.current.playbackRate = 4;
        }
    }, []);


    console.log('LoadingAnimation component rendered');
    
    return (
        <div style={styles.container}>
            <video ref={videoRef} style={styles.video} autoPlay loop muted playbackRate={2}>
                <source src="/app/plants-loading.mp4" type="video/mp4" />
                Your browser does not support the video tag.
            </video>
        </div>
    );
};

export default LoadingAnimation;