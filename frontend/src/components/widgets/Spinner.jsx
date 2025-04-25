// SpinnerLoader.tsx
import { motion } from "framer-motion";
import React from "react";
import "./styles/spinner.css";

export default function SpinnerLoader() {
  return (
    <div className="flex items-center justify-center h-full w-full">
      <motion.div
        className="w-12 h-12 border-4 border-t-transparent border-green-500 rounded-full"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
      />
    </div>
  );
}