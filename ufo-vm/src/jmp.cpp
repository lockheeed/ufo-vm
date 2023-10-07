#include <stdint.h>

#define PTR_SUM(p_base, offset) (void*)((uint64_t)p_base + offset)

extern void* data_base;
extern void* code_base;

void* _jmp(int instr_type, int size, void* entry)
{
	short op_1 = *(short*)PTR_SUM(entry, 1);
	void* op_2 = PTR_SUM(entry, 3);
	uint16_t addr;

	switch (instr_type)
	{
	case 0:
		switch (size)
		{
		case 0:
			entry = *(uint8_t*)op_2 ? PTR_SUM(code_base, op_1) : PTR_SUM(entry, 4);
			break;
		case 1:
			entry = *(uint16_t*)op_2 ? PTR_SUM(code_base, op_1) : PTR_SUM(entry, 5);
			break;
		case 2:
			entry = *(uint32_t*)op_2 ? PTR_SUM(code_base, op_1) : PTR_SUM(entry, 7);
			break;
		case 3:
			entry = *(uint64_t*)op_2 ? PTR_SUM(code_base, op_1) : PTR_SUM(entry, 11);
			break;
		}
		break;

	case 1:
		switch (size)
		{
		case 0:
			entry = *(uint8_t*)PTR_SUM(data_base, *(uint16_t*)op_2) ? PTR_SUM(code_base, op_1) : PTR_SUM(entry, 5);
			break;
		case 1:
			entry = *(uint16_t*)PTR_SUM(data_base, *(uint16_t*)op_2) ? PTR_SUM(code_base, op_1) : PTR_SUM(entry, 5);
			break;
		case 2:
			entry = *(uint32_t*)PTR_SUM(data_base, *(uint16_t*)op_2) ? PTR_SUM(code_base, op_1) : PTR_SUM(entry, 5);
			break;
		case 3:
			entry = *(uint64_t*)PTR_SUM(data_base, *(uint16_t*)op_2) ? PTR_SUM(code_base, op_1) : PTR_SUM(entry, 5);
			break;
		}
		break;

	case 2:
		addr = *(uint16_t*)PTR_SUM(data_base, *(uint16_t*)op_2);
		switch (size)
		{
		case 0:
			entry = *(uint8_t*)PTR_SUM(data_base, addr) ? PTR_SUM(code_base, op_1) : PTR_SUM(entry, 5);
			break;
		case 1:
			entry = *(uint16_t*)PTR_SUM(data_base, addr) ? PTR_SUM(code_base, op_1) : PTR_SUM(entry, 5);
			break;
		case 2:
			entry = *(uint32_t*)PTR_SUM(data_base, addr) ? PTR_SUM(code_base, op_1) : PTR_SUM(entry, 5);
			break;
		case 3:
			entry = *(uint64_t*)PTR_SUM(data_base, addr) ? PTR_SUM(code_base, op_1) : PTR_SUM(entry, 5);
			break;
		}
		break;

	case 3:
		addr = *(uint16_t*)PTR_SUM(data_base, op_1);
		switch (size)
		{
		case 0:
				entry = *(uint8_t*)PTR_SUM(data_base, *(uint16_t*)op_2) ? PTR_SUM(code_base, addr) : PTR_SUM(entry, 5);
			break;
		case 1:
			entry = *(uint16_t*)PTR_SUM(data_base, *(uint16_t*)op_2) ? PTR_SUM(code_base, addr) : PTR_SUM(entry, 5);
			break;
		case 2:
			entry = *(uint32_t*)PTR_SUM(data_base, *(uint16_t*)op_2) ? PTR_SUM(code_base, addr) : PTR_SUM(entry, 5);
			break;
		case 3:
			entry = *(uint64_t*)PTR_SUM(data_base, *(uint16_t*)op_2) ? PTR_SUM(code_base, addr) : PTR_SUM(entry, 5);
			break;
		}
		break;
	}

	return entry;
}