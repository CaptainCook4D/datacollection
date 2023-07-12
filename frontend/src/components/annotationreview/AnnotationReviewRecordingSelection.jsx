import React, {useEffect, useState} from 'react';
import './AnnotationReviewRecordingSelection.css';
import API_BASE_URL from "../../config";
import axios from "axios";
import {Button, Table} from "@mui/material";

const AnnotationReviewRecordingSelection = (props) => {
	
	const {userData, activities, recording, setActivities, setRecording} = props;
	const [reviewRecordings, setReviewRecordings] = useState([]);
	
	const [adminUserId, setAdminUserId] = useState(0);
	
	useEffect(() => {
		let url = `${API_BASE_URL}/users/${adminUserId}/review/recordings`;
		axios.get(url)
			.then((response) => {
				setReviewRecordings(response.data);
				console.log(response.data);
			})
			.catch((error) => {
				console.log(error);
			});
	}, []);
	
	const handleButtonClick = (environmentRecording) => {
		setRecording(environmentRecording.recording);
	};
	
	if (!reviewRecordings) {
		return (
			<div className="reviewEnvironmentErrorMessage">
				<h1>Something wrong with API call to fetch all user recordings for review</h1>
			</div>
		);
	}
	
	const getRecordingType = (recording) => {
		if (recording.is_error) {
			return "Error";
		} else {
			return "Normal";
		}
	}
	
	return (
		<div className="reviewRecordingsContainer">
			{reviewRecordings.map((environmentReview, environmentIndex) => (
				<div className="reviewEnvironmentRecordingsTableContainer" key={environmentIndex}>
					<h2 className="reviewEnvironmentTitle">Environment: {environmentReview.environment_name}</h2>
					<Table className="reviewEnvironmentRecordingsTable" striped bordered hover>
						<thead>
						<tr>
							<th>Recording ID</th>
							<th>Activity Name</th>
							<th>Type</th>
							<th>Status</th>
							<th>Selection</th>
						</tr>
						</thead>
						<tbody>
						{environmentReview.environment_recordings.map((environmentRecording, envRecordingIndex) => (
							<tr key={envRecordingIndex} className="reviewEnvironmentRecordingRow">
								<td>{environmentRecording.recording.id}</td>
								<td>{environmentRecording.activity_name}</td>
								<td>{getRecordingType(environmentRecording.recording)}</td>
								<td>{environmentRecording.status}</td>
								<td>
									<Button className="reviewEnvironmentReviewButton" onClick={() => handleButtonClick(environmentRecording)}>Pick to review</Button>
								</td>
							</tr>
						))}
						</tbody>
					</Table>
				</div>
			))}
		</div>
	);
};

export default AnnotationReviewRecordingSelection;
