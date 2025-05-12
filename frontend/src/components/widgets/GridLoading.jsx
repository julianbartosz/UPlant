/**
 * @file GridLoading.jsx
 * @description A React component that displays a loading spinner with animation using Framer Motion and react-loader-spinner.
 */

import { motion } from "framer-motion";
import { Grid } from "react-loader-spinner";
import "./styles/grid-loading.css";

function GridLoading() {
    const spinnerVariants = {
        initial: { opacity: 0 },
        animate: { opacity: 1, transition: { duration: 0.5 } },
    };

    return (
        <div className="gridloading-wrapper">
            <motion.div
                className="gridloading-container"
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

export default GridLoading;