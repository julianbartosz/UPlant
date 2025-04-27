// SpinnerLoader.tsx
import { motion } from "framer-motion";
import React from "react";
import { Grid } from "react-loader-spinner";
import "./styles/spinner.css";

export default function GridLoading() {
    const spinnerVariants = {
        initial: { opacity: 0 },
        animate: { opacity: 1   , transition: { duration: 0.5 } },
    };
    return (
        <div className="spinner-wrapper">
            
        <motion.div
            className="spinner-container"
            variants={spinnerVariants}
            initial="initial"
            animate="animate"
        >
            <Grid
                height="80"
                width="80"
                color="#4fa94d"
                ariaLabel="grid-loading"
                radius="12.5"
                wrapperStyle={{}}
                wrapperClass=""
                visible={true}
            />
        </motion.div>
        </div>

        
    );
}