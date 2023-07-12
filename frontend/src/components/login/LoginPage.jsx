import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';
import API_BASE_URL from "../../config";

const LoginPage = (props) => {
	const { userData, setUserData, setEnvironment, setActivities, setUserStats} = props;
	
	const [username, setUsername] = useState('');
	const [password, setPassword] = useState('');
	const [error, setError] = useState('');
	
	const navigate = useNavigate();
	
	const handleSubmit = async (event) => {
		event.preventDefault();
		
		const LOGIN_URL = `${API_BASE_URL}/login`;
		const ENVIRONMENT_URL = `${API_BASE_URL}/environment`;
		const ACTIVITIES_URL = `${API_BASE_URL}/activities`;
		
		axios
			.post(LOGIN_URL, { username, password })
			.then((loginResponse) => {
				if (loginResponse.data) {
					setUserData(loginResponse.data);
				}
				return axios.get(ENVIRONMENT_URL);
			})
			.then((environmentResponse) => {
				if (environmentResponse.data) {
					setEnvironment(environmentResponse.data);
				}
				return axios.get(ACTIVITIES_URL);
			})
			.then((activitiesResponse) => {
				if (activitiesResponse.data) {
					setActivities(activitiesResponse.data);
				}
				navigate('/');
			})
			.catch((apiError) => {
				setError(apiError);
				alert('Invalid username or password. Please try again.')
			});
	};
	
	return (
		<div className="login-container">
			{/* Define Header component for the AppBar component also display tabs based on loggedIn state */}
			
			<h1>Data Collection Tool</h1>
			<form className="login-form" onSubmit={handleSubmit}>
				<input
					type="text"
					placeholder="Username"
					value={username}
					onChange={(event) => setUsername(event.target.value)}
				/>
				<input
					type="password"
					placeholder="Password"
					value={password}
					onChange={(event) => setPassword(event.target.value)}
				/>
				<button type="submit">Login</button>
			</form>
			{error && <p>{error}</p>}
		</div>
	);
};

export default LoginPage;
