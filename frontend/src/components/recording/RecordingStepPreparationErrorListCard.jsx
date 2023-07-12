import React, { useState } from 'react';
import './RecordingStepPreparationErrorList.css';

const RecordingStepPreparationErrorList = ({ recording, stepIndex, handleDeleteAllStepErrors, handleDeleteStepError }) => {
	const [deleteEnabled, setDeleteEnabled] = useState(false);
	
	const toggleDelete = () => {
		setDeleteEnabled(!deleteEnabled);
	};
	
	const handleDeleteAll = () => {
		handleDeleteAllStepErrors();
	};
	
	const handleDeleteItem = (error) => {
		handleDeleteStepError(error);
	};
	
	return (
		<div className="recStepPrepErrorListContainer">
			<div className="recStepPrepErrorList">
				{recording.steps[stepIndex].errors.map((error, errorIndex) => (
					<div key={error.description} className="recStepPrepError">
						<div className="recStepPrepErrorTag">
							{error.tag}
						</div>
						<div className="recStepPrepErrorDescription">
							{error.description}
						</div>
						{deleteEnabled && (
							<button
								className="recStepPrepErrorDelete"
								onClick={() => handleDeleteItem(errorIndex)}
							>
								Delete
							</button>
						)}
					</div>
				))}
			</div>
			<div className="recStepPrepErrorListActions">
				<button onClick={toggleDelete}>
					{deleteEnabled ? 'Disable Delete' : 'Enable Delete'}
				</button>
				{deleteEnabled && (
					<button onClick={handleDeleteAll}>Delete All</button>
				)}
			</div>
		</div>
	);
};

export default RecordingStepPreparationErrorList;
