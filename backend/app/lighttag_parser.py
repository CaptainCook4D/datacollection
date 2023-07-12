import itertools
import os
import os.path as osp
import json
import random
import sys

import networkx as nx
import matplotlib.pyplot as plt
import yaml

#
# def add_path(path):
# 	if path not in sys.path:
# 		sys.path.insert(0, path)
#
#
# def initialize_paths():
# 	this_dir = osp.dirname(__file__)
#
# 	lib_path = osp.join(this_dir, "..", "models")
# 	add_path(lib_path)
#
# 	lib_path = osp.join(this_dir, "..",  "services")
# 	add_path(lib_path)
#
# 	lib_path = osp.join(this_dir, "..", "hololens")
# 	add_path(lib_path)
#
# 	lib_path = osp.join(this_dir, "..", "post_processing")
# 	add_path(lib_path)
#
#
# initialize_paths()

from datacollection.user_app.backend.app.models.error import Error
from datacollection.user_app.backend.app.models.error_tag import ErrorTag
from datacollection.user_app.backend.app.models.step import Step
from datacollection.user_app.backend.app.utils.constants import LightTag_Constants as const
from datacollection.user_app.backend.app.utils.logger_config import get_logger

logger = get_logger(__name__)


def create_directories(dir_path):
	if not os.path.exists(dir_path):
		os.makedirs(dir_path)


def create_tag_mappings(activity_json):
	tag_to_tag_id = {}
	tag_id_to_tag = {}
	for tag_node in activity_json[const.SCHEMA][const.TAGS]:
		tag_to_tag_id[tag_node[const.NAME]] = tag_node[const.ID]
		tag_id_to_tag[tag_node[const.ID]] = tag_node[const.NAME]
	return tag_to_tag_id, tag_id_to_tag


def create_annotation_mappings(activity_json):
	tagged_token_id_to_tag_id = {}
	tag_id_to_tagged_token_id = {}
	tagged_token_id_to_value = {}
	for annotation_node in activity_json[const.EXAMPLES][0][const.ANNOTATIONS]:
		tagged_token_id_to_tag_id[annotation_node[const.TAGGED_TOKEN_ID]] = annotation_node[const.TAG_ID]
		tag_id_to_tagged_token_id[annotation_node[const.TAG_ID]] = annotation_node[const.TAGGED_TOKEN_ID]
		tagged_token_id_to_value[annotation_node[const.TAGGED_TOKEN_ID]] = annotation_node[const.VALUE]
	return tagged_token_id_to_tag_id, tag_id_to_tagged_token_id, tagged_token_id_to_value


def create_relation_mappings(activity_json, tag_id_to_tag, tagged_token_id_to_tag_id, tagged_token_id_to_value):
	relation_id_to_tagged_token = {}
	relation_id_to_tag = {}
	relation_id_to_children = {}
	relation_id_to_tagged_token_id = {}
	for relation_node in activity_json[const.RELATIONS]:
		relation_id_to_tagged_token[relation_node[const.ID]] = tagged_token_id_to_value[
			relation_node[const.TAGGED_TOKEN_ID]]
		relation_id_to_tag[relation_node[const.ID]] = tag_id_to_tag[
			tagged_token_id_to_tag_id[relation_node[const.TAGGED_TOKEN_ID]]]
		relation_id_to_children[relation_node[const.ID]] = relation_node[const.CHILDREN]
		relation_id_to_tagged_token_id[relation_node[const.ID]] = relation_node[const.TAGGED_TOKEN_ID]
	return relation_id_to_tagged_token, relation_id_to_tag, relation_id_to_children, relation_id_to_tagged_token_id


def find_topological_orderings(dependency_graph, num_terminals=5):
	orderings = []
	
	def topological_sort(graph, visited, stack):
		if not graph:
			orderings.append(stack)
			return
		
		# Only include a sample of 1 from terminal nodes
		terminal_nodes = [node for node in graph if graph.in_degree()[node] == 0]
		random.shuffle(terminal_nodes)
		sampled_nodes = random.sample(terminal_nodes, min(num_terminals, len(terminal_nodes)))
		for node in sampled_nodes:
			if node not in visited:
				new_visited = visited | {node}
				new_graph = graph.subgraph([n for n in graph if n not in new_visited])
				topological_sort(new_graph, new_visited, stack + [node])
	
	topological_sort(dependency_graph, set(), [])
	return orderings


