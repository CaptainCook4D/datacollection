import React from 'react';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';

const ActivityTable = (props) => {
	
	const {activityIdList, activities, label} = props;
	
	const getActivityName = (id) => {
		const activity = activities.find((activity) => activity.id === id);
		return activity ? activity.name : "Unknown";
	};
	
	// Define the styles
	const styles = {
		tableRow: {
			backgroundColor: '#f2f2f2',
			'&:hover': {
				backgroundColor: '#e0e0e0',
			}
		},
		labelCell: {
			fontWeight: 'bold',
			backgroundColor: '#d5d5d5',
		}
	};
	
	return (
		
		<div>
			
			<TableContainer component={Paper}>
				<Table sx={{ minWidth: 70 }} aria-label="simple table">
					<TableHead>
						<TableRow>
							<TableCell sx={styles.labelCell}>{label}</TableCell>
						</TableRow>
					</TableHead>
					<TableBody>
						{
							activityIdList.map((activityId) => (
								<TableRow
									key={getActivityName(activityId)}
									sx={{ ...styles.tableRow, '&:last-child td, &:last-child th': { border: 0 } }}
								>
									<TableCell component="th" scope="row">
										{getActivityName(activityId)}
									</TableCell>
								</TableRow>
							))
						}
					
					</TableBody>
				</Table>
			</TableContainer>
		
		
		</div>
	
	)
	
	
}

export default ActivityTable;
