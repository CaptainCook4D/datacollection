import Home from "../home/Home";
import { Stepper, Step, StepLabel, Button } from "@mui/material";
import AppBar from "../atoms/AppBar";
import "./AnnotationReview.css";
import API_BASE_URL from "../../config";
import axios from "axios";
import RecordingSelection from "../recording/RecordingSelection";
import RecordingPreparation from "../recording/RecordingPreparation";
import RecordingRecording from "../recording/RecordingRecording";
import RecordingReview from "../recording/RecordingReview";
import React, {useEffect, useState} from "react";
import {useNavigate} from "react-router-dom";
import AnnotationReviewRecordingSelection from "./AnnotationReviewRecordingSelection";

const AnnotationReview = (props) => {
	const {userData, environment, activities, setUserData, setActivities, setEnvironment} = props;
	
	const [activeStep, setActiveStep] = useState(0);
	const [recording, setRecording] = useState(false);
	
	const navigate = useNavigate();
	const steps = ["Pick a Recording", "Review Recording"];
	const [errorTags, setErrorTags] = useState([]);
	
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
				return true;
			case 1:
				return true;
			default:
				return false;
		}
	};
	
	const handleFinish = async () => {
		if (validateStep(activeStep)) {
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
					<AnnotationReviewRecordingSelection userData={userData}
					                                    activities={activities}
					                                    recording={recording}
					                                    setActivities={setActivities}
					                                    setRecording={setRecording}	/>
				</div>);
			case 1:
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
		<div className="reviewContainer">
			<div className="reviewHeader">
				<AppBar userData={userData} />
			</div>
			
			<div className="reviewStepperContainer">
				<div className="reviewStepper">
					<Stepper activeStep={activeStep} alternativeLabel>
						{steps.map((label) => (
							<Step key={label}>
								<StepLabel>{label}</StepLabel>
							</Step>
						))}
					</Stepper>
				</div>
				
				<div className="reviewContent">
					{
						getContent(activeStep)
					}
				</div>
				
				<div className="reviewButtonContainer">
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


export default AnnotationReview;