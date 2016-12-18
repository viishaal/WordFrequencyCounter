from urllib2 import urlopen
import re
import threading
import operator
import sys
import time

import config
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
# app.config.update(dict(
# 	DATABASE=os.path.join(app.root_path, 'logs.db'),
# 	SECRET_KEY='development key'
# ))
# app.config.from_envvar('FLASKR_SETTINGS', silent=True)


cached_objects = {}     ## cache of objects initalized


class WordFrequencyCounter:

	frequency_dict = {}        # final dictionary
	data = []
	process_indices = []
	threads = []
	intermediate_dicts = []
	num_threads = config.NUMBER_THREADS
	log = []
	file_object = None

	def __init__(self, url, file_name):
		self.url = url
		self.file_name = file_name

		try:
			if url:
				lines = urlopen(self.url).readlines()
			elif file_name:
				if config.BATCH_MODE:  ## in batch mode just create the file object
					self.file_object = open(file_name, "r")
				else:
					lines = open(file_name, "r").readlines()
			else:
				raise Exception("Neither url nor file_name specified ... aborting")
		except Exception as inst:
			print inst
			sys.exit()

		if not config.BATCH_MODE:
			for line in lines:
				line = line.strip()
				if len(line) != 0:
					self.data.append(line)

			if len(self.data) < config.NUMBER_THREADS:      
				self.num_threads = 1    # small sized input? just run in a single thread

		#print len(self.data), config.NUMBER_THREADS, self.num_threads

	def prepare_batch(self, _batch):
		self.data = []
		for l in _batch:
			l = l.strip()
			if len(l) != 0:   ## ignore empty lines
				self.data.append(l)

	def allocate_work(self):
		# init indexes
		self.process_indices = []
		self.process_indices.append(0)

		total_lines = len(self.data)
		per_thread = total_lines/self.num_threads
		self.process_indices += [i for i in range(per_thread, total_lines + 1, per_thread)]
		self.process_indices[self.num_threads] = total_lines

	def _worker_thread(self, thread_idx): 
		start_idx = self.process_indices[thread_idx - 1]
		end_idx   = self.process_indices[thread_idx]
		#print "Thread number ", thread_idx, start_idx, end_idx
		_freq_dict = {}

		start = time.time()
		for i in range(start_idx, end_idx):
			# split into words
			words = self.data[i].split()
			for word in words:
				# check if abbreviation
				#clean_start = re.sub("^[^a-zA-Z0-9]+", "", word)
				#clean_end = re.sub("[^a-zA-Z0-9]+$", "", clean_start)
				if len(word) > 0:
					# just remove all special characters punctuation marks for now
					clean = re.sub("[^a-zA-Z0-9]+", "", word)
					if config.LOWERCASE:
						clean = clean.lower()

					if clean in _freq_dict:
						_freq_dict[clean] += 1
					else:
						_freq_dict[clean] = 1

		end = time.time()

		s = "Time taken by thread ", thread_idx, end - start, " for number of entries: ", end_idx, start_idx
		#self.log.append(s)
		self.intermediate_dicts.append(_freq_dict)


	def merge_dictionaries(self, dict1, dict2):
		""" merges dictionary 2 into dictionary 1

		Args:
			dict1: dictionary 1
			dict2: dictionary 2

		Returns:
			dict1
		"""

		for (k,v) in dict2.items():
			if k in dict1:
				dict1[k] += v
			else:
				dict1[k] = v

		return dict1


	def count_frequencies_batch(self):
		""" processes self.data in threads
		
			Args:
				self

			Returns:
				sorted_list of (word, frequency) tuples if running without batch mode

		"""

		start = time.time()
		self.allocate_work()
		self.intermediate_dicts = []  ## reset

		# start execution of each thread
		for thread_idx in range(0, self.num_threads):
			t = threading.Thread(target = self._worker_thread, args = (thread_idx + 1, ))
			t.daemon = True
			self.threads.append(t)
			t.start()

		# join threads
		for t in self.threads:
			t.join()
		
		final_merged = self.intermediate_dicts[0]

		# merge results (in threads?)
		if len(self.intermediate_dicts) > 1:
			for d in self.intermediate_dicts[1:]:
				final_merged = self.merge_dictionaries(final_merged, d)

		end = time.time()

		# output
		for l in self.log:
			print l

		#print "merging time ", end - start
		if not config.BATCH_MODE:
			sorted_list = sorted(final_merged.items(), key = operator.itemgetter(1), reverse=True)
			return sorted_list
		else:
			return final_merged


	def count_frequencies(self):
		""" counts frequencies of words in the given document

		Args:
			self

		Returns:
			a list of tuples such as [('the', 15), ('to', 13), ('a', 12), ('of', 10), ('and', 10)]
			first element of the tuple is the word itself and second is its count (in descending order) in the document analysed

		Example:
		>>> w = WordFrequencyCounter(None, FILE_NAME)
		>>> print w.count_frequencies()

		"""

		if config.BATCH_MODE:
			_batch = []
			idx = 0
			for line in self.file_object:
				idx = idx + 1
				if idx % config.BATCH_SIZE == 0:   ## process this batch
					print "Processing BATCH number: {}".format(idx/config.BATCH_SIZE)
					self.prepare_batch(_batch)
					intermediate_dict = self.count_frequencies_batch()
					self.merge_dictionaries(self.frequency_dict, intermediate_dict)
					_batch = []   ## reset batch
				else:
					_batch.append(line)

			if len(_batch) > 0:
				print "Processing BATCH number: {}".format(idx/config.BATCH_SIZE + 1)
				self.prepare_batch(_batch)
				intermediate_dict = self.count_frequencies_batch()
				self.merge_dictionaries(self.frequency_dict, intermediate_dict)

			sorted_list = sorted(self.frequency_dict.items(), key = operator.itemgetter(1), reverse=True)
			return sorted_list
		else:
			self.frequency_dict = self.count_frequencies_batch()
			return self.frequency_dict

	def get_frequency(self, input_word):
		""" counts frequencies of words in the given document

		Args:
			input_word whose frequency count is to be determined

		Returns:
			frequency of the input_word as found in self.frequency_dict

		"""

		if input_word not in self.frequency_dict:
			return 0
		else:
			return self.frequency_dict[input_word]


@app.route('/wordcount', methods=['GET', 'POST'])
def wordcount():
	start_time = time.time()
	filename = request.args.get('filename', '')
	input_word = request.args.get('foo', '')

	result = {}
	result["counts"] = []

	if filename in cached_objects:
		result["counts"].append(cached_objects[filename].get_frequency(input_word))
	else:
		wc = WordFrequencyCounter(None, filename)
		wc.count_frequencies()
		result["counts"].append(wc.get_frequency(input_word))
		cached_objects[filename] = wc
		
	return jsonify(results = result["counts"])


if __name__ == "__main__":
	w = WordFrequencyCounter(None, config.FILE_NAME)
	w.count_frequencies()
	print w.get_frequency("alice")

