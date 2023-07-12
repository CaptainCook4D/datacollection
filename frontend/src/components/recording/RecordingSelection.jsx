import React, { useState, useEffect } from 'react';
import "./RecordingSelection.css";
import RecordingSelectionCard from "./RecordingSelectionCard";
import RecordingDisplayCard from "./RecordingDisplayCard";
import SuccessPopup from "../atoms/SuccessPopup";
import ErrorPopup from "../atoms/ErrorPopup";

const RecordingSelection = (props) => {
	
	const {userData, environment, activities, recording, setRecording} = props;
	
	const [environmentNormalActivityIds, setEnvironmentNormalActivityIds] = useState([]);
	const [environmentErrorActivityIds, setEnvironmentErrorActivityIds] = useState([]);
	
	const [activityIdToActivityName, setActivityIdToActivityName] = useState({});
	
	const [successPopupOpen, setSuccessPopupOpen] = useState(false);
	const [errorPopupOpen, setErrorPopupOpen] = useState(false);
	
	const [successPopupMessage, setSuccessPopupMessage] = useState("");
	const [errorPopupMessage, setErrorPopupMessage] = useState("");
	
	const handleSuccessPopupOpen = (successMessage) => {
		setSuccessPopupMessage(successMessage)
		setSuccessPopupOpen(true);
	};
	
	const handleSuccessPopupClose = () => {
		setSuccessPopupOpen(false);
	};
	
	const handleErrorPopupClose = () => {
		setErrorPopupOpen(false);
	};
	
	const handleErrorPopupOpen = (errorMessage) => {
		setErrorPopupMessage(errorMessage)
		setErrorPopupOpen(true);
	};
	
	useEffect(() => {
		if (
			userData &&
			environment &&
			activities &&
			userData.recording_schedules &&
			userData.recording_schedules[environment]
		) {
			
			setEnvironmentNormalActivityIds(
				userData.recording_schedules[environment].normal_activities
			);
			
			setEnvironmentErrorActivityIds(
				userData.recording_schedules[environment].error_activities
			);
			
		}
		
		let activityIdToActivityNameTemp = {};
		activities.forEach((activity) => {
			activityIdToActivityNameTemp[activity.id] = activity.name;
		});
		
		setActivityIdToActivityName(activityIdToActivityNameTemp);
	}, [userData, environment, activities]);
	
	return (
		
		<div className="recordingSelectionContainer">
			<div className="recordingSelectionContent">
				<div className="recordingSelectionGridContainer">
					<div className="recordingSelectionGridItem">
						<RecordingSelectionCard
							userData={userData}
							environment={environment}
							activityIdToActivityName={activityIdToActivityName}
							activityIds={environmentNormalActivityIds}
							label={"Normal"}
							setRecording={setRecording}
							handleSuccessPopupOpen={handleSuccessPopupOpen}
							handleErrorPopupOpen={handleErrorPopupOpen}
						/>
					</div>
					<div className="recordingSelectionGridItem">
						<RecordingSelectionCard
							userData={userData}
							environment={environment}
							activityIdToActivityName={activityIdToActivityName}
							activityIds={environmentErrorActivityIds}
							label={"Error"}
							setRecording={setRecording}
							handleSuccessPopupOpen={handleSuccessPopupOpen}
							handleErrorPopupOpen={handleErrorPopupOpen}
						/>
					</div>
				</div>
				
				<div className="recordingSelectionDisplayContainer">
					<RecordingDisplayCard
						userData={userData}
						recording={recording}
						environment={environment}
						setRecording={setRecording}
						activities={activities}
						handleSuccessPopupOpen={handleSuccessPopupOpen}
						handleErrorPopupOpen={handleErrorPopupOpen} />
					
					<SuccessPopup isOpen={successPopupOpen} onClose={handleSuccessPopupClose} successPopupMessage={successPopupMessage} />
					<ErrorPopup
						isOpen={errorPopupOpen}
						onClose={handleErrorPopupClose}
						errorMessage={errorPopupMessage}
					/>
				</div>
				
				
			</div>
		</div>
	);
};

export default RecordingSelection;
