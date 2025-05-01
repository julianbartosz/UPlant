/**
 * A customizable toggle switch component.
 *
 * @param {Object} props
 * @param {string} [props.onLabel="Legend"]
 * @param {string} [props.offLabel="Configure"]
 * @param {boolean} [props.initialChecked=false]
 * @param {function} [props.onToggle=() => {}] 
 * @returns {JSX.Element}
 */

import React, { useState } from "react";
import "./styles/toggle-switch.css";

function ToggleSwitch({
  onLabel = "Legend",
  offLabel = "Configure",
  initialChecked = false,
  onToggle = () => {},
}) {

  const [checked, setChecked] = useState(initialChecked);

  const handleClick = () => {
    setChecked((prev) => {
      const next = !prev;
      onToggle(next);
      return next;
    });
  };

  return (
    <div className="switch-wrapper" onClick={handleClick}>
      <span className="switch-label">{offLabel}</span>
      <div className={`switch-track ${checked ? "checked" : ""}`}>
        <div className="switch-handle" />
      </div>
      <span className="switch-label">{onLabel}</span>
    </div>
  );
}

export default ToggleSwitch;
