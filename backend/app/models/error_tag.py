# import Levenshtein
# import numpy as np
# import gensim.downloader as api
# from rapidfuzz.distance.metrics_cpp import jaro_winkler_similarity


class ErrorTag:
	PREPARATION_ERROR = "Preparation Error"
	MEASUREMENT_ERROR = "Measurement Error"
	ORDER_ERROR = "Order Error"
	TIMING_ERROR = "Timing Error"
	TECHNIQUE_ERROR = "Technique Error"
	TEMPERATURE_ERROR = "Temperature Error"
	MISSING_STEP = "Missing Step"
	OTHER = "Other"
	
	# Pretrained for word2vec embeddings
	# wv = api.load('word2vec-google-news-300')
	# wv = api.load("glove-twitter-25")
	
	mistake_tag_list = [PREPARATION_ERROR, MEASUREMENT_ERROR, ORDER_ERROR, TIMING_ERROR,
	                    TECHNIQUE_ERROR, TEMPERATURE_ERROR, MISSING_STEP]
	
	@classmethod
	def get_step_error_tag_list(cls):
		return [cls.PREPARATION_ERROR, cls.MEASUREMENT_ERROR, cls.TIMING_ERROR,
		        cls.TECHNIQUE_ERROR, cls.TEMPERATURE_ERROR, cls.MISSING_STEP, cls.ORDER_ERROR, cls.OTHER]
	
	@classmethod
	def get_recording_error_tag_list(cls):
		return [cls.PREPARATION_ERROR, cls.MEASUREMENT_ERROR, cls.TIMING_ERROR,
		        cls.TECHNIQUE_ERROR, cls.TEMPERATURE_ERROR, cls.OTHER, cls.MISSING_STEP, cls.ORDER_ERROR]
	
	@classmethod
	def get_similarity_score(cls, sample_tag, tag) -> float:
		
		return 0
		
		# # get embeddings for the strings
		# try:
		# 	sample_tag_embedding = cls.wv[sample_tag]
		# except KeyError:
		# 	return 0
		# try:
		# 	tag_embedding = cls.wv[tag]
		# except KeyError:
		# 	return 0
		#
		# # compute cosine similarity
		# cosine_similarity_score = np.dot(sample_tag_embedding, tag_embedding) / (
		# 			np.linalg.norm(sample_tag_embedding) * np.linalg.norm(tag_embedding))
		# return cosine_similarity_score
	
	# @classmethod
	# def get_best_tag(cls, sample_tag) -> str:
	#
	# 	if sample_tag == cls.OTHER:
	# 		return cls.OTHER
	# 	else:
	# 		closest_tag = None
	# 		max_similarity_score = 0
	#
	# 		for tag in cls.mistake_tag_list:
	# 			# check if the strings are exactly the same
	# 			if sample_tag == tag:
	# 				return sample_tag
	#
	# 			# Check the Levenshtein distance between the strings
	# 			levenshtein_distance = Levenshtein.distance(sample_tag, tag)
	# 			if levenshtein_distance <= 1:
	# 				return tag
	#
	# 			# Check the Jaro-Winkler similarity between the strings
	# 			jaro_winkler_similarity_score = jaro_winkler_similarity(sample_tag, tag)
	# 			if jaro_winkler_similarity_score >= 0.9:
	# 				return tag
	#
	# 			# Check the cosine similarity between the embeddings
	# 			cosine_similarity_score = cls.get_similarity_score(sample_tag, tag)
	# 			if cosine_similarity_score >= max_similarity_score:
	# 				max_similarity_score = cosine_similarity_score
	# 				closest_tag = tag
	#
	# 		# if no match is found, return the default value
	# 		if max_similarity_score < 0.7:
	# 			return cls.OTHER
	#
	# 		return closest_tag
