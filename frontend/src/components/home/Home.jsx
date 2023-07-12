import {useNavigate} from "react-router-dom";
import AppBar from "../atoms/AppBar";
import React, {useEffect, useState} from "react";
import axios from "axios";
import API_BASE_URL from "../../config";
import "./Home.css";

const ErrorStatsTable = ({ errorStats }) => {
	return (
		<div className="home-table-container">
			<div className="home-table-header">
				<div>Error Type</div>
				<div>Count</div>
			</div>
			{Object.entries(errorStats).map(([errorType, count]) => (
				<div className="home-table-row" key={errorType}>
					<div>{errorType}</div>
					<div>{count}</div>
				</div>
			))}
		</div>
	);
};


const RecordingStatsTable = ({ recordingStats }) => {
	const {
		number_of_correct_recordings,
		number_of_error_recordings: number_of_error_recordings,
		number_of_recordings,
	} = recordingStats;
	
	return (
		<div className="home-table-container">
			<div className="home-table-header">
				<div>Recording Type</div>
				<div>Count</div>
			</div>
			<div className="home-table-row home-CorrectRecordingsRow">
				<div>Correct Recordings</div>
				<div>{number_of_correct_recordings}</div>
			</div>
			<div className="home-table-row home-ErrorRecordingsRow">
				<div>Error Recordings</div>
				<div>{number_of_error_recordings}</div>
			</div>
			<div className="home-table-row home-TotalRecordingsRow">
				<div>Total Recordings</div>
				<div>{number_of_recordings}</div>
			</div>
		</div>
	);
};


const Home = (props) => {
	const { userData, environment, activities } = props;
	const navigate = useNavigate();
	
	const [userStats, setUserStats] = useState({
		error_stats: {},
		recording_stats: {},
		user_recording_stats: [],
	});
	
	const fetchUserStats = () => {
		// this function will fetch the user stats from the backend
		// and set the userStats state
		const STATS_URL = `${API_BASE_URL}/users/${userData.id}/stats`;
		axios
			.get(STATS_URL)
			.then((response) => {
				setUserStats(response.data);
			})
			.catch((error) => {
				console.log(error);
				alert("Error: " + error)
			});
	};
	
	useEffect(() => {
		if (!userData) {
			navigate("/login");
		}
		
		fetchUserStats();
	}, [userData]);
	
	return (
		<div className="homeContainer">
			<div className="header">
				<AppBar userData={userData} />
			</div>
			
			<div className="homeBodyContainer">
				<div className="homeLeftColumn">
					<h2>RECORDING STATS</h2>
					<RecordingStatsTable recordingStats={userStats.recording_stats} />
				</div>
				
				<div className="homeRightColumn">
					<h2>ERROR STATS</h2>
					<ErrorStatsTable errorStats={userStats.error_stats} />
				</div>
			</div>
		</div>
	);
};

export default Home;