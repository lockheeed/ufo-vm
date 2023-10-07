#include <windows.h>
#include <iostream>
#include <fstream>

#define PTR_SUM(p_base, offset) (void*)((uint64_t)p_base + offset)

typedef void* (*INSTR_PROC)(int, int, void*);

void* data_base = nullptr;
void* code_base = nullptr;

void* _exit(int instr_type, int size, void* ops)
{
	ExitProcess(0);
	return nullptr;
}

extern void* _mov(int instr_type, int size, void* ops);
extern void* _add(int instr_type, int size, void* ops);
extern void* _sub(int instr_type, int size, void* ops);
extern void* _mul(int instr_type, int size, void* ops);
extern void* _div(int instr_type, int size, void* ops);
extern void* _xor(int instr_type, int size, void* ops);
extern void* _and(int instr_type, int size, void* ops);
extern void* _or(int instr_type, int size, void* ops);
extern void* _rand(int instr_type, int size, void* ops);
extern void* _ror(int instr_type, int size, void* ops);
extern void* _rol(int instr_type, int size, void* ops);
extern void* _lea(int instr_type, int size, void* ops);
extern void* _jmp(int instr_type, int size, void* ops);
extern void* _put(int instr_type, int size, void* ops);
extern void* _get(int instr_type, int size, void* ops);

INSTR_PROC procs[] =
{
	_exit, _mov, _add, _sub, _mul, _div, _xor, _and, _or, _rand, _ror, _rol, _lea, _jmp, _put, _get
};

struct UFOHeader
{
	int signature;
	short version;
	short entry;
	short data;
	short reserved_1;
	short reserved_2;
};

void* load_program(const char* path)
{
	OFSTRUCT fileMeta;
	HANDLE file = (HANDLE)OpenFile(path, &fileMeta, OF_READ);

	if (!file)
		return nullptr;

	DWORD size = GetFileSize(file, nullptr);
	char* buffer = new char[size];

	DWORD readen;
	bool status = ReadFile(file, buffer, size, &readen, NULL);

	if (!status || readen != size)
	{
		delete[] buffer;
		buffer = nullptr;
	}
	
	CloseHandle(file);
	return buffer;
}

void execute_ufo(void* program)
{
	UFOHeader* header = (UFOHeader*)program;

	code_base = PTR_SUM(program, sizeof(UFOHeader));
	data_base = PTR_SUM(program, header->data);
	void* entry = PTR_SUM(program, header->entry);

	while (true)
	{
		LARGE_INTEGER liStart, liEnd;
		QueryPerformanceCounter(&liStart);

		uint8_t instr_byte = *(uint8_t*)entry;

		int instr = instr_byte >> 4;
		int instr_type = (instr_byte >> 2) & 3;
		int size = instr_byte & 3;

		*(uint16_t*)data_base = (uint64_t)entry - (uint64_t)code_base;

		QueryPerformanceCounter(&liEnd);

		if (liEnd.QuadPart - liStart.QuadPart > 250)
			return;

		entry = procs[instr](instr_type, size, entry);
	}
}

int main(int argc, const char* argv[])
{
	srand(time(0));

	if (argc < 2)
	{
		std::cout << "ufo.exe <path_to_program>\n";
		return 1;
	}

	void* program = load_program(argv[1]);

	if (program == nullptr)
	{
		std::cout << "Invalid path!\n";
		return 1;
	}

	execute_ufo(program);
}