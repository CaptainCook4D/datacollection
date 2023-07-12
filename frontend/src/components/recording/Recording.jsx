import React, {useEffect, useState} from "react";
import { Stepper, Step, StepLabel, Button } from "@mui/material";
import AppBar from "../atoms/AppBar";
// import styles from "./Recording.css";
import "./Recording.css";
import RecordingSelection from "./RecordingSelection";
import RecordingPreparation from "./RecordingPreparation";
import RecordingRecording from "./RecordingRecording";
import axios from "axios";
import API_BASE_URL from "../../config";
import {useNavigate} from "react-router-dom";
import RecordingReview from "./RecordingReview";

const Recording = (props) => {
	
	const {userData, environment, activities, setUserData, setActivities, setEnvironment} = props;
	
	const [activeStep, setActiveStep] = useState(0);
	const [recording, setRecording] = useState(false);
	
	const [errorTags, setErrorTags] = useState([]);
	
	const navigate = useNavigate();
	
	useEffect(() => {
		let url = `${API_BASE_URL}/error_tags`;
		axios.get(url)
			.then((response) => {
				setErrorTags(response.data);
				console.log(response.data);
			})
			.catch((error) => {
				console.log(error);
			});
	}, []);
	
	const steps = ["Activity Selection", "Activity Preparation", "Activity Recording", "Activity Recording AnnotationReview"];
	
	const handleNext = () => {
		if (validateStep(activeStep)) {
			setActiveStep((prevActiveStep) => prevActiveStep + 1);
		}
	};
	
	const handleBack = () => {
		setActiveStep((prevActiveStep) => prevActiveStep - 1);
	};
	
	const validateStep = (stepIndex) => {
		// Add your validation logic for each step here
		// Return true if the step is valid, otherwise return false
		switch (stepIndex) {
			case 0:
				// Validate Step 1 Recording Selection
				return true;
			case 1:
				// // Validate Step 2 Recording Preparation
				// if (!recording.is_error) {
				// 	return true;
				// }
				//
				// const errorDict = {};
				// let totalErrors = 0;
				// recording.steps.forEach((step) => {
				// 	if (step.errors && step.errors.length > 0) {
				// 		step.errors.forEach((error) => {
				// 			if (error.tag){
				// 				errorDict[error.tag] = (errorDict[error.tag] || 0) + 1;
				// 				totalErrors = totalErrors + 1;
				// 			}
				// 		});
				// 	}
				// });
				//
				// const requiredErrorTypes = ["Preparation Error","Measurement Error","Timing Error","Technique Error","Temperature Error"];
				//
				// const hasAtLeastOneErrorOfEachType = requiredErrorTypes.every(
				// 	(type) => errorDict[type] && errorDict[type] > 0
				// );
				//
				// if (!hasAtLeastOneErrorOfEachType) {
				// 	alert("Please make sure you have at least one error of each type");
				// 	return false;
				// }
				//
				// if (totalErrors < Math.floor(0.6 * recording.steps.length)){
				// 	alert("Please add " + (Math.floor(0.6 * recording.steps.length) - totalErrors) + " more errors to proceed to recording" );
				// 	return false;
				// }
				//
				return true;
				
			case 2:
				// Validate Step 3 Recording Recording
				return true;
			case 3:
				// Validate Step 4 Recording AnnotationReview
				return true;
			default:
				return false;
		}
	};
	
	const handleFinish = async () => {
		if (validateStep(activeStep)) {
			// Perform API call
			// Replace the API call URL and request data with your specific API requirements
			// let updatedRecording = recording;
			// updatedRecording.recorded_by = userData.id;
			// setRecording(updatedRecording);
			let url = `${API_BASE_URL}/recordings/${recording.id}/user/${userData.id}`;
			axios.post(url, recording)
				.then(response => {
					setRecording(response.data);
					console.log(response.data);
					navigate("/login");
				})
				.catch(error => {
					alert("Error: " + error)
					console.log(error);
				});
				
		}
	};
	
	const getContent = (stepIndex) => {
		switch (stepIndex) {
			case 0:
				return ( <div>
					<RecordingSelection userData={userData}
				                                environment={environment}
				                                activities={activities}
				                                recording={recording}
				                                setUserData={setUserData}
				                                setEnvironment={setEnvironment}
				                                setActivities={setActivities}
                                                setRecording={setRecording}	/>
					</div>);
			case 1:
				return ( <div>
							<RecordingPreparation userData={userData}
							                        environment={environment}
							                        activities={activities}
								                    recording={recording}
								                    setUserData={setUserData}
								                    setEnvironment={setEnvironment}
								                    setActivities={setActivities}
								                    setRecording={setRecording}
					                                errorTags={errorTags}	/>
						</div>);
			case 2:
				return ( <div>
					<RecordingRecording userData={userData}
					                      environment={environment}
					                      activities={activities}
					                      recording={recording}
					                      setUserData={setUserData}
					                      setEnvironment={setEnvironment}
					                      setActivities={setActivities}
					                      setRecording={setRecording}	/>
				</div>);
			case 3:
				return ( <div>
					<RecordingReview userData={userData}
					                      environment={environment}
					                      activities={activities}
					                      recording={recording}
					                      setUserData={setUserData}
					                      setEnvironment={setEnvironment}
					                      setActivities={setActivities}
					                      setRecording={setRecording}
					                      errorTags={errorTags}	/>
					</div>);
			default:
				return <div>Unknown step</div>;
		}
	};
	
	return (
		<div className="recordingContainer">
			<div className="recordingHeader">
				<AppBar userData={userData} />
			</div>
			
			<div className="recordingStepperContainer">
				<div className="recordingStepper">
					<Stepper activeStep={activeStep} alternativeLabel>
						{steps.map((label) => (
							<Step key={label}>
								<StepLabel>{label}</StepLabel>
							</Step>
						))}
					</Stepper>
				</div>
				
				<div className="recordingContent">
					{
						getContent(activeStep)
					}
				</div>
				
				<div className="recordingButtonContainer">
					<Button
						className="backButton"
						disabled={activeStep === 0}
						onClick={handleBack}
					>
						Back
					</Button>
					{activeStep === steps.length - 1 ? (
						<Button
							className="nextButton"
							variant="contained"
							color="primary"
							onClick={handleFinish}
						>
							Finish
						</Button>
					) : (
						<Button
							className="nextButton"
							variant="contained"
							color="primary"
							onClick={handleNext}
						>
							Next
						</Button>
					)}
				</div>
			</div>
		</div>
	);
};


export default Recording;