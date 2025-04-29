import { useEffect, useState } from 'react';
import { useContext } from 'react';
import { UserContext } from '../context/UserProvider';

const useContentSize = (containerRef) => {
  const {gardens} = useContext(UserContext);
const [contentSize, setContentSize] = useState({ width: window.innerWidth - 234, height: window.innerHeight - 60 });
  useEffect(() => {
    console.log("ISIDE")
    const handleResize = () => {
      if (containerRef.current) {
        console.log("RESIZE")
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