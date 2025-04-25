// SpinnerLoader.tsx
import { motion } from "framer-motion";
import React from "react";
import { FidgetSpinner } from "react-loader-spinner";
// import "./styles/spinner.css";

export default function FidgetLoading() {

    const spinnerVariants = {
        initial: { opacity: 0 },
        animate: { opacity: 1   , transition: { duration: 0.5 } },
    };
    return (
        <div  style={{ backgroundColor: 'transparent', background: 'transparent' }}>
            
       
            <FidgetSpinner
  visible={true}
  height="80"
  width="80"
  ariaLabel="fidget-spinner-loading"
  wrapperStyle={{}}
  wrapperClass="fidget-spinner-wrapper"
  />
   
        </div>

        
    );
}