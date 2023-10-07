#include <stdint.h>

#define PTR_SUM(p_base, offset) (void*)((uint64_t)p_base + offset)

extern void* data_base;

void* _and(int instr_type, int size, void* entry)
{
	short op_1 = *(short*)PTR_SUM(entry, 1);
	void* op_2 = PTR_SUM(entry, 3);

	switch (instr_type)
	{
	case 0:
		switch (size)
		{
		case 0:
			*(uint8_t*)PTR_SUM(data_base, op_1) &= *(uint8_t*)op_2;
			break;
		case 1:
			*(uint16_t*)PTR_SUM(data_base, op_1) &= *(uint16_t*)op_2;
			break;
		case 2:
			*(uint32_t*)PTR_SUM(data_base, op_1) &= *(uint32_t*)op_2;
			break;
		case 3:
			*(uint64_t*)PTR_SUM(data_base, op_1) &= *(uint64_t*)op_2;
			break;
		}
		return PTR_SUM(entry, 3 + (1 << size));

	case 1:
		switch (size)
		{
		case 0:
			*(uint8_t*)PTR_SUM(data_base, op_1) &= *(uint8_t*)PTR_SUM(data_base, *(uint16_t*)op_2);
			break;
		case 1:
			*(uint16_t*)PTR_SUM(data_base, op_1) &= *(uint16_t*)PTR_SUM(data_base, *(uint16_t*)op_2);
			break;
		case 2:
			*(uint32_t*)PTR_SUM(data_base, op_1) &= *(uint32_t*)PTR_SUM(data_base, *(uint16_t*)op_2);
			break;
		case 3:
			*(uint64_t*)PTR_SUM(data_base, op_1) &= *(uint64_t*)PTR_SUM(data_base, *(uint16_t*)op_2);
			break;
		}
		return PTR_SUM(entry, 5);

	case 2:
		uint16_t addr = *(uint16_t*)PTR_SUM(data_base, *(uint16_t*)op_2);
		switch (size)
		{
		case 0:
			*(uint8_t*)PTR_SUM(data_base, op_1) &= *(uint8_t*)PTR_SUM(data_base, addr);
			break;
		case 1:
			*(uint16_t*)PTR_SUM(data_base, op_1) &= *(uint16_t*)PTR_SUM(data_base, addr);
			break;
		case 2:
			*(uint32_t*)PTR_SUM(data_base, op_1) &= *(uint32_t*)PTR_SUM(data_base, addr);
			break;
		case 3:
			*(uint64_t*)PTR_SUM(data_base, op_1) &= *(uint64_t*)PTR_SUM(data_base, addr);
			break;
		}
		return PTR_SUM(entry, 5);
	}
}