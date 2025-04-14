
/**
 * A customizable toggle switch component.
 *
 * @param {Object} props - The props object.
 * @param {string} [props.onLabel="Legend"] - The label displayed when the switch is in the "on" state.
 * @param {string} [props.offLabel="Configure"] - The label displayed when the switch is in the "off" state.
 * @param {boolean} [props.initialChecked=false] - The initial state of the switch (checked or unchecked).
 * @param {function} [props.onToggle=() => {}] - Callback function triggered when the switch is toggled.
 *   Receives the new state (boolean) as an argument.
 *
 * @returns {JSX.Element} The rendered toggle switch component.
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
