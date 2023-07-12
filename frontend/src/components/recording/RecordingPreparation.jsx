import React, {useState} from 'react';
import './RecordingPreparation.css';
import RecordingStepPreparation from "./RecordingStepPreparation";
import RecordingErrorHints from "./RecordingErrorHints";

const RecordingPreparation = (props) => {
	const { userData, environment, activities, recording, setRecording, errorTags: errorTags} = props;
	
	const [showTable, setShowTable] = useState(false);
	
	const getActivityName = (activityId) => {
		const activity = activities.find((activity) => activity.id === activityId);
		return activity.name;
	};
	
	const getDescription = (step) => {
		return step.modified_description || step.description;
	};
	
	const getActivityDescription = (activityId) => {
		const activity = activities.find((activity) => activity.id === activityId);
		const descriptions = activity.steps.map(step => step.description);
		return descriptions.join(".");
	};
	
	const getActivityErrorHints = (activityId) => {
		const activity = activities.find((activity) => activity.id === activityId);
		return activity.error_hints;
	};
	
	const handleShowErrorTableClick = () => {
		setShowTable(!showTable);
	};
	
	if (!recording) {
		return (
			<div>
				<h1>Please go back and select an activity to begin preparing for the recording</h1>
			</div>
		);
	}
	
	return (
		<div className="recPrepContainer">
			{recording.is_error ? (
				<table className="recPrepTable">
					<thead>
					<tr className="recPrepTableHeader">
						<th colSpan="4">Preparing activity {getActivityName(recording.activity_id)}</th>
					</tr>
					</thead>
					<tbody>
					<tr className="recPrepTableRow">
						<td className="recPrepBox">
							{getActivityDescription(recording.activity_id)}
						</td>
					</tr>
					<tr className="recPrepErrorHintButton">
						<button onClick={handleShowErrorTableClick}>
							SHOW ERROR HINTS
						</button>
						{showTable && <RecordingErrorHints errorHints={getActivityErrorHints(recording.activity_id)} />}
					</tr>
					{recording.steps.map((row, index) => (
						<tr key={index} className="recPrepTableRow">
							<td className="recPrepBox">
								<details className="recPrepAccordionDetails" open>
									<summary className="recPrepAccordionSummary">
										<span> {getDescription(row)} </span>
									</summary>
									<RecordingStepPreparation
										recording={recording}
										setRecording={setRecording}
										errorTags={errorTags}
										step={row}
										stepIndex={index} />
								</details>
							</td>
						</tr>
					))}
					</tbody>
				</table>
			) : (
				<h2 className="proceedToRecordButton">
					Proceed to record, you are ready!
				</h2>
			)}
			
			<h2 className="proceedToRecordButton">
				Proceed to record, you are ready!
			</h2>
		</div>
	);
	
	
};

export default RecordingPreparation;
