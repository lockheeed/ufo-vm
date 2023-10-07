#include <stdint.h>
#include <stdio.h>

#define PTR_SUM(p_base, offset) (void*)((uint64_t)p_base + offset)

extern void* data_base;

void* _get(int instr_type, int size, void* entry)
{
	void* op_1 = PTR_SUM(entry, 1);

	switch (instr_type)
	{
	case 0:
		*(uint8_t*)PTR_SUM(data_base, *(uint16_t*)op_1) = getchar();
		return PTR_SUM(entry, 3);

	case 1:
		uint16_t addr = *(uint16_t*)PTR_SUM(data_base, *(uint16_t*)op_1);
		*(uint8_t*)PTR_SUM(data_base, addr) = getchar();
		return PTR_SUM(entry, 3);
	}
}