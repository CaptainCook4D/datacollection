import "./RecordingErrorHints.css";

const RecordingErrorHints = (props) => {
	
	const {errorHints} = props;
	
	return (
		<div className="recordingErrorHints">
			<table className="recordingErrorHintTable">
				<thead>
				<tr>
					<th>Tag</th>
					<th>Description</th>
				</tr>
				</thead>
				<tbody>
				{errorHints.map((row, index) => (
					<tr key={index}>
						<td>{row.tag}</td>
						<td>{row.description}</td>
					</tr>
				))}
				</tbody>
			</table>
		</div>
	);
	
};

export default RecordingErrorHints;
