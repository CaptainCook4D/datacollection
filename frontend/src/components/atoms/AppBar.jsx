import { useState } from "react";
import React from "react";
import { useNavigate } from "react-router-dom";
import "./AppBar.css";

const AppBar = ({ userData }) => {
	const navigate = useNavigate();
	const [activeTab, setActiveTab] = useState(0);
	
	const handleTabClick = (index) => {
		setActiveTab(index);
		switch (index) {
			case 0:
				navigate("/");
				break;
			case 1:
				navigate("/preferences");
				break;
			case 2:
				navigate("/recording");
				break;
			case 3:
				navigate("/review");
				break;
			case 4:
				navigate("/annotationreview");
				break;
			case 5:
				navigate("/labelstudio");
				break;
			case 6:
				navigate("/actionannotation");
				break;
			default:
				break;
		}
	};
	
	const handleLogout = () => {
		// onLogout(); // Pass the logout function as a prop
		navigate("/login");
	};
	
	return (
		<div className="app-bar">
			{
				userData ? (
					<>
						<Tabs activeTab={activeTab} onTabClick={handleTabClick}>
							<Tab label="Home" />
							<Tab label="Preferences" />
							<Tab label="Recording" />
							<Tab label="Review" />
							<Tab label="Annotation Review" />
							<Tab label="Label Studio" />
							<Tab label="Action Annotation" />
						</Tabs>
						<button className="logout-button" onClick={handleLogout}>
							Logout
						</button>
					</>
				) : (
					<Tabs>
						DATA COLLECTION TOOL
					</Tabs>
				)
			}
		</div>
	);
};

const Tabs = ({ activeTab, onTabClick, children }) => {
	return (
		<div className="tabs">
			{React.Children.map(children, (child, index) => {
				return React.cloneElement(child, {
					active: index === activeTab,
					onClick: () => onTabClick(index),
				});
			})}
		</div>
	);
};

const Tab = ({ label, active, onClick }) => {
	return (
		<div
			className={`tab ${active ? "active" : ""}`}
			onClick={onClick}
		>
			{label}
		</div>
	);
};

export default AppBar;
