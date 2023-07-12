import React, { useState } from "react";
import axios from "axios";
import API_BASE_URL from "../../config"; // 1. Import axios
import "./RecordingRecordingInfo.css";

const RecordingRecordingInfo = (props) => {
	const { recording, setRecording } = props;
	
	const [goproToggle, setGoproToggle] = useState(
		recording.recording_info.gopro
	);
	const [hololensToggles, setHololensToggles] = useState(
		recording.recording_info.hololens_info
	);
	
	const [subprocessId, setSubprocessId] = useState(null);
	
	const handleGoproToggle = () => {
		setGoproToggle(!goproToggle);
	};
	
	const handleHololensToggle = (type) => {
		setHololensToggles({
			...hololensToggles,
			[type]: !hololensToggles[type],
		});
	};
	
	// 2. Create a function to update the toggles through an API call
	const updateToggles = async () => {
		let url = `${API_BASE_URL}/recordings/${recording.id}`;
		recording.recording_info.gopro = goproToggle;
		recording.recording_info.hololens_info = hololensToggles;
		
		axios.post(url, recording)
			.then((response) => {
				setRecording(response.data);
				if (response.status === 200) {
					alert("Toggles updated successfully!");
				} else {
					alert("Error updating toggles!");
				}
			})
			.catch((error) => {
				console.error("Error updating toggles:", error);
				alert("Error updating toggles!" + error);
			});
			
	};
	
	const handleBeginRecording = async () => {

		let url = `${API_BASE_URL}/start/recording/${recording.id}`;
		axios.post(url, recording)
			.then((response) => {
				setRecording(recording);
				setSubprocessId(response.data.subprocess_id);
				if (response.status === 200) {
					alert("Recording started successfully!");
				} else {
					alert("Error starting recording!");
				}
			})
			.catch((error) => {
				console.error("Error starting recording:", error);
				alert("Error starting recording!" + error);
			});
			
	};
	
	const handleEndRecording = async () => {

		let url = `${API_BASE_URL}/stop/recording/${recording.id}/${subprocessId}`;
		axios.post(url, recording)
			.then((response) => {
				setRecording(recording);
				if (response.status === 200) {
					alert("Recording ended successfully!");
				} else {
					alert("Error ending recording!");
				}
			})
			.catch((error) => {
				console.error("Error ending recording:", error);
				alert("Error ending recording!" + error);
			});

	};
	
	return (
		
		<div className="recRecordContent">
			<div className="recRecordInfoContainer">
				<div className="recRecordGoProInfo">
					<h2>GoPro</h2>
					<button className="recRecordButton" onClick={handleGoproToggle}>
						{goproToggle ? "Disable" : "Enable"}
					</button>
				</div>
				
				<div className="recRecordHololensInfo">
					<h2>HoloLens</h2>
					<button className="recRecordButton" onClick={() => handleHololensToggle("pv")}>
						{hololensToggles.pv ? "Disable PV" : "Enable PV"}
					</button>
					<button className="recRecordButton" onClick={() => handleHololensToggle("mc")}>
						{hololensToggles.mc ? "Disable Audio" : "Enable Audio"}
					</button>
					<button className="recRecordButton" onClick={() => handleHololensToggle("depth_ahat")}>
						{hololensToggles.depth_ahat ? "Disable Depth" : "Enable Depth"}
					</button>
					<button className="recRecordButton" onClick={() => handleHololensToggle("spatial")}>
						{hololensToggles.spatial ? "Disable Spatial" : "Enable Spatial"}
					</button>
					<button className="recRecordButton" onClick={() => handleHololensToggle("imu")}>
						{hololensToggles.imu ? "Disable IMU" : "Enable IMU"}
					</button>
				</div>
				
			</div>
			
			<div className="recRecordUpdateButtons">
				<div className="updateTogglesButton">
					<button className="recRecordButton" onClick={updateToggles}>Update Recording Info</button>
				</div>
				
				<div className="extraButtons">
					<button className="recRecordButton recRecordButton1" onClick={handleBeginRecording}>
						Begin Recording
					</button>
					<button className="recRecordButton recRecordButton2" onClick={handleEndRecording}>
						End Recording
					</button>
				</div>
			</div>
			
		</div>
		
	);
};

export default RecordingRecordingInfo;