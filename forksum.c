#include <errno.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <sys/wait.h>
#include <unistd.h>

/*
 * The program performs a parallel computation of an integer range sum. forksum.c receives a start and end value of an integer range and 
 * computes the sum of all numbers in that range. The range is split in two halves and two child processes are forked to compute the respective 
 * subproblem, until the recursion finally ends, when start and end of the range are the same. The program outputs the range sum and the number of forks.
 * You can use and modify this program for your benchmarkings.
 */

// The Result struct contains the result of the sum operation and a counter for the number of fork operations.
typedef struct Result {
	int sum;
	int num;
} Result;

// Declare functions to make them usable before the implementation.
Result forksum(int start, int end);
int parseInt(char *str, char *errMsg);

// spawnChild forks a subprocess to compute the sum with the given range of numbers. For computing the sum, the subprocess calls forksum().
// Before spawning the child process, spawnChild creates a bidirectional pipe. One side of the pipe is returned to the caller,
// the other side is used by the child process to output results.
int spawnChild(int start, int end) {
	int pipefd[2];
	if (pipe(pipefd) < 0) {
		perror("pipe");
		exit(1);
	}
	
	int child;
	while ((child = fork()) < 0) {
		perror("fork");
	}
	if (child == 0) {
		// In the child process: call forksum and write the results to our half of the pipe.
		Result result = forksum(start, end);

		close(pipefd[0]);
		FILE *stream = fdopen(pipefd[1], "w");
		if (!stream) {
			perror("fdopen child write pipe");
			exit(1);
		}
		fprintf(stream, "%d\n%d\n", result.sum, result.num);
		exit(0);
	}

	// This continues the parent process. Return our half of the pipe.
	close(pipefd[1]);
	return pipefd[0];
}

// readIntLine reads a line from the given FILE and parses its contents to an int using parseInt().
int readIntLine(FILE *stream, char *errorMsg) {
	size_t bufSize = 1024;
	char *line = malloc(bufSize);
	ssize_t len = getline(&line, &bufSize, stream);

	if (len < 0) {
		perror("read line from child");
		return 0;
	}
	line[len - 1] = '\0';
	return parseInt(line, errorMsg);
}

// readChild reads data from the given file descriptor and parses it to a Result struct.
// This reads the result data written by a child process in spawnChild().
Result readChild(int fd) {
	FILE *stream = fdopen(fd, "r");
	if (!stream) {
		perror("fdopen child read pipe");
		exit(1);
	}
	int sum = readIntLine(stream, "Failed to parse sum result from child");
	int num = readIntLine(stream, "Failed to parse num result from child");
	return (Result) {sum, num};
}

// forksum computes the sum of all numbers in the given range (inclusive) by spawning 2 child processes.
// One child computes the sum of the lower range, the other of the upper range.
// The two results are summed and returned.
// If the start and end parameters are equal, the result is returned directly. This is the break condition for the recursion.
Result forksum(int start, int end) {
	if (start >= end) {
		if (start > end)
			fprintf(stderr, "Start bigger than end: %d - %d\n", start, end);

		// The recursive fork arrived at a leaf process. Return our input and 1 to count this leaf process.
		return (Result) {start, 1};
	}
	
	// First, spawn child processes for the two sub-ranges. The result is a file descriptor for a buffer where the child will write its results.
	int mid = start + (end - start) / 2;
	int child1 = spawnChild(start, mid);
	int child2 = spawnChild(mid + 1, end);
	
	// Read the results from the two file descriptors.
	Result res1 = readChild(child1);
	Result res2 = readChild(child2);

	// Wait for the 2 child processes to exit and return the summed result.
	// Add 1 to the number of processes to count the current process.
	wait(0);
	wait(0);
	return (Result) {res1.sum + res2.sum, res1.num + res2.num + 1};
}

// parseInt is a helper function to parse an integer and exit with an error message, if parsing fails.
int parseInt(char *str, char *errMsg) {
	char *endptr = NULL;
	errno = 0;
	int result = strtol(str, &endptr, 10);
	if (errno != 0) {
		perror(errMsg);
		exit(1);
	}
	if (*endptr) {
		fprintf(stderr, "%s: %s\n", errMsg, str);
		exit(1);
	}
	return result;
}

// The main function parses the two command line arguments: The start and end of the number range to sum up.
// Afterwards, it calls forksum() with the two given parameters.
// After forksum() completes, the expected result of the sum is computed for validation, using the Gauß sum formula.
// The time for the forksum() function is measured and the number of forks per second is printed to the standard output.
int main(int argc, char **args) {
	// Parse parameters
	if (argc != 3) {
		fprintf(stderr, "Need 2 parameters: start and end\n");
		exit(1);
	}
	int start = parseInt(args[1], "Failed to parse start argument");
	int end = parseInt(args[2], "Failed to parse end argument");

	// Compute the result using forksum()
	Result result = forksum(start, end);

	// Compare the result to the expectation and print the result.
	int test = (end*(end+1)/2) - (start*(start+1)/2) + start;
	if (test == result.sum) {
		fprintf(stdout, "Correct result: %d\n", result.sum);
		fprintf(stdout, "Number of forks: %d\n", result.num);
		exit(0);
	} else {
		fprintf(stdout, "Wrong result: %d (should be: %d)\n", result.sum, test);
		exit(1);
	}
}
