import multiprocessing

URL = "http://www.umich.edu/~umfandsf/other/ebooks/alice30.txt"   # if file is read from a remote URL
FILE_NAME = "alice30.txt"
NUMBER_THREADS = 4
#NUMBER_THREADS = multiprocessing.cpu_count()

BATCH_MODE = True       # process file in batches
BATCH_SIZE = 1000	# size in number of lines for each batch


LOWERCASE = True        # use lower case