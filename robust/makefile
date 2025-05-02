CC = gcc
CFLAGS = -Wall -Wextra -g -fopenmp -Iinc
LDFLAGS = -lm -fopenmp
SRCS = RWoperation.c inc/helper.c inc/pcg_basic.c
TARGET = RWoperation

$(TARGET): $(SRCS)
	$(CC) $(CFLAGS) $(SRCS) -o $(TARGET) $(LDFLAGS)

.PHONY: clean
clean:
	rm -f $(TARGET)