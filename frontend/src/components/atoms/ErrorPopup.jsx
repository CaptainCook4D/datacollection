import React from 'react';
import './ErrorPopup.css';

const ErrorPopup = ({ isOpen, onClose, errorMessage }) => {
	return (
		isOpen && (
			<div className="error-popup">
				<div className="error-popup-content">
					<p>{errorMessage}</p>
					<button className="close-btn" onClick={onClose}>
						Close
					</button>
				</div>
			</div>
		)
	);
};

export default ErrorPopup;
