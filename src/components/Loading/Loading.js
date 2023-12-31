import React from "react";
import './Loading.css';

function Loading(){
    return (
        <div className="loading">
            <svg viewBox="25 25 50 50">
                <circle cx="50" cy="50" r="20"></circle>
            </svg>
        </div>
    )
}

export default Loading;