CC ?= gcc
CFLAGS ?= -std=c99 -Wall -Wextra -pedantic -O2 -fPIC
CPPFLAGS += -Iinclude

SRCDIR = .
OBJDIR = build
BINDIR = bin
LIBDIR = lib

SOURCES = fingerprint/fingerprint.c governor/governor.c rknn/rknn_adapter.c jetson/jetson_adapter.c
OBJECTS = $(OBJDIR)/fingerprint.o $(OBJDIR)/governor.o $(OBJDIR)/rknn_adapter.o $(OBJDIR)/jetson_adapter.o

TARGET_LIB = $(LIBDIR)/liblitrun_core.so
TARGET_PROBE = $(BINDIR)/litrun-probe
TARGET_TEST_FP = $(BINDIR)/test_fingerprint
TARGET_TEST_GOV = $(BINDIR)/test_governor
TARGET_TEST_RKNN = $(BINDIR)/test_rknn
TARGET_TEST_JETSON = $(BINDIR)/test_jetson

.PHONY: all shared test clean

all: $(TARGET_LIB) $(TARGET_PROBE)

shared: $(TARGET_LIB)

$(OBJDIR):
	mkdir -p $(OBJDIR)

$(BINDIR):
	mkdir -p $(BINDIR)

$(LIBDIR):
	mkdir -p $(LIBDIR)

$(OBJDIR)/fingerprint.o: fingerprint/fingerprint.c include/fingerprint.h | $(OBJDIR)
	$(CC) $(CFLAGS) $(CPPFLAGS) -c $< -o $@

$(OBJDIR)/governor.o: governor/governor.c include/governor.h | $(OBJDIR)
	$(CC) $(CFLAGS) $(CPPFLAGS) -c $< -o $@

$(OBJDIR)/rknn_adapter.o: rknn/rknn_adapter.c include/rknn_adapter.h | $(OBJDIR)
	$(CC) $(CFLAGS) $(CPPFLAGS) -c $< -o $@

$(OBJDIR)/jetson_adapter.o: jetson/jetson_adapter.c include/jetson_adapter.h | $(OBJDIR)
	$(CC) $(CFLAGS) $(CPPFLAGS) -c $< -o $@

$(TARGET_LIB): $(OBJECTS) | $(LIBDIR)
	$(CC) -shared $(OBJECTS) -o $@

$(TARGET_PROBE): tools/probe_main.c $(OBJECTS) | $(BINDIR)
	$(CC) $(CFLAGS) $(CPPFLAGS) tools/probe_main.c $(OBJECTS) -o $@

$(TARGET_TEST_FP): ../tests/core/test_fingerprint.c $(OBJECTS) | $(BINDIR)
	$(CC) $(CFLAGS) $(CPPFLAGS) $< $(OBJECTS) -o $@

$(TARGET_TEST_GOV): ../tests/core/test_governor.c $(OBJECTS) | $(BINDIR)
	$(CC) $(CFLAGS) $(CPPFLAGS) $< $(OBJECTS) -o $@

$(TARGET_TEST_RKNN): ../tests/core/test_rknn.c $(OBJECTS) | $(BINDIR)
	$(CC) $(CFLAGS) $(CPPFLAGS) $< $(OBJECTS) -o $@

$(TARGET_TEST_JETSON): ../tests/core/test_jetson.c $(OBJECTS) | $(BINDIR)
	$(CC) $(CFLAGS) $(CPPFLAGS) $< $(OBJECTS) -o $@

test: $(TARGET_TEST_FP) $(TARGET_TEST_GOV) $(TARGET_TEST_RKNN) $(TARGET_TEST_JETSON)
	@echo "--- Running C Unit Tests ---"
	./$(TARGET_TEST_FP)
	./$(TARGET_TEST_GOV)
	./$(TARGET_TEST_RKNN)
	./$(TARGET_TEST_JETSON)
	@echo "All C unit tests passed successfully!"

clean:
	rm -rf $(OBJDIR) $(BINDIR) $(LIBDIR)

