#include <stdint.h>
#include <stdio.h>

#define PTR_SUM(p_base, offset) (void*)((uint64_t)p_base + offset)

extern void* data_base;

void* _put(int instr_type, int size, void* entry)
{
	void* op_1 = PTR_SUM(entry, 1);

	switch (instr_type)
	{
	case 0:
		putchar(*(uint8_t*)op_1);
		return PTR_SUM(entry, 2);

	case 1:
		putchar(*(uint8_t*)PTR_SUM(data_base, *(uint16_t*)op_1));		
		return PTR_SUM(entry, 3);

	case 2:
		uint16_t addr = *(uint16_t*)PTR_SUM(data_base, *(uint16_t*)op_1);
		putchar(*(uint8_t*)PTR_SUM(data_base, addr));
		return PTR_SUM(entry, 3);
	}
}