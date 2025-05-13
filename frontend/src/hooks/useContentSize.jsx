/**
 * @file useContentSize.jsx
 * @description A custom React hook that calculates and provides the size of a container element.
 * It updates the size dynamically when the window is resized.
 *
 * @param {Object} containerRef - A React ref object pointing to the container element.
 * @returns {Object} An object containing the width and height of the container element.
 */
import { useEffect, useState } from 'react';

const useContentSize = (containerRef) => {
  const [contentSize, setContentSize] = useState({ width: window.innerWidth - 234, height: window.innerHeight - 60 });
    useEffect(() => {
      const handleResize = () => {
        if (containerRef.current) {
          const { width, height } = containerRef.current.getBoundingClientRect();
          setContentSize({ width, height });
        }
      };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [containerRef]);

  return contentSize;
};

export default useContentSize;