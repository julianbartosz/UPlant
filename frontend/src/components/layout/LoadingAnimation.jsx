import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const LoadingAnimation = ({ redirect }) => {
    const navigate = useNavigate();
    const videoRef = useRef();

    useEffect(() => {
        const timer = setTimeout(() => {
            navigate(redirect); 
        }, 2500);
        return () => clearTimeout(timer);
    }, [redirect]);

    useEffect(() => {
        if (videoRef.current) {
            videoRef.current.playbackRate = 4;
        }
    }, []);

    const handleVideoLoaded = () => {
        setIsLoaded(true);
    };

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
        attribution: {
            position: 'absolute',
            bottom: '10px',
            right: '10px',
            color: 'white',
            fontSize: '12px',
        },
    };

    return (
        <div style={styles.container}>
            <video 
                ref={videoRef} 
                style={styles.video} 
                autoPlay 
                loop 
                muted 
                onLoadedData={handleVideoLoaded}
            >
                <source src="/app/plants-loading.mp4" type="video/mp4" />
                Your browser does not support the video tag.
            </video>
            <div style={styles.attribution}>
                <a 
                    href="https://www.vecteezy.com/free-videos/animated-plants" 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    style={{ color: 'white', textDecoration: 'none' }}
                >
                    Animated Plants Stock Videos by Vecteezy
                </a>
            </div>
        </div>
    );
};

export default LoadingAnimation;