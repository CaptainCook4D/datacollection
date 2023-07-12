import React from 'react';
import axios from "axios";
import './RecordingDisplayCard.css';
import API_BASE_URL from "../../config";

const RecordingDisplayCard = (props) => {
	
	const {userData, environment, activities, recording, setRecording, handleSuccessPopupOpen, handleErrorPopupOpen} = props;
	
	const getActivityName = (activityId) => {
		const activity = activities.find((activity) => activity.id === activityId);
		return activity.name;
	};
	
	const selectRecording = async () => {
		try {
			let url = `${API_BASE_URL}/users/${userData.id}/environment/${environment}/select/recordings/${recording.id}`;
			const response = await axios.post(url);
			setRecording(response.data)
			handleSuccessPopupOpen("Picked the recording, proceed to prepare the recording");
		} catch (error) {
			console.error(error);
			handleErrorPopupOpen("Error picking the recording, change selection or refresh the page to try again");
		}
	};
	
	return (
		<div className="recordingDisplayGridContainer">
			{recording ? (
				<div>
					<div className="recordingDisplayGridItem">
						<table className="recordingDisplayTable">
							<thead>
							<tr>
								<th>Recording Steps for {getActivityName(recording.activity_id)}</th>
							</tr>
							</thead>
							<tbody>
							{recording.steps.map((step, index) => (
								<tr key={index}>
									<td>{step.description}</td>
								</tr>
							))}
							</tbody>
						</table>
					</div>
					
					<div className="recordingDisplayGridItem">
						<button
							onClick={selectRecording}
							className="recordingSelectionButton"
						>
							Pick to record
						</button>
					</div>
				</div>
			) : (
				<div className="recordingDisplayGridItem">
					<h6 className="recordingDisplayNoRecording">
						No recording selected
					</h6>
				</div>
			)}
		</div>
	);
}

export default RecordingDisplayCard;