def fetch_activity_programs(topological_orderings, num_programs):
	num_topological_orders = len(topological_orderings)
	if num_topological_orders > num_programs:
		activity_programs = random.sample(topological_orderings, num_programs)
	else:
		activity_programs = topological_orderings.copy()
		for idx in range(num_programs - num_topological_orders):
			activity_programs.append(random.choice(topological_orderings))
	return activity_programs


class LightTagParser:
	
	def __init__(self, data_directory):
		self.data_directory = data_directory
		self.activity_data_directory = os.path.join(self.data_directory, "lighttag", "v2")
		self.recording_data_directory = os.path.join(self.data_directory, "recordings", "v2")
		self.dependency_graph_data_directory = os.path.join(self.data_directory, "graphs", "v2")
		
		create_directories(self.activity_data_directory)
		create_directories(self.recording_data_directory)
		create_directories(self.dependency_graph_data_directory)
	
	def generate_dependency_graph(self, activity_file_name):
		logger.info("--------------------------------------------------------------------------- \n")
		activity_path = os.path.join(self.activity_data_directory, activity_file_name)
		with open(activity_path) as activity_file:
			activity_json = json.load(activity_file)
		
		# 1. Generate Map and Inverse Map of Tags and Tag ID from schema
		tag_to_tag_id, tag_id_to_tag = create_tag_mappings(activity_json)
		
		# 2. Generate Map and Inverse Map of Tagged Token ID and Tag ID
		tagged_token_id_to_tag_id, tag_id_to_tagged_token_id, tagged_token_id_to_value = create_annotation_mappings(
			activity_json)
		
		# 3. Generate a Map of Relation ID and value
		relation_id_to_tagged_token, relation_id_to_tag, relation_id_to_children, relation_id_to_tagged_token_id = create_relation_mappings(
			activity_json, tag_id_to_tag, tagged_token_id_to_tag_id, tagged_token_id_to_value)
		
		# 4. Start generating a graph based on Nodes
		# Node ID - [Tag: Step Value] - Network X
		# Children - [List Nodes]
		# Have a map of {Node ID: Node}
		graph = nx.DiGraph()
		
		# Create map, inverse map of the node label and step information
		step_counter = 0
		node_id_to_step_info = {}
		step_info_to_node_id = {}
		node_id_to_step_id = {}
		
		relation_id_to_node_id = {}
		node_id_to_node_attributes = {}
		node_id_to_tagged_token_id = {}
		
		node_id_to_children = {}
		node_id_to_parent = {}
		start_node_id = "start_node"
		graph.add_node(start_node_id, label="START")
		node_id_to_step_info[step_counter] = "START"
		step_info_to_node_id["START"] = start_node_id
		node_id_to_step_id[start_node_id] = step_counter
		step_counter += 1
		
		# 5. Add all nodes to the graph with Node ID as attribute
		for relation_node in activity_json[const.RELATIONS]:
			
			# Terminal Node in LightTag graph, no need to create a node for it - [Step Node] in LightTag
			if len(relation_node[const.CHILDREN]) < 1:
				continue
			
			step_info = None
			node_attributes = {}
			tagged_token = relation_id_to_tagged_token[relation_node[const.ID]]
			for child_id in relation_node[const.CHILDREN]:
				child_tag = relation_id_to_tag[child_id]
				if child_tag == const.STEP:
					# Assigns node-id as : node_id-put-"put onion into box"
					step_info = relation_id_to_tagged_token[child_id]
					break
			
			node_attributes[const.ACTION] = tagged_token
			node_attributes[const.STEP] = step_info
			node_label = f'{tagged_token}-{step_info}'
			
			node_id = f'{relation_node[const.TAGGED_TOKEN_ID]}:{tagged_token}:{step_info}'
			
			relation_id_to_node_id[relation_node[const.ID]] = node_id
			node_id_to_node_attributes[node_id] = node_attributes
			node_id_to_tagged_token_id[node_id] = relation_node[const.TAGGED_TOKEN_ID]
			
			node_label = step_counter
			node_id_to_step_info[step_counter] = step_info
			step_info_to_node_id[step_info] = node_id
			node_id_to_step_id[node_id] = step_counter
			step_counter += 1
			
			node_id_to_children[node_id] = []
			node_id_to_parent[node_id] = []
			
			graph.add_node(node_id, label=node_label, **node_attributes)
		
		edge_list = []
		for relation_node in activity_json[const.RELATIONS]:
			
			if len(relation_node[const.CHILDREN]) < 1:
				continue
			
			parent_node_id = relation_id_to_node_id[relation_node[const.ID]]
			for child_id in relation_node[const.CHILDREN]:
				
				if relation_id_to_tag[child_id] == const.STEP:
					continue
				
				try:
					child_node_id = relation_id_to_node_id[child_id]
				except KeyError:
					# tagged_token = relation_id_to_tagged_token[child_id]
					# child_node_id = f'{child_id}-{tagged_token}'
					# child_node_label = tagged_token
					# relation_id_to_node_id[child_id] = child_node_id
					#
					# graph.add_node(child_node_id, label=child_node_label)
					logger.error(f"Exception occurred in adding the edge from {child_id} to {parent_node_id}")
					# continue
					child_tagged_token_id = relation_id_to_tagged_token_id[child_id]
					child_node_id = [node_id for node_id, tagged_token_id in node_id_to_tagged_token_id.items() if
					                 tagged_token_id == child_tagged_token_id][0]
					
					logger.info(f"Adding the edge from {child_node_id} to {parent_node_id}")
				
				graph.add_edge(child_node_id, parent_node_id)
				edge_list.append((node_id_to_step_id[child_node_id], node_id_to_step_id[parent_node_id]))
				
				if parent_node_id not in node_id_to_children:
					node_id_to_children[parent_node_id] = []
				node_id_to_children[child_node_id].append(parent_node_id)
				node_id_to_parent[parent_node_id].append(child_node_id)
		
		for node_id, parents in node_id_to_parent.items():
			if len(parents) < 1:
				graph.add_edge(start_node_id, node_id)
				edge_list.append((0, node_id_to_step_id[node_id]))
		
		end_node_id = "end_node"
		graph.add_node(end_node_id, label="END")
		node_id_to_step_info[step_counter] = "END"
		step_info_to_node_id["END"] = end_node_id
		node_id_to_step_id[end_node_id] = step_counter
		
		for node_id, children in node_id_to_children.items():
			if len(children) < 1:
				graph.add_edge(node_id, end_node_id)
				edge_list.append((node_id_to_step_id[node_id], step_counter))
		step_counter += 1
		
		recording_dict = {"steps": node_id_to_step_info, "edges": edge_list}
		with open(os.path.join(self.recording_data_directory, activity_file_name), "w") as recording_text_file:
			recording_text_file.write(json.dumps(recording_dict))
		
		plt.figure(figsize=(50, 50), dpi=150)
		
		# labels = nx.get_node_attributes(graph, const.LABEL)
		# nx.draw_planar(
		# 	graph,
		# 	arrowsize=8,  # smaller arrows
		# 	with_labels=True,
		# 	node_size=10000,  # larger nodes
		# 	node_color="#ffff8f",
		# 	linewidths=2.0,
		# 	width=1.0,  # smaller edge width
		# 	font_size=30,  # larger font
		# 	labels=labels
		# )
		#
		# dependency_graph_path = os.path.join(self.dependency_graph_data_directory, f'{activity_file_name[:-5]}.png')
		# plt.savefig(dependency_graph_path)
		# plt.clf()
		#
		# # print(graph.nodes)
		# logger.info(f"Finished processing {activity_file_name}")
		# # print(graph.edges)
		# logger.info("--------------------------------------------------------------------------- \n")
		#
		# 6. Return graph
		return graph
	
	def generate_activity_recording_data(self, activity_file_name):
		dependency_graph = self.generate_dependency_graph(activity_file_name)
		
		terminal_node_map = {
			"broccolistirfry.json": 2,
			"gardenfreshsweetcornsalsa.json": 2,
			"scrambledeggs.json": 2,
			"spicymasalabread.json": 2
		}
		
		num_terminals = 5
		if activity_file_name in terminal_node_map:
			num_terminals = terminal_node_map[activity_file_name]
		
		topological_orderings = find_topological_orderings(dependency_graph, num_terminals=num_terminals)
		
		valid_programs = fetch_activity_programs(topological_orderings, const.NUM_VALID_PROGRAMS)
		invalid_programs = fetch_activity_programs(topological_orderings, const.NUM_INVALID_PROGRAMS)
		
		program_dict_list = self._generate_program_dicts(valid_programs, invalid_programs)
		
		activity_recording_file_path = os.path.join(self.recording_data_directory, activity_file_name[:-5])
		with open(activity_recording_file_path, 'w') as activity_recording_file:
			yaml.dump(program_dict_list, activity_recording_file)
	
	def _generate_program_dicts(self, valid_programs, invalid_programs):
		program_dicts = []
		
		for i, program in enumerate(valid_programs):
			program_dict = self._generate_program_dict(program, i + 1, is_valid=True)
			program_dicts.append(program_dict)
		
		for i, program in enumerate(invalid_programs):
			program_dict = self._generate_program_dict(program, i + 1 + const.NUM_VALID_PROGRAMS, is_valid=False)
			program_dicts.append(program_dict)
		
		return program_dicts
	
	def _generate_program_dict(self, program, program_counter, is_valid):
		program_dict = {const.RECORDING_ID: program_counter}
		step_dicts = [self._step_dict_from_program_step(step) for step in program]
		
		if not is_valid:
			step_dicts, error_dicts = self._add_errors(step_dicts, program_counter, const.NUM_VALID_PROGRAMS)
			if len(error_dicts) > 0:
				program_dict[const.ERRORS] = error_dicts
		
		program_dict[const.STEPS] = step_dicts
		
		return program_dict
	
	def _step_dict_from_program_step(self, program_step):
		step_description = "-".join(program_step.split(":")[-2:])
		return Step(step_description).to_dict()
	
	def _add_errors(self, step_dicts, program_counter, base_counter):
		# Order errors for all the invalid programs > 10
		# Missing step for all the invalid programs < 30
		if program_counter > const.THRESHOLD_NUM_MISSING_STEPS + base_counter:
			step_dicts = self._shuffle_steps(step_dicts)
		
		error_dicts = []
		filtered_step_dicts = []
		
		for step_dict in step_dicts:
			if program_counter < const.THRESHOLD_NUM_MISSING_STEPS_ORDER_ERRORS + base_counter and random.random() < 0.1:
				error_dicts.append(Error(ErrorTag.MISSING_STEP, step_dict[const.DESCRIPTION]).to_dict())
			else:
				filtered_step_dicts.append(step_dict)
		
		if program_counter > const.THRESHOLD_NUM_MISSING_STEPS + base_counter:
			error_dicts.append(Error(ErrorTag.ORDER_ERROR).to_dict())
		
		return filtered_step_dicts, error_dicts
	
	def _shuffle_steps(self, step_dicts):
		num_to_shuffle = len(step_dicts) // 5
		indices_to_shuffle = random.sample(range(len(step_dicts)), num_to_shuffle)
		
		for i in indices_to_shuffle:
			random_index = random.randint(0, len(step_dicts) - 1)
			step_dicts[i], step_dicts[random_index] = step_dicts[random_index], step_dicts[i]
		
		return step_dicts
	
	def generate_recording_data(self):
		# self.generate_activity_recording_data("microwavemugpizza.json")
		for activity_file_name in os.listdir(self.activity_data_directory):
			self.generate_activity_recording_data(activity_file_name)
	
	def generate_dependency_graphs(self):
		for activity_file_name in os.listdir(self.activity_data_directory):
			dependency_graph = self.generate_dependency_graph(activity_file_name)


if __name__ == "__main__":
	info_directory = r"C:\Users\rohit\PycharmProjects\skillearn\datacollection\user_app\backend\info_files"
	parser = LightTagParser(info_directory)
	parser.generate_dependency_graphs()
