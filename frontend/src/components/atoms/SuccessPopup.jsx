import React from 'react';
import './SuccessPopup.css';

const SuccessPopup = (props) => {
	
	const { isOpen, onClose, successPopupMessage } = props;
	
	return (
		isOpen && (
			<div className="success-popup">
				<div className="success-popup-content">
					<p>{successPopupMessage}</p>
					<button className="close-btn" onClick={onClose}>
						Close
					</button>
				</div>
			</div>
		)
	);
};

export default SuccessPopup;
