import AppBar from "../atoms/AppBar";
import "./LabelStudio.css";
import {useEffect, useState} from "react";
import API_BASE_URL from "../../config";
import axios from "axios";
import {Table} from "@mui/material";
import {CircularProgress} from "@mui/material";

const LabelStudio = (props) => {
	
	const {userData, environment, activities, setUserData, setActivities, setEnvironment} = props;
	
	// Add the following state
	const [loadingCreate, setLoadingCreate] = useState(false);
	const [loadingDelete, setLoadingDelete] = useState(false);
	const [loadingBackup, setLoadingBackup] = useState(false);
	const [loadingCreateRecording, setLoadingCreateRecording] = useState(false);
	const [loadingDeleteRecording, setLoadingDeleteRecording] = useState(false);
	const [loadingBackupRecording, setLoadingBackupRecording] = useState(false);
	
	const [annotationActivities, setAnnotationActivities] = useState(null);
	
	const [activityIdToActivityNameMap, setActivityIdToActivityNameMap] = useState({});
	
	useEffect(() => {
		let url = `${API_BASE_URL}/users/${userData.id}/annotation/assignments`;
		axios.get(url)
			.then(response => {
				setAnnotationActivities(response.data);
				console.log(response.data);
			})
			.catch(error => {
				alert("Error: " + error)
				console.log(error);
			});
	}, []);
	
	useEffect(() => {
		let tempActivityIdToActivityNameMap = {};
		
		activities.forEach(activity => {
			tempActivityIdToActivityNameMap[activity.id] = activity.name;
		});
		
		setActivityIdToActivityNameMap(tempActivityIdToActivityNameMap);
	}, [activities]);
	
	const handleCreateProjectsButtonClick = (annotationActivity) => {
		setLoadingCreate(true);
		let url = `${API_BASE_URL}/users/${userData.id}/annotation/activities/${annotationActivity.activity_id}/create/projects`;
		axios.post(url)
			.then((response) => {
				setLoadingCreate(false);
				alert('Successfully created projects for activity: ' + annotationActivity.activity_id)
			})
			.catch((apiError) => {
				setLoadingCreate(false);
				alert('Error during API call: ' + apiError)
				console.error('Error during API call:', apiError);
			});
	}
	
	const handleDeleteProjectsButtonClick = (annotationActivity) => {
		setLoadingDelete(true);
		let url = `${API_BASE_URL}/users/${userData.id}/annotation/activities/${annotationActivity.activity_id}/delete/projects`;
		axios.post(url)
			.then((response) => {
				setLoadingDelete(false);
				alert('Successfully deleted projects for activity: ' + annotationActivity.activity_id)
			})
			.catch((apiError) => {
				setLoadingDelete(false);
				alert('Error during API call: ' + apiError)
				console.error('Error during API call:', apiError);
			});
	}
	
	const handleBackupAnnotationsButtonClick = (annotationActivity) => {
		setLoadingBackup(true);
		let url = `${API_BASE_URL}/users/${userData.id}/annotation/activities/${annotationActivity.activity_id}/backup/projects`;
		axios.post(url)
			.then((response) => {
				setLoadingBackup(false);
				alert('Successfully backed up projects for activity: ' + annotationActivity.activity_id)
			})
			.catch((apiError) => {
				setLoadingBackup(false);
				alert('Error during API call: ' + apiError)
				console.error('Error during API call:', apiError);
			});
	}
	
	const handleCreateRecordingProjectButtonClick = (annotationActivityRecording) => {
		setLoadingCreateRecording(true);
		let url = `${API_BASE_URL}/users/${userData.id}/annotation/recording/${annotationActivityRecording.id}/create/project`;
		axios.post(url)
			.then((response) => {
				setLoadingCreateRecording(false);
				alert('Successfully created project for recording: ' + annotationActivityRecording.id)
			})
			.catch((apiError) => {
				setLoadingCreateRecording(false);
				alert('Error during API call: ' + apiError)
				console.error('Error during API call:', apiError);
			});
	}
	
	const handleDeleteRecordingProjectButtonClick = (annotationActivityRecording) => {
		setLoadingDeleteRecording(true);
		let url = `${API_BASE_URL}/users/${userData.id}/annotation/recording/${annotationActivityRecording.id}/delete/project`;
		axios.post(url)
			.then((response) => {
				setLoadingDeleteRecording(false);
				alert('Successfully deleted project for recording: ' + annotationActivityRecording.id)
			})
			.catch((apiError) => {
				setLoadingDeleteRecording(false);
				alert('Error during API call: ' + apiError)
				console.error('Error during API call:', apiError);
			});
	}
	
	const handleBackupRecordingAnnotationButtonClick = (annotationActivityRecording) => {
		setLoadingBackupRecording(true);
		let url = `${API_BASE_URL}/users/${userData.id}/annotation/recording/${annotationActivityRecording.id}/backup/project`;
		axios.post(url)
			.then((response) => {
				setLoadingBackupRecording(false);
				alert('Successfully backed up project for recording: ' + annotationActivityRecording.id)
			})
			.catch((apiError) => {
				setLoadingBackupRecording(false);
				alert('Error during API call: ' + apiError)
				console.error('Error during API call:', apiError);
			});
	}
	
	
	return (
		<div className="labelStudioContainer">
			<div className="labelStudioHeader">
				<AppBar userData={userData} />
			</div>
			
			<div className="labelStudioContent">
				<div className="labelStudioContentHeader">
					<h1>Label Studio Projects Window</h1>
				</div>
				
				<div className="labelStudioContentBody">
					{
						annotationActivities?.map((annotationActivity, annotationActivityIndex) => (
							<div className="labelStudioActivityContainer" key={annotationActivityIndex}>
								<div className="labelStudioActivityHeader">
									{loadingCreate && <CircularProgress />}
									{loadingBackup && <CircularProgress />}
									{loadingDelete && <CircularProgress />}
									{loadingCreateRecording && <CircularProgress />}
									{loadingBackupRecording && <CircularProgress />}
									{loadingDeleteRecording && <CircularProgress />}
								</div>
								<Table className="labelStudioActivityRecordingsTable" striped bordered hover>
									<thead>
									<tr>
										<th>{activityIdToActivityNameMap[annotationActivity.activity_id]}</th>
										<th><button className="labelStudioButtonCreate" onClick={() => handleCreateProjectsButtonClick(annotationActivity)}>Create Projects</button></th>
										<th><button className="labelStudioButtonBackup" onClick={() => handleBackupAnnotationsButtonClick(annotationActivity)}>Backup Annotations</button></th>
										<th><button className="labelStudioButtonDelete" onClick={() => handleDeleteProjectsButtonClick(annotationActivity)}>Delete Projects</button></th>
									</tr>
									</thead>
									<tbody>
									{annotationActivity.recordings.map((annotationActivityRecording, annotationActivityRecordingIndex) => (
										<tr key={annotationActivityRecordingIndex}>
											<td>{annotationActivityRecording.id}</td>
											<td><button className="labelStudioButtonCreate" onClick={() => handleCreateRecordingProjectButtonClick(annotationActivityRecording)}>Create Recording Project</button></td>
											<td><button className="labelStudioButtonBackup" onClick={() => handleBackupRecordingAnnotationButtonClick(annotationActivityRecording)}>Backup Recording Annotation</button></td>
											<td><button className="labelStudioButtonDelete" onClick={() => handleDeleteRecordingProjectButtonClick(annotationActivityRecording)}>Delete Recording Project</button></td>
										</tr>
									))}
									</tbody>
								</Table>
							</div>
							
							))
					}
				
				</div>
			</div>
		</div>
	);
	
};

export default LabelStudio;