import { useState, useEffect, useRef } from 'react';
import "./styles/bar.css";

function LoadingBar({ seconds, isLoading }) {
    const [width, setWidth] = useState(0);
    const [completed, setCompleted] = useState(false);
    const timerRef = useRef(null);

    useEffect(() => {
        const sec = parseFloat(seconds);

        if (isLoading) {
            setCompleted(false);
            setWidth(0);

            // Start progress to 100% over `seconds`
            requestAnimationFrame(() => {
                setWidth(100);
            });

            // When the duration is over, set it as completed
            if (sec > 0) {
                timerRef.current = setTimeout(() => {
                    setCompleted(true);
                }, sec * 1000);
            } else {
                // If seconds is 0 or invalid, skip animation
                setWidth(100);
                setCompleted(true);
            }
        }

        return () => {
            clearTimeout(timerRef.current);
        };
    }, [isLoading, seconds]);

    const shouldShowBar = isLoading || (completed && isLoading !== undefined);

    return (
        shouldShowBar && (
            <div className="container">
                <div className="loading-bar-container">
                    <div
                        className="loading-bar"
                        style={{
                            width: `${width}%`,
                            transition: isLoading && !completed ? `width ${seconds}s linear` : 'none'
                        }}
                    ></div>
                </div>
            </div>
        )
    );
}

export default LoadingBar;
