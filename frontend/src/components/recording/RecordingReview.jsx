import React from 'react';
import './RecordingReview.css';
import RecordingStepPreparation from "./RecordingStepPreparation";

const RecordingReview = (props) => {
	
	const { userData, environment, activities, recording, setRecording, errorTags} = props;
	
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
	
	if (!recording) {
		return (
			<div>
				<h1>Please go back and select an activity to begin preparing for the recording</h1>
			</div>
		);
	}
	
	return (
		<div className="recReviewContainer">
			<table className="recReviewTable">
				<thead>
				<tr className="recReviewTableHeader">
					<th colSpan="4">Preparing activity {getActivityName(recording.activity_id)}</th>
				</tr>
				</thead>
				<tbody>
				<tr className="recReviewTableRow">
					<td className="recReviewBox">
						{getActivityDescription(recording.activity_id)}
					</td>
				</tr>
				{recording.steps.map((row, index) => (
					<tr key={index} className="recReviewTableRow">
						<td className="recReviewBox">
							<details className="recReviewAccordionDetails" open>
								<summary className="recReviewAccordionSummary">
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
		</div>
	);
	
	
};

export default RecordingReview;
