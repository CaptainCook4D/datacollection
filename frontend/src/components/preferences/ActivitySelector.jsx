import React, { useEffect, useState } from "react";
import axios from "axios";
import { Box, Button, Checkbox, FormControlLabel, Typography } from "@mui/material";
import "./ActivitySelector.css";
import {useNavigate} from "react-router-dom";
import API_BASE_URL from "../../config";


const ActivitySelector = (props) => {
	
	const { activities, activityPreferences, activityCategory, setUserData, userId } = props;
	
	const navigate = useNavigate();
	const [selectedActivities, setSelectedActivities] = useState([]);
	const [categoryActivities, setCategoryActivities] = useState([]);
	
	useEffect(() => {
		const categoryActivities = activities.filter((activity) => activity.category === activityCategory);
		setCategoryActivities(categoryActivities);
		
		const categoryActivityPreferences = activityPreferences.filter((activityId) => {
			const activity = activities.find((activity) => activity.id === activityId);
			return activity.category === activityCategory;
		});
		setSelectedActivities(categoryActivityPreferences);
		
	}, [activityCategory, activityPreferences, activities]);
	
	const handleSelectAll = () => {
		const allActivityIds = categoryActivities.map((activity) => activity.id);
		setSelectedActivities(allActivityIds);
	};
	
	const handleUnselectAll = () => {
		setSelectedActivities(activityPreferences);
	};
	
	const handleActivitySelect = (activityId) => {
		if (selectedActivities.includes(activityId)) {
			setSelectedActivities(
				selectedActivities.filter((id) => id !== activityId)
			);
		} else {
			setSelectedActivities([...selectedActivities, activityId]);
		}
	};
	
	const handleApiRequest = () => {
		let url = `${API_BASE_URL}/users/${userId}/preferences/${activityCategory}`;
		axios.post(url, { selectedActivities })
			.then((response) => {
				setUserData(response.data);
				navigate("/preferences");
			})
			.catch((error) => {
				alert("Error updating preferences. Please try again later.")
				console.log(error);
			});
	};
	
	return (
		<Box className="activitySelector">
			<Typography variant="h6">{activityCategory} Preference Selector</Typography>
			<Box className="checkboxControls">
				<FormControlLabel
					control={
						<Checkbox
							id="select-all"
							onChange={handleSelectAll}
							checked={selectedActivities.length === activities.length}
						/>
					}
					label="Select All"
				/>
				<FormControlLabel
					control={
						<Checkbox
							id="unselect-all"
							onChange={handleUnselectAll}
							checked={selectedActivities.length === 0}
						/>
					}
					label="Undo Select All"
				/>
			</Box>
			<Box>
				{categoryActivities.map((activity) => (
					<FormControlLabel
						key={activity.id}
						htmlFor={`activity-${activity.id}`}
						control={
							<Checkbox
								id={`activity-${activity.id}`}
								value={activity.id}
								onChange={() => handleActivitySelect(activity.id)}
								checked={selectedActivities.includes(activity.id)}
							/>
						}
						label={activity.name}
						className="activityItem" // Apply the CSS class
					/>
				))}
			</Box>
			<Button variant="contained" onClick={handleApiRequest}>
				Update {activityCategory} Preferences
			</Button>
		</Box>
	);
};

export default ActivitySelector;
