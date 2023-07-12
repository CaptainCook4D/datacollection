import React from 'react';
import './RecordingRequiredItems.css';

const RequiredItemsTable = ({ requiredItems }) => {
	const tableData = requiredItems.map((item, index) => {
		const key = Object.keys(item)[0];
		const value = item[key];
		return { index: parseInt(key, 10) || index + 1, value };
	});
	
	return (
		<table className="rec-req-items-table">
			<thead>
			<tr>
				<th className="rec-req-table-header">Item</th>
			</tr>
			</thead>
			<tbody>
			{tableData.map((row, index) => {
				if (row.value != null && row.value !== "") {
					return (
						<tr
							key={row.index}
							className={`rec-req-table-row ${
								index % 2 === 0 ? "rec-req-even-row" : "rec-req-odd-row"
							}`}
						>
							<td className="rec-req-table-cell">{row.value}</td>
						</tr>
					);
				}
				return null;
			})}
			</tbody>
		</table>
	);
	
};

export default RequiredItemsTable;
