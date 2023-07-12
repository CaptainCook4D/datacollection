import React, {useState} from 'react';
import axios from 'axios';
import './RecordingStepPreparation.css';
import RecordingStepPreparationErrorList from "./RecordingStepPreparationErrorListCard";
import API_BASE_URL from "../../config";

const RecordingStepPreparation = (props) => {
	
	const {recording, setRecording, errorTags, stepIndex} = props;
	
	const [selectedItems, setSelectedItems] = useState(new Set());
	const [errorText, setErrorText] = useState('');
	const [stepDescription, setStepDescription] = useState('');
	
	const resetState = () => {
		setSelectedItems(new Set());
		setErrorText('');
		setStepDescription('');
	};
	
	const handleCheckboxChange = (item, checked) => {
		const newSelectedItems = new Set(selectedItems);
		
		if (checked) {
			newSelectedItems.add(item);
		} else {
			newSelectedItems.delete(item);
		}
		
		setSelectedItems(newSelectedItems);
	};
	
	const handleErrorTextChange = (e) => {
		setErrorText(e.target.value);
	};
	
	const handleUpdateStepDescriptionChange = (e) => {
		setStepDescription(e.target.value);
	};
	
	const handleClick = async () => {
		if (selectedItems.size === 0) {
			alert('Please select at least one error tag.');
			return;
		} else if (errorText === '') {
			alert('Please enter a description of the error.');
			return;
		}
		if (stepDescription !== '') {
			recording.steps[stepIndex].modified_description = stepDescription;
		}
		
		if (!recording.steps[stepIndex].errors) {
			recording.steps[stepIndex].errors = [];
		}
		
		recording.steps[stepIndex].errors.push({
			tag: [...selectedItems.values()][0],
			description: errorText
		});
		
		let url = `${API_BASE_URL}/recordings/${recording.id}`;
		axios.post(url, recording)
			.then((recordingResponse) => {
				if (recordingResponse.data) {
					setRecording(recordingResponse.data);
					resetState();
				}
			})
			.catch((apiError) => {
				alert('Error during API call: ' + apiError)
				console.error('Error during API call:', apiError);
			});
	};
	
	const handleDeleteAllStepErrors = async () => {
		recording.steps[stepIndex].errors = [];
		let url = `${API_BASE_URL}/recordings/${recording.id}`;
		axios.post(url, recording)
			.then((recordingResponse) => {
				if (recordingResponse.data) {
					setRecording(recordingResponse.data);
				}
			})
			.catch((apiError) => {
				alert('Error during API call: ' + apiError)
				console.error('Error during API call:', apiError);
			});
	};
	
	const handleDeleteStepError = async (errorIndex) => {
		recording.steps[stepIndex].errors.splice(errorIndex, 1);
		let url = `${API_BASE_URL}/recordings/${recording.id}`;
		axios.post(url, recording)
			.then((recordingResponse) => {
				if (recordingResponse.data) {
					setRecording(recordingResponse.data);
				}
			})
			.catch((apiError) => {
				alert('Error during API call: ' + apiError)
				console.error('Error during API call:', apiError);
			});
	};
	
	return (
		<div className="recStepPrepContainer">
			
			{
				recording.steps[stepIndex].errors && recording.steps[stepIndex].errors.length > 0 ? (
					<RecordingStepPreparationErrorList recording={recording}
					                                   stepIndex={stepIndex}
					                                   handleDeleteStepError={handleDeleteStepError}
					                                   handleDeleteAllStepErrors={handleDeleteAllStepErrors} />
					
			
					): null
			}
			
			
			<div className="recStepPrepUpdateErrorContainer">
				<div className="recStepPrepOriginalText">
					Original Description: {recording.steps[stepIndex].description}
				</div>
				
				<div className="recStepPrepErrorTags">
					{errorTags.map((item) => (
						<div key={item} className="errorTagBox">
							<input
								className="errorTagCheckbox"
								type="checkbox"
								checked={selectedItems.has(item)}
								onChange={(e) => handleCheckboxChange(item, e.target.checked)}
							/>
							<label className="errorTagLabel">{item}</label>
						</div>
					))}
				</div>
				
				<div className="recStepPrepErrorDescription">
					<div className="recStepPrepErrorDescriptionText">
						Error Description:
					</div>
					<div className="recStepPrepInputText">
						<input className="inputTextField" type="text" value={errorText} onChange={handleErrorTextChange} />
					</div>
				</div>
				
				<div className="recStepPrepUpdateStepDescription">
					<div className="recStepPrepUpdateStepDescriptionText">
						Updated Step Description:
					</div>
					<div className="recStepPrepInputText">
						<input className="inputTextField" type="text" value={stepDescription} onChange={handleUpdateStepDescriptionChange} />
					</div>
				</div>
				
				<button onClick={handleClick} className="recStepPrepUpdateButton">
					Update Errors
				</button>
			</div>
		
		</div>
	);
};

export default RecordingStepPreparation;
